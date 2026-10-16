"""Tests sur le 8742 réel, USB, SANS MOUVEMENT. Fermer l'application Picomotor avant.
Lancer (PowerShell) :  $env:NEWPORT_HARDWARE=1 ; python -m pytest test_hardware_8742.py -v
VA et AC de chaque axe sont restaurés à la fin."""
import os

import pytest

from newport_8742 import Newport8742, Newport8742Error

pytestmark = pytest.mark.skipif(os.environ.get("NEWPORT_HARDWARE") != "1",
                                reason="définir NEWPORT_HARDWARE=1 pour tester le matériel")


@pytest.fixture(scope="module")
def inst():
    i = Newport8742("hw8742")        # allow_motion=False : aucun mouvement possible
    yield i
    i.close()


def test_idn(inst):
    idn = inst.get_idn()
    assert idn["model"] == "8742" and idn["firmware"]


def test_file_erreurs_vide(inst):
    assert inst.drain_errors() == []


def test_lectures_par_axe(inst):
    for ax in (inst.axis1, inst.axis2, inst.axis3, inst.axis4):
        assert ax.motor_type() in (0, 1, 2, 3)
        assert isinstance(ax.position(), int)
        assert isinstance(ax.is_moving(), bool)


def test_va_ac_ecriture_relecture_et_restauration(inst):
    for ax in (inst.axis1, inst.axis2, inst.axis3, inst.axis4):
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


def test_mouvement_refuse(inst):
    with pytest.raises(Newport8742Error, match="allow_motion"):
        inst.axis1.move_relative(1)
