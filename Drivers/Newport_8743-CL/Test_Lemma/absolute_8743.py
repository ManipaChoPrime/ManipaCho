# -*- coding: utf-8 -*-
"""Recherche de position absolue (AF) du 8311 sur le 8743-CL : la position se retrouve-t-elle après une mise hors tension ?

STATUT : NON EXÉCUTÉ sur matériel. Vérifié seulement contre un faux contrôleur (check_absolute_8743.py).

Le manuel (8743-CL, AD, AF, OF?) ne dit pas jusqu'où l'axe se déplace pendant AF. Ce script est donc prudent :
  * il lit l'état et s'arrête sans mouvement s'il y a une erreur en file, si ZH bit 2 n'est pas à 1 (codeur quasi-absolu
    déclaré), si SN n'est pas à 1, si MM n'est pas à 0 ou si l'axe n'est pas arrêté ;
  * il règle AD (mode final) : par défaut 1, retour à la position de départ de la recherche ;
  * il lance AF, puis lit AF? et TP? toutes les 0,5 s ; il envoie ST puis AB si TP s'éloigne de plus de --max-comptes
    du départ (défaut 20000 comptes, environ 1 mm) ou si la recherche dépasse --timeout secondes ;
  * il restaure AD dans un finally.
Il n'envoie ni PA, ni PR, ni MV, ni SM, ni ZH, ni SN, ni MM. AF est la seule commande de mouvement.

Usage (PowerShell, venv actif, depuis le dossier Instrument) :
    python absolute_8743.py
    python absolute_8743.py --axe 1 --mode 1 --max-comptes 20000 --timeout 120
    python absolute_8743.py --comparer rapport_absolute_8743_precedent.json     (compare TP absolu à un essai précédent)
Sorties : rapport_absolute_8743.txt et rapport_absolute_8743.json. Arrêt manuel : Ctrl+C (ST puis AB).

Protocole pour savoir si la position survit à une mise hors tension :
  1. lancer le script, renommer rapport_absolute_8743.json en absolute_1.json ;
  2. éteindre le 8743-CL, le rallumer sans toucher au 8311 ;
  3. relancer avec --comparer absolute_1.json : les TP absolus après AF doivent être égaux à quelques comptes près.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime

from motion_8743 import Journal, lire_etat
from newport_8743 import Newport8743

PAS_S = 0.5


def executer_absolu(inst, args, confirmer, note, ancien=None) -> dict:
    a = args.axe
    ax = getattr(inst, f"axis{a}")
    sortie: dict = {"axe": a, "mode_AD": args.mode, "max_comptes": args.max_comptes}
    avant = lire_etat(inst, ax, a)
    for nom in ("absolute_search_mode", "absolute_found", "absolute_search_done"):
        try:
            avant[nom] = getattr(ax, nom)()
        except Exception as exc:
            avant[nom] = f"échec : {exc}"
    err = inst.drain_errors()
    sortie["etat_avant"], sortie["erreurs_avant"] = avant, err
    note(f"État avant : {avant} ; erreurs en file : {err or 'aucune'}")
    refus = []
    if err: refus.append(f"erreurs en file : {err}")
    if not avant["ZH"] & 4: refus.append("ZH bit 2 = 0 : codeur quasi-absolu non déclaré")
    if avant["SN"] != 1: refus.append("SN n'est pas à 1")
    if avant["MM"] != 0: refus.append("MM n'est pas à 0")
    if not avant["arrete"]: refus.append("l'axe n'est pas arrêté")
    if refus:
        sortie["resultat"] = "refus avant mouvement : " + " ; ".join(refus)
        note("ARRÊT SANS MOUVEMENT : " + sortie["resultat"])
        return sortie
    if not confirmer():
        sortie["resultat"] = "annulé par l'utilisateur, aucun mouvement"
        note(sortie["resultat"])
        return sortie

    tp0 = avant["TP"]
    ad0 = avant["absolute_search_mode"]
    suivi, echec = [], None
    try:
        ax.absolute_search_mode(args.mode)
        t0 = time.monotonic()
        ax.find_absolute()
        note("AF lancé. Suivi de AF? et TP? :")
        while True:
            termine = ax.absolute_search_done()
            tp = ax.position()
            dt = time.monotonic() - t0
            suivi.append((round(dt, 1), tp, termine))
            note(f"    t = {dt:5.1f} s, TP = {tp}, AF? = {int(termine)}")
            if termine:
                break
            if abs(tp - tp0) > args.max_comptes:
                raise RuntimeError(f"TP s'est éloigné de {abs(tp - tp0)} comptes du départ (limite {args.max_comptes}).")
            if dt > args.timeout:
                raise RuntimeError(f"Recherche d'absolu encore en cours après {args.timeout} s.")
            time.sleep(PAS_S)
        sortie["duree_s"] = round(time.monotonic() - t0, 1)
        sortie["erreurs_apres_AF"] = inst.drain_errors()
        if sortie["erreurs_apres_AF"]:
            raise RuntimeError(f"Erreurs du contrôleur après AF : {sortie['erreurs_apres_AF']}")
    except BaseException as exc:                      # Ctrl+C compris
        echec = f"{type(exc).__name__} : {exc}"
        note(f"ERREUR : {echec}. Envoi de ST puis AB.")
        for envoi in (ax.stop, inst.abort):
            try:
                envoi()
            except Exception as e2:
                note(f"  {envoi.__name__} a échoué : {e2}")
    finally:
        try:
            ax.absolute_search_mode(ad0 if isinstance(ad0, int) else 0)
        except Exception as e2:
            note(f"  restauration de AD échouée : {e2}")
    time.sleep(PAS_S)
    apres = lire_etat(inst, ax, a)
    for nom in ("absolute_found",):
        try:
            apres[nom] = getattr(ax, nom)()
        except Exception as exc:
            apres[nom] = f"échec : {exc}"
    sortie["suivi"], sortie["etat_apres"], sortie["echec"] = suivi, apres, echec
    tps = [t for _, t, _ in suivi] or [tp0]
    sortie["TP_depart"], sortie["TP_absolu_apres"] = tp0, apres["TP"]
    sortie["excursion_comptes"] = (min(tps) - tp0, max(tps) - tp0)
    note(f"TP avant {tp0}, TP après {apres['TP']}, OF? après : {apres['absolute_found']}, "
         f"excursion pendant AF : de {sortie['excursion_comptes'][0]:+d} à {sortie['excursion_comptes'][1]:+d} comptes "
         f"({(sortie['excursion_comptes'][1] - sortie['excursion_comptes'][0]) * 0.0496:.0f} µm)")
    if ancien and not echec:
        d = apres["TP"] - ancien["TP_absolu_apres"]
        sortie["ecart_avec_ancien"] = d
        note(f"Comparaison : TP absolu {apres['TP']} contre {ancien['TP_absolu_apres']} pour l'essai précédent, écart {d:+d} comptes "
             f"({d * 0.0496:+.2f} µm).")
    sortie["resultat"] = "échec : " + echec if echec else "terminé"
    return sortie


def main() -> int:
    p = argparse.ArgumentParser(description="Recherche de position absolue du 8311 sur le 8743-CL.")
    p.add_argument("--axe", type=int, default=1, choices=(1, 2))
    p.add_argument("--mode", type=int, default=1, choices=(0, 1, 2), help="AD : 0 aucun mouvement final, 1 retour au départ (défaut), 2 zéro absolu")
    p.add_argument("--max-comptes", type=int, default=20000, help="éloignement maximal de TP pendant AF avant arrêt (défaut 20000, environ 1 mm)")
    p.add_argument("--timeout", type=float, default=120.0)
    p.add_argument("--comparer", default=None, help="rapport JSON d'un essai précédent")
    p.add_argument("--rapport", default="rapport_absolute_8743.txt")
    p.add_argument("--json", default="rapport_absolute_8743.json")
    args = p.parse_args()
    ancien = json.load(open(args.comparer, encoding="utf-8")) if args.comparer else None

    rapport: list[str] = []

    def note(ligne=""):
        print(ligne)
        rapport.append(ligne)

    def confirmer() -> bool:
        print(f"\nAF va déplacer le 8311 de l'axe {args.axe} sur une distance que le manuel ne donne pas. Mode final AD={args.mode}. "
              f"Arrêt automatique au-delà de {args.max_comptes} comptes ({args.max_comptes * 0.0496 / 1000:.1f} mm) du départ.")
        print("Il doit être libre, sans rien pousser, en milieu de course. Ctrl+C arrête le moteur.")
        rep = input("Tape OUI pour continuer, autre chose pour annuler : ").strip()
        rapport.append(f"Confirmation demandée, réponse : {rep!r}")
        return rep == "OUI"

    note(f"Rapport absolute_8743.py, {datetime.now():%Y-%m-%d %H:%M:%S}")
    note("STATUT : script non exécuté avant ce rapport ; les lignes ci-dessous sont la sortie réelle.")
    from newport_usb import UsbTransport
    journal = Journal(UsbTransport(defensive=True, match="8743"))
    sortie: dict = {"date": datetime.now().isoformat(timespec="seconds")}
    code = 0
    try:
        inst = Newport8743("ab8743", transport=journal, allow_motion=True, max_move=args.max_comptes)
        try:
            sortie.update(executer_absolu(inst, args, confirmer, note, ancien))
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
