# -*- coding: utf-8 -*-
"""Sondage du contrôleur Newport 8743-CL en USB, SANS MOUVEMENT, par ctypes.

STATUT : NON EXÉCUTÉ sur matériel. Vérifié seulement contre un faux pilote (check_no_motion_8743.py).

Réutilise probe_8742.py (même dossier) : transport, journal, garde anti-mouvement, tests communs.
Envoie des lectures, des écritures de VA et AC (valeur d'origine restaurée dans un finally)
et des commandes volontairement invalides. N'envoie aucun mnémonique de mouvement ni de sauvegarde (SM),
ni d'écriture de boucle fermée (MM, CL, DB, FE, ZH, SN). La garde refuse tout mouvement, même par erreur.

Deux étapes :
  python probe_8743.py                      8743-CL seul, sans moteur
  python probe_8743.py --moteur-branche     8743-CL + 8311 branché (moteur ET codeur), lectures seulement

Sorties : rapport_probe_8743.txt et rapport_probe_8743.json (ou rapport_probe_8743_moteur.* avec --moteur-branche).
Application Picomotor fermée. Lancer depuis le dossier Instrument.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime

import probe_8742 as P
from probe_8742 import CONFORME, NON_CONFORME, A_EXAMINER, Sonde
from detect_usb import ErreurDetection, charger_dll, declarer_signatures, lire_infos, machine_pe, ouvrir

# Garde élargie aux mnémoniques de mouvement propres au 8743-CL : MZ (index), AF (recherche d'absolu).
# MM n'est pas dans la liste, mais la sonde n'en envoie jamais l'écriture (seulement MM?).
P.RE_MOUVEMENT = re.compile(r"^\s*\d*\s*(PA|PR|MV|JA|MC|MT|MZ|OR|AF)(?![A-Z?])|^\s*\d*\s*(PA|PR|MV|MT|MZ|OR|AF)\?", re.I)
# Écritures de configuration refusées aussi : la sonde ne doit rien changer à la boucle ni sauvegarder.
RE_CONFIG = re.compile(r"^\s*\d*\s*(MM|CL|DB|FE|ZH|SN|SM|RS|XX|SL|SR|AD|AE)(?![A-Z?])\s*[-+]?\d", re.I)
_envoyer_orig = Sonde.envoyer


def _envoyer_garde(self, commande, **kw):
    if RE_CONFIG.match(commande) or re.match(r"^\s*(SM|RS|XX|\*RST)\s*$", commande, re.I):
        raise RuntimeError(f"Commande de configuration refusée par la garde : {commande!r}")
    return _envoyer_orig(self, commande, **kw)


Sonde.envoyer = _envoyer_garde


POLL_MAX_S = 2.0      # attente maximale d'une réponse à une requête
POLL_PAS_S = 0.1      # intervalle entre deux lectures


class SondeRobuste(Sonde):
    """Évite le décalage des réponses vu sur le 8743-CL (rapport du 2026-10-15) :
    avant chaque requête, vide les réponses restées dans le pilote (notées comme orphelines) ;
    après l'envoi, relit jusqu'à POLL_MAX_S si la réponse n'est pas encore arrivée (notée comme tardive)."""

    def __init__(self, dll, dev_id):
        super().__init__(dll, dev_id)
        self.orphelines: list[str] = []
        self.tardives: list[str] = []

    def _vider_pilote(self, avant: str):
        for _ in range(20):
            code, brut = self._lire_brut()
            if code != 0 or not brut:
                return
            self.orphelines.append(f"avant {avant} : {P.visible(brut)}")

    def demander(self, commande, *, terminaison=""):
        if not commande.rstrip().endswith("?"):
            return super().demander(commande, terminaison=terminaison)
        self._vider_pilote(commande)
        self.envoyer(commande, terminaison=terminaison)
        t0 = time.monotonic()
        brut = b""
        while True:
            time.sleep(P.PAUSE_S if time.monotonic() == t0 or not brut else POLL_PAS_S)
            code, brut = self._lire_brut()
            if code == 0 and brut:
                break
            brut = b""
            if time.monotonic() - t0 > POLL_MAX_S:
                break
            time.sleep(POLL_PAS_S)
        attente = time.monotonic() - t0
        if brut and attente > P.PAUSE_S + 0.05:
            self.tardives.append(f"{commande} : {attente:.2f} s")
        self.journal[-1]["brut"] = brut
        self.journal[-1]["code_lecture"] = 0 if brut else 1
        return brut


