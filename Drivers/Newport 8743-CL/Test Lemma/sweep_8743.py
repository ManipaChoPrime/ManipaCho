# -*- coding: utf-8 -*-
"""Balayage de vitesses et de distances : PA entre A et B, boucle ouverte puis fermée, pour chaque combinaison.

STATUT : NON EXÉCUTÉ sur matériel. Vérifié seulement contre un faux contrôleur (check_sweep_8743.py).

Enchaîne closed_loop_8743.executer_boucle pour chaque combinaison VA:comptes de --combos, avec une seule confirmation.
A = position de départ de chaque combinaison (le dernier retour finit sur A, donc elle ne dérive pas si PA est exact),
B = A + comptes. Le script s'arrête à la première combinaison qui échoue (erreur, Ctrl+C) : MM, VA, AC et DB sont
restaurés, ST puis AB envoyés. Mêmes commandes que closed_loop_8743.py : lectures, VA, AC, DB, MM 1 puis MM 0, PA vers A et B.
Pas de AF, SM, ZH, SN, MV.

Usage (PowerShell, venv actif, depuis le dossier Instrument) :
    python sweep_8743.py
    python sweep_8743.py --combos 1000:20000,2000:20000,2000:40000 --deadband 2 --cycles 2
Sorties : rapport_sweep_8743.txt et rapport_sweep_8743.json (la table récapitulative est à la fin du .txt).
Montage : 8311 libre, en milieu de course, plus de 2,2 mm de marge de chaque côté pour 40000 comptes.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from datetime import datetime
from types import SimpleNamespace

from closed_loop_8743 import executer_boucle
from motion_8743 import Journal
from newport_8743 import Newport8743

COMPTE_PAR_S_PAR_VA = 0.6      # mesures du 2026-10-15 : 0,59 à 0,71 comptage/s par unité de VA
SURCOUT_DEPLACEMENT_S = 3.5    # écriture, lecture de TB?, 2 s de lecture de TP? après l'arrêt


def combos_depuis(texte: str) -> list[tuple[int, int]]:
    res = []
    for bloc in texte.split(","):
        va, amp = bloc.split(":")
        res.append((int(va), int(amp)))
    return res


def tableau(resultats: list[dict]) -> list[str]:
    lignes = ["VA     comptes   boucle    écart max A   écart max B   durée moy. aller (s)   durée moy. retour (s)"]
    for r in resultats:
        for phase in ("ouverte", "fermee"):
            ph = r.get("phases", {}).get(phase)
            if not ph:
                continue
            vis = ph["visites"]
            dB = [v["duree_mouvement_s"] for v in vis if v["point"] == "B"]
            dA = [v["duree_mouvement_s"] for v in vis if v["point"] == "A"]
            lignes.append(f"{r['va']:<6d} {r['amplitude']:<9d} {phase:<9s} {ph['A'].get('max_abs', '-'):<13} {ph['B'].get('max_abs', '-'):<13} "
                          f"{statistics.mean(dB):<22.1f} {statistics.mean(dA):.1f}")
    return lignes


def main() -> int:
    p = argparse.ArgumentParser(description="Balayage de vitesses et de distances du 8311 sur le 8743-CL.")
    p.add_argument("--axe", type=int, default=1, choices=(1, 2))
    p.add_argument("--combos", default="1000:20000,2000:20000,2000:40000", help="liste VA:comptes séparée par des virgules")
    p.add_argument("--deadband", type=int, default=2)
    p.add_argument("--cycles", type=int, default=2)
    p.add_argument("--settle", type=float, default=2.0)
    p.add_argument("--rapport", default="rapport_sweep_8743.txt")
    p.add_argument("--json", default="rapport_sweep_8743.json")
    args = p.parse_args()
    combos = combos_depuis(args.combos)
    if not all(1 <= va <= 2000 and 100 <= amp <= 45000 for va, amp in combos) or not 0 <= args.deadband <= 1000 or not 1 <= args.cycles <= 10:
        print("VA entre 1 et 2000, comptes entre 100 et 45000 (environ 2,2 mm), --deadband entre 0 et 1000, --cycles entre 1 et 10.")
        return 2

    rapport: list[str] = []

    def note(ligne=""):
        print(ligne)
        rapport.append(ligne)

    duree = sum(4 * args.cycles * (amp / (COMPTE_PAR_S_PAR_VA * va) + SURCOUT_DEPLACEMENT_S) for va, amp in combos)

    def confirmer() -> bool:
        print(f"\nLe 8311 de l'axe {args.axe} va faire {len(combos)} séries de déplacements entre A et B, "
              f"d'abord en boucle ouverte puis fermée (MM=1) : {', '.join(f'VA={va} sur {amp} comptes ({amp * 0.0496 / 1000:.2f} mm)' for va, amp in combos)}.")
        print(f"Durée estimée : {duree / 60:.0f} minutes. Le moteur sera bruyant à VA élevée. Libre, en milieu de course, "
              f"plus de {max(a for _, a in combos) * 0.0496 / 1000 + 0.2:.1f} mm de marge de chaque côté. Ctrl+C arrête le moteur.")
        rep = input("Tape OUI pour continuer, autre chose pour annuler : ").strip()
        rapport.append(f"Confirmation demandée, réponse : {rep!r}")
        return rep == "OUI"

    note(f"Rapport sweep_8743.py, {datetime.now():%Y-%m-%d %H:%M:%S}")
    note("STATUT : script non exécuté avant ce rapport ; les lignes ci-dessous sont la sortie réelle.")
    from newport_usb import UsbTransport
    journal = Journal(UsbTransport(defensive=True, match="8743"))
    resultats: list[dict] = []
    sortie: dict = {"date": datetime.now().isoformat(timespec="seconds"), "combos": combos}
    code = 0
    confirme = {"fait": False}

    def confirmer_une_fois() -> bool:
        if confirme["fait"]:
            return True
        confirme["fait"] = confirmer()
        return confirme["fait"]

    try:
        inst = Newport8743("sw8743", transport=journal, allow_motion=True, max_move=max(a for _, a in combos) + 200)
        try:
            for va, amp in combos:
                note(f"\n=== VA={va}, {amp} comptes ({amp * 0.0496:.0f} µm) ===")
                a = SimpleNamespace(axe=args.axe, amplitude=amp, va=va, deadband=args.deadband, cycles=args.cycles,
                                    settle=args.settle, timeout=max(90.0, 3 * amp / (COMPTE_PAR_S_PAR_VA * va)))
                r = executer_boucle(inst, a, confirmer_une_fois, note)
                resultats.append(r)
                if r["resultat"] != "terminé":
                    note(f"Balayage arrêté : {r['resultat']}")
                    break
        finally:
            inst.close()
    except Exception as exc:
        note(f"ERREUR imprévue ({type(exc).__name__}) : {exc}. Envoyez ce rapport en entier.")
        sortie["erreur"] = f"{type(exc).__name__} : {exc}"
        code = 1
    note("\nRécapitulatif (écarts TP - cible en comptes, valeur absolue maximale) :")
    for ligne in tableau(resultats):
        note(ligne)
    sortie["resultats"] = resultats
    sortie["echanges"] = journal.echanges
    with open(args.rapport, "w", encoding="utf-8") as f:
        f.write("\n".join(rapport) + "\n")
    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(sortie, f, ensure_ascii=False, indent=2)
    print(f"\nRapports écrits : {os.path.abspath(args.rapport)} et {os.path.abspath(args.json)}")
    return code


if __name__ == "__main__":
    sys.exit(main())
