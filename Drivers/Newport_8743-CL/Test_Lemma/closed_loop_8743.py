# -*- coding: utf-8 -*-
"""Boucle ouverte contre boucle fermée du 8311 sur le 8743-CL : retrouve-t-on les positions A et B ?

STATUT : NON EXÉCUTÉ sur matériel. Vérifié seulement contre un faux contrôleur (check_closed_loop_8743.py).

A = position de départ (TP?), B = A + --amplitude comptes (défaut 2000, environ 100 µm).
Phase 1, boucle ouverte (MM=0) : --cycles allers-retours B puis A par PA (position absolue en comptes).
Phase 2, boucle fermée (MM=1) : les mêmes déplacements.
Après chaque arrivée (MD? = 1), TP? est lu pendant --settle secondes. Le rapport donne, par phase et par point,
l'écart TP - cible en comptes (49,6 nm chacun) : moyenne, dispersion, maximum.

Ce que le script envoie : lectures (*IDN?, ZZ?, ZH?, SN?, MM?, QM?, TP?, MD?, VA?, AC?, DB?, CL?, FE?, OF?, PH?, TB?) ;
VA, AC et DB (valeurs d'origine restaurées dans un finally) ; MM 1 puis MM 0 ; des PA vers A et B ; ST puis AB en cas
d'erreur ou de Ctrl+C. Il n'envoie ni AF, ni SM, ni ZH, ni SN, ni MV, ni CL, ni FE. max_move du driver = amplitude + 200 :
aucun déplacement plus grand n'est possible.

Il s'arrête sans mouvement s'il y a une erreur en file, si MM n'est pas à 0, si SN n'est pas à 1 ou si l'axe n'est pas
arrêté, puis demande de taper OUI. Montage : 8311 libre, en milieu de course (marge de plus de 1 mm de chaque côté).

Usage (PowerShell, venv actif, depuis le dossier Instrument) :
    python closed_loop_8743.py
    python closed_loop_8743.py --axe 1 --amplitude 2000 --va 1000 --deadband 20 --cycles 3 --settle 2
Sorties : rapport_closed_loop_8743.txt et rapport_closed_loop_8743.json. Arrêt manuel : Ctrl+C.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime

from motion_8743 import Journal, lire_etat
from newport_8743 import Newport8743

PAS_SONDAGE_S = 0.05
PAS_SETTLE_S = 0.5


def aller(inst, ax, a, nom, cible, args, note) -> dict:
    """PA vers `cible`, attente de l'arrêt par MD?, puis lecture de TP? pendant --settle secondes."""
    tp_avant = ax.position()
    t0 = time.monotonic()
    ax.move_absolute(cible)                              # écrit PA puis lit la file d'erreurs
    vu = False
    while True:
        en_mvt = ax.is_moving()
        dt = time.monotonic() - t0
        vu |= en_mvt
        if not en_mvt and (vu or dt > 1.0):
            break
        if dt > args.timeout:
            raise RuntimeError(f"L'axe {a} est encore en mouvement après {args.timeout} s.")
        time.sleep(PAS_SONDAGE_S)
    t_arret = time.monotonic() - t0
    tp_arret = ax.position()
    serie, t1 = [], time.monotonic()
    while time.monotonic() - t1 < args.settle:
        serie.append((round(time.monotonic() - t0, 2), ax.position()))
        time.sleep(PAS_SETTLE_S)
    tp_final = ax.position()
    erreurs = inst.drain_errors()
    v = {"point": nom, "cible": cible, "TP_avant": tp_avant, "TP_a_l_arret": tp_arret, "TP_final": tp_final,
         "ecart_a_l_arret": tp_arret - cible, "ecart_final": tp_final - cible, "duree_mouvement_s": round(t_arret, 2),
         "serie_TP": serie, "erreurs": erreurs}
    note(f"    {nom} (cible {cible}) : arrêt à {t_arret:.1f} s, TP {tp_arret} (écart {v['ecart_a_l_arret']:+d}), "
         f"après {args.settle} s TP {tp_final} (écart {v['ecart_final']:+d}), erreurs {erreurs or 'aucune'}")
    if erreurs:
        raise RuntimeError(f"Erreurs du contrôleur pendant le déplacement vers {nom} : {erreurs}")
    return v


def stats(visites: list[dict], point: str) -> dict:
    e = [v["ecart_final"] for v in visites if v["point"] == point]
    if not e:
        return {}
    return {"n": len(e), "ecarts": e, "moyenne": round(statistics.mean(e), 2), "min": min(e), "max": max(e),
            "dispersion": max(e) - min(e), "max_abs": max(abs(x) for x in e)}


