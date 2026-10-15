"""Tests des fonctions de haut niveau sur le 8743-CL réel, à partir du fichier unique newport_picomotors.py.
Fermer l'application Picomotor avant. Le 8311 est sur l'axe 1.

Étape 1, sans mouvement (la référence est posée par DH à la position actuelle, sans bouger l'axe) :
    $env:NEWPORT_HARDWARE=1 ; python -m pytest test_hardware_api_8743.py -v -s
Étape 2, mouvements minuscules (+-100 comptes, 5 µm, recul d approche de 500 comptes) : 8311 libre, en milieu de course :
    $env:NEWPORT_HARDWARE=1 ; $env:NEWPORT_MOTION=1 ; python -m pytest test_hardware_api_8743.py -v -s

Le fichier de positions est temporaire. VA, AC, DB et MM sont restaurés à la fin."""
import os

import pytest

from newport_picomotors import SENTINELLE, Newport8742Error, connect_8743

pytestmark = pytest.mark.skipif(os.environ.get("NEWPORT_HARDWARE") != "1", reason="définir NEWPORT_HARDWARE=1")
MOUVEMENT = os.environ.get("NEWPORT_MOTION") == "1"


@pytest.fixture(scope="module")
def pico(tmp_path_factory):
    fichier = str(tmp_path_factory.mktemp("pos") / "pos.json")
    p = connect_8743("hwapi", allow_motion=MOUVEMENT, max_velocity=2000, max_move=800, positions_file=fichier)
    ax = p.axis1
    etat = {n: getattr(ax, n)() for n in ("velocity", "acceleration", "deadband", "closed_loop")}
    yield p
    for nom in ("closed_loop", "deadband", "velocity", "acceleration"):
        try:
            getattr(ax, nom)(etat[nom])
        except Exception as exc:
            print(f"restauration de {nom} échouée : {exc}")
    print("\ntransport : orphelines", p._transport.orphelines, "tardives", p._transport.tardives)
    p.close()


def test_where_sans_mouvement(pico):
    w = pico.axis1.where()
    print("\nwhere() :", w)
    assert isinstance(w["counts"], int) and w["en_mouvement"] is False


def test_set_reference_pose_tp_sans_bouger(pico):
    ax = pico.axis1
    if ax.reference_valid:
        ax.set_reference(force=True)
    else:
        ax.set_reference()
    assert ax.reference_valid and ax.where()["counts"] == SENTINELLE
    with pytest.raises(Newport8742Error, match="existe déjà"):
        ax.set_reference()


def test_mark_et_positions(pico):
    ax = pico.axis1
    p = ax.mark("T")
    assert p["counts"] == SENTINELLE and "T" in ax.positions() and ax.where()["positions_proches"] == ["T"]
    ax.forget("T")
    assert "T" not in ax.positions()


def test_vitesse_et_distance_refusees_sans_toucher_au_controleur(pico):
    ax = pico.axis1
    va = ax.velocity()
    with pytest.raises(Exception):
        ax.move(10, speed=3000)
    with pytest.raises(Newport8742Error):
        ax.move(10_000)                      # au-delà de max_move=800 ou de allow_motion
    assert ax.velocity() == va and pico.drain_errors() == []


@pytest.mark.skipif(not MOUVEMENT, reason="définir NEWPORT_MOTION=1 pour les mouvements")
def test_move_aller_retour_et_goto(pico):
    ax = pico.axis1
    ax.mark("A")
    r1 = ax.move(100, speed="normal")
    r2 = ax.move(-100, speed="normal")
    print("\nmove +100 :", r1, "\nmove -100 :", r2)
    assert abs(r1["ecart_comptes"]) <= 2 and abs(r2["ecart_comptes"]) <= 2
    ax.move(100, speed="normal")
    g = ax.goto("A")                         # approche par le côté +, boucle fermée pendant le déplacement
    print("goto A :", g)
    assert abs(g["ecart_comptes"]) <= 2 and ax.closed_loop() == 0 and ax.deadband() == 0
    r3 = ax.nudge(1)
    r4 = ax.nudge(-1)
    print("nudge +1, -1 :", r3, r4)
    ax.goto("A", closed_loop=False)
    assert abs(ax.where()["counts"] - SENTINELLE) <= 2
