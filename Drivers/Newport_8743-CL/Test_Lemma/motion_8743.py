# -*- coding: utf-8 -*-
"""Premier mouvement du 8311 sur le 8743-CL, USB : un aller de +N comptes puis un retour de -N comptes.

STATUT : NON EXÉCUTÉ sur matériel. Vérifié seulement contre un faux contrôleur (check_motion_8743.py).

Ce que le script envoie, et rien d'autre :
  * lectures (*IDN?, ZZ?, ZH?, SN?, MM?, QM?, TP?, MD?, VA?, AC?, PH?, PR?, TB?) ;
  * VA et AC (valeurs d'origine restaurées dans un finally) ;
  * un PR de +N puis un PR de -N comptes, N = --comptes (défaut 100, environ 5 µm ; au plus 45000, environ 2,2 mm) ;
  * ST puis AB en cas d'erreur, de dépassement de durée ou de Ctrl+C.
Il n'envoie ni MM (boucle fermée), ni AF, ni PA, ni SM, ni ZH, ni SN, ni MV. Le driver est construit avec
max_move=N : aucun déplacement plus grand n'est possible.

Avant de bouger, le script lit l'état et s'arrête sans mouvement s'il y a une erreur en file, si MM n'est pas à 0,
si SN n'est pas à 1 ou si l'axe n'est pas arrêté. Il demande ensuite de taper OUI.

Montage attendu : 8311 sur l'axe choisi, libre, sans rien pousser, en milieu de course. Application Picomotor fermée.

Usage (PowerShell, venv actif, depuis le dossier Instrument) :
    python motion_8743.py
    python motion_8743.py --axe 1 --comptes 100 --va 200
Sorties : rapport_motion_8743.txt et rapport_motion_8743.json.
Arrêt manuel : Ctrl+C (le script envoie ST puis AB) ou éteindre le contrôleur.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime

from newport_8743 import Newport8743

PAS_SONDAGE_S = 0.05      # intervalle entre deux lectures de MD?
ATTENTE_DEMARRAGE_S = 0.5  # temps pendant lequel on attend de voir MD? passer à 0 après un PR


class Journal:
    """Enveloppe d'un transport : enregistre chaque commande et chaque réponse avec l'heure."""

    def __init__(self, transport):
        self._t = transport
        self.echanges: list[dict] = []
        self._t0 = time.monotonic()

    def write(self, cmd):
        self.echanges.append({"t": round(time.monotonic() - self._t0, 3), "envoye": cmd})
        self._t.write(cmd)

    def ask(self, cmd):
        rep = self._t.ask(cmd)
        self.echanges.append({"t": round(time.monotonic() - self._t0, 3), "envoye": cmd, "recu": rep})
        return rep

    def close(self):
        self._t.close()

    def __getattr__(self, nom):
        return getattr(self._t, nom)


def lire_etat(inst, ax, a) -> dict:
    return {
        "idn": inst._transport.ask("*IDN?"), "ZZ": inst.ask("ZZ?"), "ZH": ax.hardware_config(), "SN": ax.units(),
        "MM": ax.closed_loop(), "QM": ax.motor_type(), "TP": ax.position(), "arrete": not ax.is_moving(),
        "VA": ax.velocity(), "AC": ax.acceleration(), "PH": inst.hardware_status(),
    }


def deplacer(inst, ax, a, comptes: int, timeout_s: float, note, suivi_tp_s: float = 0.0) -> dict:
    """Un PR, puis attente de l'arrêt par MD?. Renvoie les mesures. Lève RuntimeError si l'axe ne s'arrête pas."""
    tp_avant = ax.position()
    t0 = time.monotonic()
    ax.move_relative(comptes, verifier_erreurs=False)   # pas de lecture de TB? avant de suivre MD?
    eviter = getattr(inst._transport, "eviter_vidage", None)
    if eviter:
        eviter()                                        # PR ne produit pas de réponse : pas de vidage avant MD?
    t_envoi = time.monotonic() - t0
    vu_en_mouvement, echantillons, suivi, dernier_suivi = False, [], [], 0.0
    while True:
        en_mvt = ax.is_moving()
        dt = time.monotonic() - t0
        echantillons.append((round(dt, 3), en_mvt))
        if suivi_tp_s and en_mvt and dt - dernier_suivi >= suivi_tp_s:
            dernier_suivi = dt
            suivi.append((round(dt, 1), ax.position()))
            note(f"    t = {dt:.1f} s, TP = {suivi[-1][1]}")
        vu_en_mouvement |= en_mvt
        if not en_mvt and (vu_en_mouvement or dt > ATTENTE_DEMARRAGE_S):
            break
        if dt > timeout_s:
            raise RuntimeError(f"L'axe {a} est encore en mouvement après {timeout_s} s.")
        time.sleep(PAS_SONDAGE_S)
    duree = time.monotonic() - t0
    erreurs = inst.drain_errors()
    tp_apres = ax.position()
    res = {
        "comptes_demandes": comptes, "TP_avant": tp_avant, "TP_apres": tp_apres, "delta_TP": tp_apres - tp_avant,
        "duree_s": round(duree, 3), "envoi_s": round(t_envoi, 3), "mouvement_vu_par_MD": vu_en_mouvement,
        "PR?": inst.ask(f"{a}PR?"), "QM?": ax.motor_type(), "erreurs": erreurs,
        "nb_lectures_MD": len(echantillons), "echantillons_MD": echantillons, "suivi_TP": suivi,
    }
    en_mvt_t = [t for t, m in echantillons if m]
    if en_mvt_t:
        res["MD_en_mouvement_de_s"], res["MD_en_mouvement_a_s"] = en_mvt_t[0], en_mvt_t[-1]
    plage = (f"MD? à 0 de {res['MD_en_mouvement_de_s']} s à {res['MD_en_mouvement_a_s']} s après l'envoi"
             if vu_en_mouvement else "MD? jamais vu à 0 (mouvement fini avant la première lecture, ou MD? ne reflète pas le mouvement)")
    note(f"  PR {comptes:+d} : TP {tp_avant} -> {tp_apres} (delta {res['delta_TP']:+d}), envoi {res['envoi_s']} s, "
         f"sortie de la boucle à {res['duree_s']} s, {plage}, PR? -> {res['PR?']!r}, QM? -> {res['QM?']}, erreurs {res['erreurs'] or 'aucune'}")
    if erreurs:
        raise RuntimeError(f"Erreurs du contrôleur après PR {comptes:+d} : {erreurs}")
    return res