def executer_boucle(inst, args, confirmer, note) -> dict:
    a = args.axe
    ax = getattr(inst, f"axis{a}")
    sortie: dict = {"axe": a, "amplitude": args.amplitude, "va": args.va, "deadband": args.deadband, "cycles": args.cycles}
    avant = lire_etat(inst, ax, a)
    for nom in ("deadband", "update_interval", "following_error", "absolute_found"):
        try:
            avant[nom] = getattr(ax, nom)()
        except Exception as exc:
            avant[nom] = f"échec : {exc}"
    err = inst.drain_errors()
    sortie["etat_avant"], sortie["erreurs_avant"] = avant, err
    note(f"État avant : {avant} ; erreurs en file : {err or 'aucune'}")
    refus = []
    if err: refus.append(f"erreurs en file : {err}")
    if avant["MM"] != 0: refus.append("MM n'est pas à 0 (boucle fermée déjà active)")
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

    A = ax.position()
    B = A + args.amplitude
    sortie["A"], sortie["B"] = A, B
    note(f"A = {A}, B = {B} (écart {args.amplitude} comptes, {args.amplitude * 0.0496:.0f} µm).")
    va0, ac0, db0 = avant["VA"], avant["AC"], avant["deadband"]
    sortie["phases"], echec = {}, None
    try:
        ax.velocity(args.va)
        ax.deadband(args.deadband)
        for phase in ("ouverte", "fermee"):
            note(f"Phase boucle {'ouverte (MM=0)' if phase == 'ouverte' else 'fermée (MM=1)'} :")
            visites = []
            if phase == "fermee":
                ax.closed_loop(1)
                sortie["TP_apres_MM1"] = []
                for _ in range(4):
                    time.sleep(PAS_SETTLE_S)
                    sortie["TP_apres_MM1"].append(ax.position())
                note(f"  MM=1 activé, TP lu 4 fois au repos : {sortie['TP_apres_MM1']}")
            for c in range(args.cycles):
                note(f"  cycle {c + 1} :")
                for nom, cible in (("B", B), ("A", A)):
                    visites.append(aller(inst, ax, a, nom, cible, args, note))
            if phase == "fermee":
                ax.closed_loop(0)
            sortie["phases"][phase] = {"visites": visites, "A": stats(visites, "A"), "B": stats(visites, "B")}
            note(f"  Écarts finaux TP - cible (comptes) : A {sortie['phases'][phase]['A']}, B {sortie['phases'][phase]['B']}")
    except BaseException as exc:                      # Ctrl+C compris
        echec = f"{type(exc).__name__} : {exc}"
        note(f"ERREUR : {echec}. Envoi de ST puis AB.")
        for envoi in (ax.stop, inst.abort):
            try:
                envoi()
            except Exception as e2:
                note(f"  {envoi.__name__} a échoué : {e2}")
    finally:
        for nom, valeur in (("closed_loop", 0), ("deadband", db0), ("velocity", va0), ("acceleration", ac0)):
            try:
                getattr(ax, nom)(valeur)
            except Exception as e2:
                note(f"  restauration de {nom} échouée : {e2}")
    apres = lire_etat(inst, ax, a)
    sortie["etat_apres"], sortie["echec"] = apres, echec
    sortie["restaure"] = (apres["MM"], apres["VA"], apres["AC"]) == (0, va0, ac0)
    note(f"MM, VA, AC restaurés : {sortie['restaure']} ; état après : {apres}")
    sortie["resultat"] = "échec : " + echec if echec else "terminé"
    return sortie


def main() -> int:
    p = argparse.ArgumentParser(description="Boucle ouverte contre boucle fermée, 8311 sur le 8743-CL.")
    p.add_argument("--axe", type=int, default=1, choices=(1, 2))
    p.add_argument("--amplitude", type=int, default=2000, help="écart B - A en comptes (49,6 nm), défaut 2000")
    p.add_argument("--va", type=int, default=1000)
    p.add_argument("--deadband", type=int, default=20, help="bande morte DB en comptes (défaut 20, environ 1 µm)")
    p.add_argument("--cycles", type=int, default=3)
    p.add_argument("--settle", type=float, default=2.0, help="secondes de lecture de TP? après chaque arrêt")
    p.add_argument("--timeout", type=float, default=30.0, help="durée maximale d'un déplacement, en secondes")
    p.add_argument("--rapport", default="rapport_closed_loop_8743.txt")
    p.add_argument("--json", default="rapport_closed_loop_8743.json")
    args = p.parse_args()
    if not (100 <= args.amplitude <= 20000 and 1 <= args.va <= 2000 and 0 <= args.deadband <= 1000 and 1 <= args.cycles <= 10):
        print("--amplitude entre 100 et 20000, --va entre 1 et 2000, --deadband entre 0 et 1000, --cycles entre 1 et 10.")
        return 2

    rapport: list[str] = []

    def note(ligne=""):
        print(ligne)
        rapport.append(ligne)

    def confirmer() -> bool:
        n = 2 * args.cycles * 2
        print(f"\nLe 8311 de l'axe {args.axe} va faire {n} déplacements de {args.amplitude} comptes "
              f"({args.amplitude * 0.0496:.0f} µm) entre A et B, d'abord en boucle ouverte puis en boucle fermée (MM=1).")
        print("Il doit être libre, sans rien pousser, en milieu de course. Ctrl+C arrête le moteur.")
        rep = input("Tape OUI pour continuer, autre chose pour annuler : ").strip()
        rapport.append(f"Confirmation demandée, réponse : {rep!r}")
        return rep == "OUI"

    note(f"Rapport closed_loop_8743.py, {datetime.now():%Y-%m-%d %H:%M:%S}")
    note("STATUT : script non exécuté avant ce rapport ; les lignes ci-dessous sont la sortie réelle.")
    from newport_usb import UsbTransport
    journal = Journal(UsbTransport(defensive=True, match="8743"))
    sortie: dict = {"date": datetime.now().isoformat(timespec="seconds")}
    code = 0
    try:
        inst = Newport8743("cl8743", transport=journal, allow_motion=True, max_move=args.amplitude + 200)
        try:
            sortie.update(executer_boucle(inst, args, confirmer, note))
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
