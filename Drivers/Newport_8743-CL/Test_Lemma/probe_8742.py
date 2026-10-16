# -*- coding: utf-8 -*-
"""Sondage du contrôleur Newport 8742 en USB, SANS MOUVEMENT, par ctypes.

STATUT : NON EXÉCUTÉ. Ce script n'a jamais tourné sur matériel. Il est compilé
(python -m py_compile) et vérifié contre un faux pilote (check_no_motion.py),
mais les verdicts « conforme » ne valent que pour le rapport que vous renverrez.

Ce que le script envoie : des lectures, des écritures de vitesse (VA) et
d'accélération (AC) sans effet mécanique (valeur d'origine restaurée à la fin)
et des commandes volontairement invalides. Il n'envoie aucune commande de
mouvement ni de sauvegarde en mémoire. Une garde (MOTS_MOUVEMENT) refuse
d'envoyer tout mnémonique de mouvement, même par erreur de programmation.
Débranchez les moteurs ou laissez les axes vides : aucun moteur n'est requis.

Il réutilise le chargement ctypes de detect_usb.py (même dossier) : lancez-le
depuis le dossier Instrument.

Usage (PowerShell, environnement virtuel actif, application Picomotor fermée) :
    python probe_8742.py
    python probe_8742.py --axes 1,2 --dll "C:\\...\\Bin\\x64\\usbdll.dll"

Sorties : rapport_probe.txt (lisible) et rapport_probe.json (même contenu).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from ctypes import byref, c_ulong, create_string_buffer
from datetime import datetime

from detect_usb import (  # chargement ctypes réutilisé tel quel
    CHEMIN_DLL_DEFAUT, PRODUCT_ID_DEFAUT, TAILLE_TAMPON,
    ErreurDetection, charger_dll, declarer_signatures, lire_infos, machine_pe, ouvrir,
)

PAUSE_S = 0.15  # attente entre envoi et lecture

# Mnémoniques de mouvement du manuel (8742 et 8743-CL). Jamais envoyés.
MOTS_MOUVEMENT = "PR PA MV JA MC MT OR".split()
RE_MOUVEMENT = re.compile(r"^\s*\d*\s*(" + "|".join(MOTS_MOUVEMENT) + r")(?![A-Z])", re.I)

# Plages du manuel (8742 rév. D, p. 87 et p. 71)
VA_MIN, VA_MAX = 1, 2000
AC_MIN, AC_MAX = 1, 200000

# Correspondance incertitude (docs/protocol_8742.md) -> test. None = non couverte.
TABLEAU_INCERTITUDES = {
    1: ("Terminaison de commande", ["T02"], None),
    2: ("Terminaison de réponse", ["T01", "T03"], None),
    3: ("Port TCP", [], "Ethernet seulement : ce script n'utilise que l'USB."),
    4: ("API de la DLL USB", ["T00"], "Réglée par le manuel de l'API fourni ; T00 vérifie que la DLL exporte les fonctions utilisées."),
    5: ("Sens de PR?", [], "Exige l'envoi de PR? (mnémonique de mouvement exclu) et, pour trancher, un déplacement."),
    6: ("MV? non décrite", [], "MV? est un mnémonique de mouvement exclu, et le manuel déconseille de l'utiliser."),
    7: ("Format de CL?", [], "CL? n'existe que sur le 8743-CL."),
    8: ("Unité de VA et AC", ["T10"], "Partielle : T10 vérifie le relu des valeurs, mais l'unité exige un mouvement mesuré."),
    9: ("Écriture : réponse ou non", ["T09"], None),
    10: ("Axe de ZZ", ["T08"], None),
    11: ("Hors plage : 7 ou x01", ["T11"], None),
    12: ("Deux axes en mouvement", [], "Exige deux moteurs câblés et des mouvements."),
}


class Sonde:
    """Échanges avec le contrôleur, journalisés. Les deux méthodes _brut touchent le pilote."""

    def __init__(self, dll, dev_id: int):
        self.dll, self.dev_id = dll, dev_id
        self.journal: list[dict] = []   # échanges du test en cours

    # -- niveau pilote (remplacé par un faux pilote dans check_no_motion.py) --
    def _envoyer_brut(self, octets: bytes) -> int:
        return self.dll.newp_usb_send_ascii(self.dev_id, octets, len(octets))

    def _lire_brut(self) -> tuple[int, bytes]:
        tampon = create_string_buffer(TAILLE_TAMPON)
        nb = c_ulong(0)
        code = self.dll.newp_usb_get_ascii(self.dev_id, tampon, TAILLE_TAMPON, byref(nb))
        return code, tampon.raw[: nb.value]

    # -- niveau commande --
    def envoyer(self, commande: str, *, terminaison: str = "") -> int:
        """Envoie sans lire. Refuse tout mnémonique de mouvement. Le pilote ajoute CR s'il manque."""
        if RE_MOUVEMENT.match(commande):
            raise RuntimeError(f"Commande de mouvement refusée par la garde : {commande!r}")
        code = self._envoyer_brut((commande + terminaison).encode("ascii"))
        self.journal.append({"commande": commande + terminaison, "code_envoi": code})
        return code

    def lire(self) -> bytes:
        """Lit une fois ; renvoie b'' si le pilote signale un échec (pas de réponse)."""
        time.sleep(PAUSE_S)
        code, brut = self._lire_brut()
        self.journal[-1]["brut"] = brut
        self.journal[-1]["code_lecture"] = code
        return brut if code == 0 else b""

    def demander(self, commande: str, *, terminaison: str = "") -> bytes:
        self.envoyer(commande, terminaison=terminaison)
        return self.lire()

    def texte(self, commande: str) -> str:
        """Réponse nettoyée (CR, LF, NUL et espaces retirés aux bords)."""
        return self.demander(commande).decode("ascii", errors="replace").strip("\r\n\0 ")

    def vider_erreurs(self) -> list[str]:
        """Vide la file d'erreurs (TB?) ; les échanges ne sont pas gardés dans le journal du test."""
        sauve = list(self.journal)
        erreurs = []
        for _ in range(11):
            rep = self.demander("TB?").decode("ascii", errors="replace").strip("\r\n\0 ")
            if rep.split(",")[0].strip() in ("0", ""):
                break
            erreurs.append(rep)
        self.journal[:] = sauve
        return erreurs

    def code_erreur(self) -> str:
        """Premier code d'erreur en file (TB?), '0' si vide."""
        rep = self.texte("TB?")
        return rep.split(",")[0].strip() or "?"


