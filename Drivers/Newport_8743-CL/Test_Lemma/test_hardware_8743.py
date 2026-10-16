"""Tests sur le 8743-CL réel, USB, SANS MOUVEMENT. Fermer l'application Picomotor avant.
Lancer (PowerShell) :  $env:NEWPORT_HARDWARE=1 ; python -m pytest test_hardware_8743.py -v -s
VA et AC de chaque axe sont restaurés à la fin. Le 8311 doit être sur l'axe 1 (l'axe 2 sert de témoin)."""
import os

import pytest

from newport_8742 import Newport8742Error
from newport_8743 import Newport8743

pytestmark = pytest.mark.skipif(os.environ.get("NEWPORT_HARDWARE") != "1",
                                reason="définir NEWPORT_HARDWARE=1 pour tester le matériel")


@pytest.fixture(scope="module")
def inst():
    i = Newport8743("hw8743")        # allow_motion=False : aucun mouvement possible
    yield i
    print("\ntransport : orphelines", i._transport.orphelines, "tardives", i._transport.tardives)
    i.close()


def test_idn(inst):
    idn = inst.get_idn()
    assert idn["model"] == "8743-CL" and idn["firmware"]


def test_file_erreurs_vide(inst):
    assert inst.drain_errors() == []


def test_lectures_par_axe(inst):
    for ax in (inst.axis1, inst.axis2):
        assert ax.motor_type() in (0, 1, 2, 3)
        assert ax.units() in (0, 1)
        assert ax.closed_loop() in (0, 1)
        assert isinstance(ax.position(), int) and ax.position.unit in ("count", "step")
        assert isinstance(ax.is_moving(), bool)
        assert ax.update_interval() > 0 and ax.deadband() >= 0 and ax.following_error() >= 0
        assert isinstance(ax.hardware_config(), int)
    assert 0 <= inst.hardware_status() <= 63
    print("\nZH axe 1 :", inst.axis1.hardware_config(), "PH :", inst.hardware_status(), "TP axe 1 :", inst.axis1.position())


def test_va_ac_ecriture_relecture_et_restauration(inst):
    for ax in (inst.axis1, inst.axis2):
        va0, ac0 = ax.velocity(), ax.acceleration()
        try:
            ax.velocity(1000)
            ax.acceleration(50000)
            assert (ax.velocity(), ax.acceleration()) == (1000, 50000)
        finally:
            ax.velocity(va0)
            ax.acceleration(ac0)
        assert (ax.velocity(), ax.acceleration()) == (va0, ac0)


def test_validation_refuse_sans_toucher_au_controleur(inst):
    va0 = inst.axis1.velocity()
    with pytest.raises(Exception):
        inst.axis1.velocity(0)
    assert inst.axis1.velocity() == va0 and inst.drain_errors() == []


def test_zh_lecture_seule(inst):
    zh0 = inst.axis1.hardware_config()
    with pytest.raises(Exception):
        inst.axis1.hardware_config(0)
    assert inst.axis1.hardware_config() == zh0


def test_mouvements_refuses(inst):
    for appel in (lambda: inst.axis1.move_relative(1), lambda: inst.axis1.move_absolute(1),
                  inst.axis1.find_absolute, lambda: inst.axis1.closed_loop(1)):
        with pytest.raises(Newport8742Error, match="allow_motion"):
            appel()
    assert inst.axis1.closed_loop() == 0