def executer_mouvement(inst, args, confirmer, note, attendre=None) -> dict:
    a = args.axe
    ax = getattr(inst, f"axis{a}")
    sortie: dict = {"axe": a, "comptes": args.comptes, "va": args.va}
    sens = getattr(args, "sens", 1)
    suivi = 2.0 if args.comptes > 2000 else 0.0
    note(f"Axe {a}, aller de {sens * args.comptes:+d} comptes puis retour de {-sens * args.comptes:+d}, VA={args.va}.")
    attendu = args.comptes * 49.6 / 20 / args.va
    mesure = args.comptes / (0.628 * args.va)
    note(f"Durée attendue par mouvement : {attendu:.1f} s d'après le manuel du 8311 (49,6 nm par comptage, 20 nm par pas, VA en pas/s) ; "
         f"{mesure:.1f} s d'après la mesure à VA=50 (31 comptes/s, supposée proportionnelle à VA).")
    avant = lire_etat(inst, ax, a)
    err = inst.drain_errors()
    sortie["etat_avant"], sortie["erreurs_avant"] = avant, err
    note(f"État avant : {avant} ; erreurs en file : {err or 'aucune'}")
    refus = []
    if err: refus.append(f"erreurs en file : {err}")
    if avant["MM"] != 0: refus.append("MM n'est pas à 0 (boucle fermée active)")
    if avant["SN"] != 1: refus.append("SN n'est pas à 1 (comptes codeur)")
    if not avant["arrete"]: refus.append("l'axe n'est pas arrêté")
    if refus:
        sortie["resultat"] = "refus avant mouvement : " + " ; ".join(refus)
        note("ARRÊT SANS MOUVEMENT : " + sortie["resultat"])
        return sortie
    if not confirmer():
        sortie["resultat"] = "annulé par l'utilisateur, aucun mouvement"
        note(sortie["resultat"])
        return sortie

    va0, ac0 = avant["VA"], avant["AC"]
    echec = None
    try:
        ax.velocity(args.va)
        sortie["TP_apres_ecriture_VA"] = [ax.position() for _ in range(3)]
        note(f"TP lu 3 fois au repos après l'écriture de VA : {sortie['TP_apres_ecriture_VA']}")
        sortie["aller"] = deplacer(inst, ax, a, sens * args.comptes, args.timeout, note, suivi)
        if attendre:
            attendre(f"Aller terminé (TP = {ax.position()}). Relève la position de l'embout, puis tape ENTRÉE pour le retour.")
        sortie["retour"] = deplacer(inst, ax, a, -sens * args.comptes, args.timeout, note, suivi)
    except BaseException as exc:                      # Ctrl+C compris
        echec = f"{type(exc).__name__} : {exc}"
        note(f"ERREUR : {echec}. Envoi de ST puis AB.")
        for envoi in (ax.stop, inst.abort):
            try:
                envoi()
            except Exception as e2:
                note(f"  {envoi.__name__} a échoué : {e2}")
    finally:
        for nom, valeur in (("velocity", va0), ("acceleration", ac0)):
            try:
                getattr(ax, nom)(valeur)
            except Exception as e2:
                note(f"  restauration de {nom} échouée : {e2}")
    apres = lire_etat(inst, ax, a)
    sortie["etat_apres"], sortie["echec"] = apres, echec
    sortie["VA_AC_restaures"] = (apres["VA"], apres["AC"]) == (va0, ac0)
    if "aller" in sortie and "retour" in sortie:
        d = sortie["aller"]["delta_TP"] + sortie["retour"]["delta_TP"]
        sortie["ecart_aller_retour_comptes"] = d
        al = sortie["aller"]
        if al["mouvement_vu_par_MD"]:
            sortie["vitesse_comptes_par_s"] = round(args.comptes / (al["MD_en_mouvement_a_s"] - al["envoi_s"]), 1) if al["MD_en_mouvement_a_s"] > al["envoi_s"] else None
        else:
            sortie["vitesse_comptes_par_s"] = None
        note(f"Écart après aller-retour : {d:+d} comptes ; vitesse de l'aller : "
             + (f"{sortie['vitesse_comptes_par_s']} comptes/s (de la fin de l'envoi à la dernière lecture de MD? à 0)"
                if sortie["vitesse_comptes_par_s"] else "non mesurable, MD? n'a pas été vu à 0 (utiliser une VA plus basse)"))
    note(f"VA et AC restaurés : {sortie['VA_AC_restaures']} ; état après : {apres}")
    sortie["resultat"] = "échec : " + echec if echec else "terminé"
    return sortie