def visible(brut: bytes) -> str:
    """Rend les caractères de contrôle lisibles : CR -> \\r, LF -> \\n, NUL -> \\0."""
    s = brut.decode("latin-1")
    s = s.replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n").replace("\0", "\\0")
    return "".join(c if 32 <= ord(c) < 127 or c in "" else f"\\x{ord(c):02x}" for c in s) or "(vide)"


# --- Tests : chacun renvoie (verdict, note) et laisse ses échanges dans sonde.journal ---
CONFORME, NON_CONFORME, A_EXAMINER = "conforme", "non conforme", "à examiner"


def t00_pilote(s: Sonde, args):
    noms = ["newp_usb_init_product", "newp_usb_open_devices", "newp_usb_uninit_system",
            "newp_usb_get_device_info", "newp_usb_send_ascii", "newp_usb_get_ascii"]
    manque = [n for n in noms if not hasattr(s.dll, n)]
    return (NON_CONFORME, f"fonctions absentes : {manque}") if manque else (CONFORME, "6 fonctions exportées")


def t01_terminaison_reponse(s: Sonde, args):
    brut = s.demander("*IDN?")
    if brut.endswith(b"\r\n"):
        return A_EXAMINER, "réponse terminée par CR LF (section 6.1.1 du manuel)"
    if brut.endswith(b"\n"):
        return A_EXAMINER, "réponse terminée par LF seul (section 5.3.1 du manuel)"
    if brut.endswith(b"\r"):
        return A_EXAMINER, "réponse terminée par CR seul, contredit les deux sections"
    return NON_CONFORME, "ni CR ni LF en fin de réponse"


def t02_terminaison_commande(s: Sonde, args):
    reps = {t: s.demander("*IDN?", terminaison=t) for t in ("", "\r", "\n", "\r\n")}
    ok = [repr(t) for t, r in reps.items() if r.strip(b"\r\n\0 ")]
    erreurs = s.vider_erreurs()
    note = f"terminaisons suivies d'une réponse : {', '.join(ok) or 'aucune'} ; erreurs en file : {erreurs or 'aucune'}"
    return (CONFORME if reps[""] and reps["\r"] else NON_CONFORME), note