def _avec_synchro(fonction):
    """Ajoute au verdict les réponses orphelines ou tardives vues pendant le test."""
    def enveloppe(s, args):
        if isinstance(s, SondeRobuste):
            s.orphelines.clear()
            s.tardives.clear()
        verdict, note = fonction(s, args)
        if isinstance(s, SondeRobuste) and (s.orphelines or s.tardives):
            note += f" ; SYNCHRO : orphelines {s.orphelines or 'aucune'}, tardives {s.tardives or 'aucune'}"
            if verdict == CONFORME:
                verdict = A_EXAMINER
        return verdict, note
    enveloppe.__name__ = fonction.__name__
    return enveloppe


TABLEAU_INCERTITUDES = {
    1: ("Format de *IDN? et VE? du 8743-CL", ["T03", "T04"], None),
    2: ("Firmware selon le numéro de série (v4.06 attendu pour S/N > 11001)", ["T03", "T04"], None),
    3: ("Unité par défaut SN (1 = comptes codeur)", ["T12"], None),
    4: ("MM par défaut (0 = boucle fermée désactivée)", ["T13"], "Le manuel écrit la syntaxe xxDB? pour MM? et FE? : la sonde envoie xxMM? et xxFE?."),
    5: ("ZH par défaut et bits", ["T14"], None),
    6: ("Format de CL? (entier ou décimal)", ["T15"], None),
    7: ("Bits de PH? et état de MD?", ["T16"], None),
    8: ("Moteur et codeur vus avec le 8311 branché", ["T17"], "Seulement avec --moteur-branche."),
    9: ("Sens de PR?", [], "Exige un déplacement."),
    10: ("MV? non décrite", [], "Mnémonique de mouvement exclu."),
    11: ("Unité de VA et AC quand SN=1", [], "Exige un mouvement mesuré."),
    12: ("Comportement de la boucle fermée (MM=1)", [], "Exige un mouvement."),
    13: ("Port TCP", [], "Ethernet seulement : ce script n'utilise que l'USB."),
}


def t03_idn(s, args):
    rep = s.texte("*IDN?")
    ok = re.match(r"^New[_ ]?Focus\s+8743\S*\s+v?\S+\s+\S+", rep) is not None
    return (CONFORME if ok else NON_CONFORME), (
        f"attendu : « New_Focus 8743-CL v<version> <date> » (manuel p. 80) ; obtenu {rep!r}. "
        "Attendu v4.06 pour S/N > 11001 (notes de firmware p. 2)")


def t04_ve(s, args):
    rep = s.texte("VE?")
    ok = re.match(r"^8743\S*\s+Version\s+\S+", rep) is not None
    return (CONFORME if ok else NON_CONFORME), f"attendu : « 8743-CL Version <v> <date> » (p. 117) ; obtenu {rep!r}"


def _lire_par_axe(s, args, suffixe, valides):
    vals = {a: s.texte(f"{a}{suffixe}") for a in args.axes}
    return vals, all(re.fullmatch(valides, v) for v in vals.values())


def t12_sn(s, args):
    vals, ok = _lire_par_axe(s, args, "SN?", r"[01]")
    return (CONFORME if ok else NON_CONFORME), f"SN? par axe : {vals} (0 = pas, 1 = comptes codeur, défaut 1, p. 111)"


def t13_mm(s, args):
    vals, ok = _lire_par_axe(s, args, "MM?", r"[01]")
    return (CONFORME if ok else NON_CONFORME), (
        f"MM? par axe : {vals} (0 = boucle fermée désactivée, défaut après mise sous tension, p. 94)")


def t14_zh(s, args):
    vals, ok = _lire_par_axe(s, args, "ZH?", r"\d+")
    return (CONFORME if ok else NON_CONFORME), (
        f"ZH? par axe : {vals} (bit 0 limites matérielles, bit 1 suivi, bit 2 codeur quasi-absolu, bit 3 limites logicielles, p. 119)")