def main() -> int:
    p = argparse.ArgumentParser(description="Aller-retour de N comptes du 8311 sur le 8743-CL.")
    p.add_argument("--axe", type=int, default=1, choices=(1, 2))
    p.add_argument("--comptes", type=int, default=100)
    p.add_argument("--va", type=int, default=200)
    p.add_argument("--sens", type=int, choices=(1, -1), default=1, help="sens de l'aller : 1 ou -1 (défaut 1)")
    p.add_argument("--pause", action="store_true", help="attendre ENTRÉE entre l'aller et le retour (pour relever une mesure)")
    p.add_argument("--timeout", type=float, default=None, help="durée maximale d'un mouvement, en secondes (défaut : max(20, 3 fois la durée attendue))")
    p.add_argument("--rapport", default="rapport_motion_8743.txt")
    p.add_argument("--json", default="rapport_motion_8743.json")
    args = p.parse_args()
    if not 1 <= args.comptes <= 45000 or not 1 <= args.va <= 2000:
        print("--comptes doit être entre 1 et 45000 (environ 2,2 mm) et --va entre 1 et 2000.")
        return 2
    if args.timeout is None:
        args.timeout = max(20.0, 3 * args.comptes * 49.6 / 20 / args.va)

    rapport: list[str] = []

    def note(ligne=""):
        print(ligne)
        rapport.append(ligne)

    def confirmer() -> bool:
        print(f"\nLe 8311 de l'axe {args.axe} va bouger de {args.sens * args.comptes:+d} puis {-args.sens * args.comptes:+d} comptes (environ "
              f"{args.comptes * 0.0496:.1f} µm, sur 12700 µm de course). Il doit être libre, sans rien pousser, en milieu de course.")
        if args.comptes * 0.0496 > 1000:
            print(f"Déplacement de {args.comptes * 0.0496 / 1000:.2f} mm : vérifie qu'il reste plus de {args.comptes * 0.0496 / 1000:.0f} mm de course de chaque côté (course totale 12,7 mm).")
        rep = input("Tape OUI pour continuer, autre chose pour annuler : ").strip()
        rapport.append(f"Confirmation demandée, réponse : {rep!r}")
        return rep == "OUI"

    def attendre(msg):
        print(f"\n{msg}")
        rep = input("> ")
        rapport.append(f"Pause : {msg} Réponse : {rep!r}")

    note(f"Rapport motion_8743.py, {datetime.now():%Y-%m-%d %H:%M:%S}")
    note("STATUT : script non exécuté avant ce rapport ; les lignes ci-dessous sont la sortie réelle.")
    from newport_usb import UsbTransport
    journal = Journal(UsbTransport(defensive=True, match="8743"))
    sortie: dict = {"date": datetime.now().isoformat(timespec="seconds")}
    code = 0
    try:
        inst = Newport8743("mv8743", transport=journal, allow_motion=True, max_move=args.comptes)
        try:
            sortie.update(executer_mouvement(inst, args, confirmer, note, attendre if args.pause else None))
        finally:
            inst.close()
    except Exception as exc:
        note(f"ERREUR imprévue ({type(exc).__name__}) : {exc}. Envoyez ce rapport en entier.")
        sortie["erreur"] = f"{type(exc).__name__} : {exc}"
        code = 1
    sortie["echanges"] = journal.echanges
    with open(args.rapport, "w", encoding="utf-8") as f:
        f.write("\n".join(rapport) + "\n")
    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(sortie, f, ensure_ascii=False, indent=2)
    print(f"\nRapports écrits : {os.path.abspath(args.rapport)} et {os.path.abspath(args.json)}")
    return code


if __name__ == "__main__":
    sys.exit(main())