def t03_idn(s: Sonde, args):
    rep = s.texte("*IDN?")
    ok = re.match(r"^New[_ ]?Focus\s+\S+\s+v?\S+\s+\S+(,\s*SN\S+)?\s*\S*$", rep) is not None
    return (CONFORME if ok else NON_CONFORME), (
        "attendu : « New_Focus <modèle> v<version> <date> » ; le manuel (p. 68) ajoute « , SN<série> », "
        "absent sur le 8742 réel (v3.04) où la série suit la date sans virgule ni SN")


def t04_ve(s: Sonde, args):
    rep = s.texte("VE?")
    ok = re.match(r"^8742\s+Version\s+\S+\s+\S+", rep) is not None
    return (CONFORME if ok else NON_CONFORME), "attendu : « 8742 Version 1.9 11/01/12 » (p. 88)"


def t05_erreurs(s: Sonde, args):
    s.vider_erreurs()
    te = s.texte("TE?")
    tb = s.texte("TB?")
    ok = te == "0" and re.match(r"^0\s*,\s*\S", tb) is not None
    return (CONFORME if ok else NON_CONFORME), "file vide : TE? -> 0 et TB? -> « 0, NO ERROR DETECTED » (p. 84 et 85)"


def t06_type_moteur(s: Sonde, args):
    vals = {a: s.texte(f"{a}QM?") for a in args.axes}
    ok = all(v in ("0", "1", "2", "3") for v in vals.values())
    return (CONFORME if ok else NON_CONFORME), f"QM? par axe : {vals} (valeurs en mémoire, 0 à 3, p. 78) ; aucun test du moteur réel"


def t07_position(s: Sonde, args):
    vals = {a: s.texte(f"{a}TP?") for a in args.axes}
    ok = all(re.fullmatch(r"-?\d+", v) for v in vals.values())
    return (CONFORME if ok else NON_CONFORME), f"TP? par axe : {vals} (entier, pas, p. 86) ; 0 attendu après mise sous tension"


def t08_zz(s: Sonde, args):
    sans = s.texte("ZZ?")
    avec = s.texte("1ZZ?")
    err = s.vider_erreurs()
    ok = re.fullmatch(r"\d+", sans) is not None
    return (CONFORME if ok else NON_CONFORME), (
        f"ZZ? -> {sans!r}, 1ZZ? -> {avec!r}, erreurs {err or 'aucune'} ; "
        "le manuel documente ZZ sans axe (p. 89) ; défaut 0 = détection automatique")


def t09_ecriture_sans_reponse(s: Sonde, args):
    a = args.axes[0]
    valeur = s.texte(f"{a}VA?")
    s.envoyer(f"{a}VA{valeur}")      # réécrit la valeur actuelle : aucun changement
    brut = s.lire()
    err = s.vider_erreurs()
    ok = brut.strip(b"\r\n\0 ") == b"" and not err
    return (CONFORME if ok else NON_CONFORME), (
        f"écriture VA de la valeur actuelle ({valeur}) ; attendu : aucune réponse et file d'erreurs vide ; erreurs {err or 'aucune'}")


def t10_defauts_et_bornes(s: Sonde, args):
    """Défauts de VA et AC, puis écriture/relecture aux bornes de la plage, valeur d'origine restaurée."""
    resume, ok_global = {}, True
    for a in args.axes:
        for mnem, lo, hi, defaut in (("VA", VA_MIN, VA_MAX, 2000), ("AC", AC_MIN, AC_MAX, 100000)):
            origine = s.texte(f"{a}{mnem}?")
            res = {"origine": origine, "defaut_manuel": defaut}
            try:
                for nom, v in (("bas", lo), ("haut", hi)):
                    s.envoyer(f"{a}{mnem}{v}")
                    relu = s.texte(f"{a}{mnem}?")
                    res[nom] = relu
                    if relu != str(v):
                        ok_global = False
            finally:                      # restauration, même en cas d'erreur
                if re.fullmatch(r"\d+", origine):
                    s.envoyer(f"{a}{mnem}{origine}")
                    res["restaure"] = s.texte(f"{a}{mnem}?")
                    if res["restaure"] != origine:
                        ok_global = False
            resume[f"{a}{mnem}"] = res
    err = s.vider_erreurs()
    if err:
        ok_global = False
    return (CONFORME if ok_global else NON_CONFORME), (
        f"bornes du manuel VA {VA_MIN}-{VA_MAX} et AC {AC_MIN}-{AC_MAX}, défauts 2000 et 100000 : {resume} ; erreurs {err or 'aucune'}")