def t15_boucle(s, args):
    vals = {}
    ok = True
    for mn in ("CL?", "DB?", "FE?"):
        vals[mn] = {a: s.texte(f"{a}{mn}") for a in args.axes}
        ok &= all(re.fullmatch(r"-?\d+(\.\d+)?", v) for v in vals[mn].values())
    return (CONFORME if ok else NON_CONFORME), (
        f"{vals} ; le manuel dit « entier » pour CL? (plage 0.1 à 100000 s) : noter si la réponse est décimale (p. 87)")


def t16_ph_md(s, args):
    ph = s.texte("PH?")
    md = {a: s.texte(f"{a}MD?") for a in args.axes}
    ok = re.fullmatch(r"\d+", ph) is not None and all(v in ("0", "1") for v in md.values())
    return (CONFORME if ok else NON_CONFORME), (
        f"PH? -> {ph!r} (bits 0 à 5 : limites et index des axes 1 et 2, p. 101) ; MD? -> {md} (0 en mouvement, 1 arrêté)")


def t17_moteur_branche(s, args):
    """Capture seule : état lu avec le moteur et le codeur branchés. Aucune attente de valeur."""
    if not args.moteur_branche:
        return A_EXAMINER, "ignoré : relancer avec --moteur-branche une fois le 8311 branché (moteur et codeur)"
    etat = {}
    for mn in ("QM?", "SN?", "MM?", "ZH?", "TP?", "MD?"):
        etat[mn] = {a: s.texte(f"{a}{mn}") for a in args.axes}
    etat["PH?"] = s.texte("PH?")
    err = s.vider_erreurs()
    return A_EXAMINER, f"état avec 8311 branché : {etat} ; erreurs en file : {err or 'aucune'} (x34 = connecteur codeur absent)"


TESTS = [
    ("T00", "chargement du pilote et fonctions exportées", P.t00_pilote),
    ("T01", "terminaison de la réponse à *IDN?", P.t01_terminaison_reponse),
    ("T02", "terminaison de commande (aucune, CR, LF, CR LF)", P.t02_terminaison_commande),
    ("T03", "format de la réponse à *IDN?", t03_idn),
    ("T04", "format de la réponse à VE?", t04_ve),
    ("T05", "file d'erreurs vide : TE? et TB?", P.t05_erreurs),
    ("T06", "type de moteur QM? par axe", P.t06_type_moteur),
    ("T07", "lecture de position TP? par axe", P.t07_position),
    ("T08", "registre ZZ? avec et sans axe", P.t08_zz),
    ("T09", "écriture sans réponse", P.t09_ecriture_sans_reponse),
    ("T10", "défauts et bornes VA et AC, avec restauration", P.t10_defauts_et_bornes),
    ("T11", "codes d'erreur : inconnue, manquant, axe et valeur hors plage", P.t11_hors_plage_et_erreurs),
    ("T12", "unité SN? par axe", t12_sn),
    ("T13", "boucle fermée MM? par axe", t13_mm),
    ("T14", "configuration matérielle ZH? par axe", t14_zh),
    ("T15", "paramètres de boucle CL?, DB?, FE?", t15_boucle),
    ("T16", "état matériel PH? et MD?", t16_ph_md),
    ("T17", "état avec le 8311 branché (lecture seule)", t17_moteur_branche),
]
TESTS = [(i, n, _avec_synchro(f)) for i, n, f in TESTS]
P.TESTS = TESTS
P.TABLEAU_INCERTITUDES = TABLEAU_INCERTITUDES


def lire_infos_synchro(dll, essais=10):
    """Relit la liste des contrôleurs tant qu'une réponse parasite (restée dans le contrôleur
    après une exécution interrompue ou décalée) a pris la place de la description attendue."""
    ecartees = []
    infos = []
    for _ in range(essais):
        infos = lire_infos(dll)
        if any("8743" in d or "8742" in d for _, d in infos):
            return infos, ecartees
        ecartees.append(infos)
    return infos, ecartees


