"""Tests du driver contre le faux transport (aucun matériel). Lancer : python -m pytest test_driver_logic.py -v"""
import pytest

from fake_transport import FakeTransport
from newport_8742 import Newport8742, Newport8742Error

MOUVEMENT = ("PR", "PA", "MV", "JA", "MC", "MT", "OR")


@pytest.fixture
def make():
    cree = []

    def _make(qm=0, allow_motion=False):
        ft = FakeTransport(qm=qm)
        inst = Newport8742(f"n{len(cree)}", transport=ft, allow_motion=allow_motion)
        cree.append(inst)
        return inst, ft
    yield _make
    Newport8742.close_all()


def envoyees_mouvement(ft):
    return [c for c in ft.sent if any(c[1:].startswith(m) for m in MOUVEMENT)]


def test_idn(make):
    inst, _ = make()
    assert inst.get_idn() == {"vendor": "New_Focus", "model": "8742", "firmware": "3.04", "serial": "108042"}


@pytest.mark.parametrize("nom,valeur", [("velocity", 0), ("velocity", 2001), ("acceleration", 0),
                                         ("acceleration", 200001), ("motor_type", 4)])
def test_validation_refuse_avant_envoi(make, nom, valeur):
    inst, ft = make()
    ft.sent.clear()
    with pytest.raises(Exception):
        getattr(inst.axis1, nom)(valeur)
    assert not any(c[1:3] in ("VA", "AC", "QM") and not c.endswith("?") for c in ft.sent)


def test_ecriture_et_relecture(make):
    inst, ft = make()
    inst.axis2.velocity(1000)
    inst.axis2.acceleration(5000)
    assert (inst.axis2.velocity(), inst.axis2.acceleration()) == (1000, 5000)
    assert ft.val["1VA"] == 2000


def test_tiny_limite_a_1750(make):
    inst, _ = make(qm=2)
    inst.axis1.velocity(1750)
    with pytest.raises(Newport8742Error, match="Tiny"):
        inst.axis1.velocity(1800)


def test_erreur_controleur_levee(make):
    inst, ft = make()
    ft.errors.append("108, MOTOR NOT CONNECTED")
    with pytest.raises(Newport8742Error, match="MOTOR NOT CONNECTED"):
        inst.axis1.velocity(500)


def test_mouvement_refuse_sans_allow_motion(make):
    inst, ft = make(qm=3, allow_motion=False)
    with pytest.raises(Newport8742Error, match="allow_motion"):
        inst.axis1.move_relative(10)
    assert envoyees_mouvement(ft) == []


def test_mouvement_refuse_sans_type_moteur(make):
    inst, ft = make(qm=0, allow_motion=True)
    with pytest.raises(Newport8742Error, match="QM=0"):
        inst.axis1.move_relative(10)
    assert envoyees_mouvement(ft) == []


def test_mouvement_envoye_si_autorise(make):
    inst, ft = make(qm=3, allow_motion=True)
    inst.axis1.move_relative(-25)
    inst.axis1.move_absolute(100)
    assert envoyees_mouvement(ft) == ["1PR-25", "1PA100"]
    with pytest.raises(Newport8742Error, match="32 bits"):
        inst.axis1.move_relative(2**31)


def test_arrets_toujours_permis(make):
    inst, ft = make(qm=0, allow_motion=False)
    inst.axis1.stop()
    inst.abort()
    assert "1ST" in ft.sent and "AB" in ft.sent


def test_lectures(make):
    inst, _ = make()
    assert inst.axis3.position() == 0
    assert inst.axis3.is_moving() is False