def t11_hors_plage_et_erreurs(s: Sonde, args):
    """Commande inconnue (6), paramètre manquant (38), axe hors plage (9), valeurs au-dessus du maximum.

    Mesuré le 2026-10-14 : le contrôleur accepte VA0 et AC0 (aucune erreur) et les garde en mémoire.
    On n'envoie donc plus de valeur sous le minimum. Au-dessus du maximum, le contrôleur répond
    xx10 (VA, vitesse maximale) et xx11 (AC, accélération maximale), avec xx le numéro d'axe.
    VA et AC de tous les axes sondés sont restaurés dans un finally, quoi qu'il arrive.
    """
    a = args.axes[0]
    s.vider_erreurs()
    cas = [
        ("inconnue", "HELLO?", {"6"}),
        ("parametre_manquant", f"{a}VA", {"38"}),
        ("axe_hors_plage", f"{args.axe_invalide}TP?", {"9"}),
        ("va_trop_haut", f"{a}VA{VA_MAX + 1}", {f"{a}10", "7", f"{a}01"}),
        ("ac_trop_haut", f"{a}AC{AC_MAX + 1}", {f"{a}11", "7", f"{a}01"}),
    ]
    obtenus, ok = {}, True
    avant = {x: (s.texte(f"{x}VA?"), s.texte(f"{x}AC?")) for x in args.axes}
    try:
        for nom, cmd, attendus in cas:
            s.vider_erreurs()
            s.envoyer(cmd)
            s.lire()                      # l'écriture ne doit rien renvoyer
            code = s.code_erreur()
            obtenus[nom] = code
            if code not in attendus:
                ok = False
    finally:                              # restauration de tous les axes, même en cas d'erreur
        for x, (va0, ac0) in avant.items():
            if re.fullmatch(r"\d+", va0):
                s.envoyer(f"{x}VA{va0}")
            if re.fullmatch(r"\d+", ac0):
                s.envoyer(f"{x}AC{ac0}")
        s.vider_erreurs()
    apres = {x: (s.texte(f"{x}VA?"), s.texte(f"{x}AC?")) for x in args.axes}
    restaure = apres == avant
    return (CONFORME if ok and restaure else NON_CONFORME), (
        f"codes obtenus {obtenus} ; attendus 6, 38, 9, {a}10 (VA) et {a}11 (AC) ; "
        f"VA et AC restaurés sur les axes {list(args.axes)} : {restaure} (avant {avant}, après {apres})")


TESTS = [
    ("T00", "chargement du pilote et fonctions exportées", t00_pilote),
    ("T01", "terminaison de la réponse à *IDN?", t01_terminaison_reponse),
    ("T02", "terminaison de commande (aucune, CR, LF, CR LF)", t02_terminaison_commande),
    ("T03", "format de la réponse à *IDN?", t03_idn),
    ("T04", "format de la réponse à VE?", t04_ve),
    ("T05", "file d'erreurs vide : TE? et TB?", t05_erreurs),
    ("T06", "type de moteur QM? par axe", t06_type_moteur),
    ("T07", "lecture de position TP? par axe", t07_position),
    ("T08", "registre ZZ? avec et sans axe", t08_zz),
    ("T09", "écriture sans réponse", t09_ecriture_sans_reponse),
    ("T10", "défauts et bornes VA et AC, avec restauration", t10_defauts_et_bornes),
    ("T11", "codes d'erreur : inconnue, manquant, axe et valeur hors plage", t11_hors_plage_et_erreurs),
]