def executer(args, rapport, json_out) -> int:
    def note(ligne=""):
        print(ligne)
        rapport.append(ligne)

    note(f"Rapport probe_8743.py, {datetime.now():%Y-%m-%d %H:%M:%S}, moteur branché : {args.moteur_branche}")
    note("STATUT : script non exécuté avant ce rapport ; les lignes ci-dessous sont la sortie réelle.")
    note("Aucune commande de mouvement ni de configuration de boucle n'est envoyée (gardes dans le script).")
    dll = charger_dll(args.dll)
    note(f"DLL chargée : {args.dll}, architecture {machine_pe(args.dll)}")
    declarer_signatures(dll)
    ouverte = False
    try:
        nombre = ouvrir(dll, args.produit)
        ouverte = True
        if nombre == 0:
            raise ErreurDetection("Aucun périphérique trouvé. Action : lancez detect_usb.py et corrigez d'abord ce point.")
        infos, ecartees = lire_infos_synchro(dll)
        if ecartees:
            note(f"Réponses restées dans le contrôleur et écartées avant la liste : {ecartees}")
        note(f"Contrôleurs listés : {infos}")
        candidats = [(i, d) for i, d in infos if "8743" in d]
        if args.indice is not None:
            dev_id, desc = infos[args.indice]
        elif len(candidats) == 1:
            dev_id, desc = candidats[0]
        else:
            raise ErreurDetection(f"{len(candidats)} contrôleur(s) 8743 reconnu(s) dans {infos}. "
                                  "Action : relancez avec --indice N (position dans cette liste).")
        note(f"Contrôleur sondé : DeviceID {dev_id}, {desc}")
        json_out["controleur"] = {"device_id": dev_id, "description": desc}
        note()
        resultats = P.executer_tests(SondeRobuste(dll, dev_id), args, note)
        json_out["tests"] = resultats
        note()
        for ligne in P.tableau_texte():
            note(ligne)
        bilan = {v: sum(r["verdict"] == v for r in resultats) for v in (CONFORME, NON_CONFORME, A_EXAMINER, "erreur")}
        note()
        note(f"Bilan : {bilan}")
        json_out["bilan"] = bilan
        return 0
    finally:
        if ouverte:
            dll.newp_usb_uninit_system()


def main() -> int:
    p = argparse.ArgumentParser(description="Sondage USB du 8743-CL, sans mouvement.")
    p.add_argument("--dll", default=os.environ.get("NEWPORT_USBDLL", P.CHEMIN_DLL_DEFAUT))
    p.add_argument("--produit", type=lambda s: int(s, 0), default=P.PRODUCT_ID_DEFAUT)
    p.add_argument("--indice", type=int, default=None, help="position du contrôleur dans la liste (défaut : le seul 8743)")
    p.add_argument("--axes", default="1,2", help="axes sondés, défaut 1,2")
    p.add_argument("--axe-invalide", type=int, default=3, help="axe hors plage pour le test d'erreur (défaut 3)")
    p.add_argument("--moteur-branche", action="store_true", help="8311 branché : active T17")
    p.add_argument("--rapport", default=None)
    p.add_argument("--json", default=None)
    args = p.parse_args()
    args.axes = [int(x) for x in args.axes.split(",") if x.strip()]
    suffixe = "_moteur" if args.moteur_branche else ""
    args.rapport = args.rapport or f"rapport_probe_8743{suffixe}.txt"
    args.json = args.json or f"rapport_probe_8743{suffixe}.json"

    rapport, json_out = [], {"statut": "sortie réelle", "date": datetime.now().isoformat(timespec="seconds"), "tests": []}
    try:
        code = executer(args, rapport, json_out)
    except ErreurDetection as exc:
        print(f"\nERREUR : {exc}")
        rapport.append(f"ERREUR : {exc}")
        json_out["erreur"] = str(exc)
        code = 1
    except Exception as exc:
        msg = (f"ERREUR imprévue ({type(exc).__name__}) : {exc}\n"
               "Action : envoyez ce rapport en entier pour qu'on adapte le script.")
        print(f"\n{msg}")
        rapport.append(msg)
        json_out["erreur"] = msg
        code = 2
    with open(args.rapport, "w", encoding="utf-8") as f:
        f.write("\n".join(rapport) + "\n")
    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(json_out, f, ensure_ascii=False, indent=2)
    print(f"\nRapports écrits : {os.path.abspath(args.rapport)} et {os.path.abspath(args.json)}")
    return code


if __name__ == "__main__":
    sys.exit(main())