def executer_tests(sonde: Sonde, args, note) -> list[dict]:
    """Lance chaque test ; une exception est notée dans le rapport et n'arrête pas la suite."""
    resultats = []
    for ident, nom, fonction in TESTS:
        sonde.journal.clear()
        try:
            verdict, remarque = fonction(sonde, args)
        except Exception as exc:
            verdict, remarque = "erreur", f"{type(exc).__name__} : {exc}. Le test est ignoré, les suivants continuent."
        echanges = [{"commande": e["commande"], "brut": visible(e.get("brut", b"")),
                     "code_envoi": e.get("code_envoi"), "code_lecture": e.get("code_lecture")}
                    for e in sonde.journal]
        incertitudes = [n for n, (_, tests, _) in TABLEAU_INCERTITUDES.items() if ident in tests]
        res = {"id": ident, "nom": nom, "incertitudes": incertitudes, "echanges": echanges,
               "verdict": verdict, "note": remarque}
        resultats.append(res)
        cmds = " ; ".join(e["commande"].replace("\r", "\\r").replace("\n", "\\n") for e in echanges[:6])
        raws = " ; ".join(e["brut"] for e in echanges[:6])
        suite = f" (+{len(echanges) - 6} échanges)" if len(echanges) > 6 else ""
        note(f"[{ident}] {nom} | envoyé : {cmds}{suite} | brut : {raws}{suite} | verdict : {verdict} | {remarque}")
        # filet de sécurité : si le test a laissé des erreurs en file, on les vide pour le suivant
        try:
            sonde.vider_erreurs()
        except Exception:
            pass
    return resultats


def tableau_texte() -> list[str]:
    lignes = ["Correspondance incertitude -> test (protocol_8742.md) :"]
    for n, (nom, tests, raison) in TABLEAU_INCERTITUDES.items():
        etat = "couverte par " + ", ".join(tests) if tests else "NON couverte"
        lignes.append(f"  U{n:<2} {nom} : {etat}" + (f" ({raison})" if raison else ""))
    return lignes


def executer(args, rapport: list[str], json_out: dict) -> int:
    def note(ligne: str = "") -> None:
        print(ligne)
        rapport.append(ligne)

    note(f"Rapport probe_8742.py, {datetime.now():%Y-%m-%d %H:%M:%S}")
    note("STATUT : script non exécuté avant ce rapport ; les lignes ci-dessous sont la sortie réelle.")
    note("Aucune commande de mouvement n'est envoyée (garde dans le script).")
    dll = charger_dll(args.dll)
    note(f"DLL chargée : {args.dll}, architecture {machine_pe(args.dll)}")
    declarer_signatures(dll)
    ouverte = False
    try:
        nombre = ouvrir(dll, args.produit)
        ouverte = True
        if nombre == 0:
            raise ErreurDetection("Aucun périphérique trouvé. Action : lancez detect_usb.py et corrigez d'abord ce point.")
        infos = lire_infos(dll)
        if not infos:
            raise ErreurDetection("Liste de périphériques vide. Action : débranchez, rebranchez, relancez.")
        dev_id, desc = infos[args.indice]
        note(f"Contrôleur sondé : DeviceID {dev_id}, {desc}")
        json_out["controleur"] = {"device_id": dev_id, "description": desc}
        note()
        resultats = executer_tests(Sonde(dll, dev_id), args, note)
        json_out["tests"] = resultats
        note()
        for ligne in tableau_texte():
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
    p = argparse.ArgumentParser(description="Sondage USB du 8742, sans mouvement.")
    p.add_argument("--dll", default=os.environ.get("NEWPORT_USBDLL", CHEMIN_DLL_DEFAUT))
    p.add_argument("--produit", type=lambda s: int(s, 0), default=PRODUCT_ID_DEFAUT)
    p.add_argument("--indice", type=int, default=0, help="indice du contrôleur dans la liste (défaut 0)")
    p.add_argument("--axes", default="1,2,3,4", help="axes sondés, défaut 1,2,3,4")
    p.add_argument("--axe-invalide", type=int, default=5, help="axe hors plage pour le test d'erreur (défaut 5)")
    p.add_argument("--rapport", default="rapport_probe.txt")
    p.add_argument("--json", default="rapport_probe.json")
    args = p.parse_args()
    args.axes = [int(x) for x in args.axes.split(",") if x.strip()]

    rapport: list[str] = []
    json_out: dict = {"statut": "sortie réelle", "date": datetime.now().isoformat(timespec="seconds"), "tests": []}
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
