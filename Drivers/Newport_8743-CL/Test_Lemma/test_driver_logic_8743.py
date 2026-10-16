"""Tests du driver 8743-CL contre le faux transport (aucun matériel).
Lancer : python -m pytest test_driver_logic_8743.py -v"""
import ctypes

import pytest

from fake_transport import FakeTransport8743
from newport_8743 import Newport8743
from newport_8742 import Newport8742Error
from newport_usb import UsbTransport

MOUVEMENT = ("PR", "PA", "MV", "JA", "MC", "MT", "MZ", "OR", "AF")


@pytest.fixture
def make():
    def _make(allow_motion=False, max_move=1000, **kw):
        ft = FakeTransport8743(**kw)
        _make.n.append(1)
        return Newport8743(f"n{len(_make.n)}", transport=ft, allow_motion=allow_motion, max_move=max_move), ft
    _make.n = []
    yield _make
    Newport8743.close_all()


def mouvements(ft):
    return [c for c in ft.sent if any(c[1:].startswith(m) for m in MOUVEMENT) and not c.endswith("?")]


def test_idn(make):
    inst, _ = make()
    assert inst.get_idn() == {"vendor": "New_Focus", "model": "8743-CL", "firmware": "4.06", "serial": "13097"}


def test_deux_axes_seulement(make):
    inst, _ = make()
    assert hasattr(inst, "axis1") and hasattr(inst, "axis2") and not hasattr(inst, "axis3")


@pytest.mark.parametrize("nom,valeur", [("velocity", 0), ("velocity", 2001), ("acceleration", 0), ("acceleration", 200001),
                                         ("motor_type", 4), ("units", 2), ("closed_loop", 2), ("update_interval", 0.05),
                                         ("deadband", -1), ("following_error", -1)])
def test_validation_refuse_avant_envoi(make, nom, valeur):
    inst, ft = make()
    ft.sent.clear()
    with pytest.raises(Exception):
        getattr(inst.axis1, nom)(valeur)
    assert not [c for c in ft.sent if not c.endswith("?")]


def test_lectures_mesurees(make):
    inst, _ = make()
    a = inst.axis1
    assert (a.units(), a.closed_loop(), a.hardware_config(), a.update_interval(), a.deadband(),
            a.following_error(), a.motor_type()) == (1, 0, 4, 0.1, 0, 1000, 0)
    assert inst.hardware_status() == 56 and a.is_moving() is False


def test_ecriture_relecture(make):
    inst, _ = make()
    inst.axis2.velocity(1000)
    inst.axis2.update_interval(0.5)
    assert (inst.axis2.velocity(), inst.axis2.update_interval()) == (1000, 0.5)


def test_unite_de_position_suit_sn(make):
    inst, _ = make()
    inst.axis1.position()
    assert inst.axis1.position.unit == "count"
    inst.axis1.units(0)
    inst.axis1.position()
    assert inst.axis1.position.unit == "step"


def test_zh_lecture_seule(make):
    inst, ft = make()
    with pytest.raises(Exception):
        inst.axis1.hardware_config(0)
    assert not [c for c in ft.sent if "ZH" in c and not c.endswith("?")]


def test_pas_de_commandes_absentes(make):
    inst, _ = make()
    for nom in ("find_home", "home", "move_to_limit", "find_index"):
        assert not hasattr(inst.axis1, nom)


def test_erreur_controleur_levee(make):
    inst, ft = make()
    ft.errors.append("108, MOTOR NOT CONNECTED")
    with pytest.raises(Newport8742Error, match="MOTOR NOT CONNECTED"):
        inst.axis1.velocity(500)


def test_mouvement_refuse_sans_allow_motion(make):
    inst, ft = make(allow_motion=False, qm=3)
    for appel in (lambda: inst.axis1.move_relative(10), lambda: inst.axis1.move_absolute(10), inst.axis1.find_absolute):
        with pytest.raises(Newport8742Error, match="allow_motion"):
            appel()
    assert mouvements(ft) == []


def test_mouvement_qm0_permis_si_detection_auto(make):
    inst, ft = make(allow_motion=True, qm=0, zz=0)
    inst.axis1.move_relative(-25)
    assert mouvements(ft) == ["1PR-25"]


def test_mouvement_qm0_refuse_si_detection_coupee(make):
    inst, ft = make(allow_motion=True, qm=0, zz=1)
    with pytest.raises(Newport8742Error, match="détection automatique"):
        inst.axis1.move_relative(10)
    assert mouvements(ft) == []


def test_mouvement_qm3_sans_zz(make):
    inst, ft = make(allow_motion=True, qm=3, zz=1)
    inst.axis1.move_relative(10)
    assert mouvements(ft) == ["1PR10"]


def test_max_move(make):
    inst, ft = make(allow_motion=True, qm=3, max_move=100)
    inst.axis1.move_relative(100)
    with pytest.raises(Newport8742Error, match="max_move"):
        inst.axis1.move_relative(101)
    with pytest.raises(Newport8742Error, match="max_move"):
        inst.axis1.move_absolute(500)
    inst.axis1.move_absolute(inst.axis1.position() + 50)
    assert mouvements(ft)[-1].startswith("1PA")
    with pytest.raises(Newport8742Error, match="32 bits"):
        inst.axis1.move_relative(2**31)


def test_find_absolute_conditions(make):
    inst, ft = make(allow_motion=True, qm=3)
    inst.axis1.find_absolute()
    assert "1AF" in ft.sent
    with pytest.raises(Newport8742Error, match="quasi-absolu"):
        inst.axis2.find_absolute()                  # ZH axe 2 = 0
    ft.val["1SN"] = 0
    with pytest.raises(Newport8742Error, match="SN"):
        inst.axis1.find_absolute()


def test_boucle_fermee(make):
    inst, ft = make(allow_motion=False)
    with pytest.raises(Newport8742Error, match="allow_motion"):
        inst.axis1.closed_loop(1)
    inst.axis1.closed_loop(0)                        # couper est toujours permis
    inst2, ft2 = make(allow_motion=True, sn=0)
    with pytest.raises(Newport8742Error, match="SN"):
        inst2.axis1.closed_loop(1)
    inst3, ft3 = make(allow_motion=True)
    inst3.axis1.closed_loop(1)
    assert ft3.val["1MM"] == 1


def test_arrets_toujours_permis(make):
    inst, ft = make(allow_motion=False)
    inst.axis1.stop()
    inst.abort()
    assert "1ST" in ft.sent and "AB" in ft.sent


# -- transport défensif, contre une fausse DLL --
class FausseDll:
    """avant : réponses déjà dans le pilote (orphelines). apres : réponses qui arrivent après l'envoi,
    None = lecture vide (réponse pas encore arrivée)."""

    def __init__(self, avant, apres):
        self.file, self.apres, self.envoyees = list(avant), list(apres), []

    def newp_usb_send_ascii(self, dev, brut, n):
        self.envoyees.append(brut.decode())
        self.file.extend(self.apres)
        self.apres = []
        return 0

    def newp_usb_get_ascii(self, dev, tampon, taille, nb_ref):
        if not self.file:
            return 1
        rep = self.file.pop(0)
        if rep is None:
            return 1
        ctypes.memmove(tampon, rep, len(rep))
        nb_ref._obj.value = len(rep)
        return 0


def transport(avant, apres):
    t = object.__new__(UsbTransport)
    t._dll, t.device_id, t._open = FausseDll(avant, apres), 1, False
    t.pause_s, t.defensive, t.poll_max_s, t.poll_step_s = 0.0, True, 0.5, 0.0
    t.orphelines, t.tardives, t._vider_requis = [], [], True
    return t


def test_transport_vide_les_orphelines():
    t = transport([b"0, NO ERROR DETECTED\r\n"], [b"2000\r\n"])
    assert t.ask("1VA?") == "2000"
    assert len(t.orphelines) == 1


def test_transport_attend_une_reponse_tardive():
    t = transport([], [None, None, b"2000\r\n"])
    assert t.ask("1VA?") == "2000"


def test_transport_leve_sans_reponse():
    t = transport([], [])
    t.poll_max_s = 0.05
    with pytest.raises(RuntimeError, match="Pas de réponse"):
        t.ask("1VA?")


def test_transport_ne_vide_pas_entre_deux_requetes():
    t = transport([], [b"2000\r\n"])
    t.ask("1VA?")
    lectures = []
    ancien = t._dll.newp_usb_get_ascii
    t._dll.newp_usb_get_ascii = lambda *a: (lectures.append(1), ancien(*a))[1]
    t._dll.apres = [b"100000\r\n"]
    t.ask("1AC?")
    assert len(lectures) == 1                      # une seule lecture : la réponse, sans vidage préalable


def test_transport_vide_apres_une_ecriture():
    t = transport([], [b"2000\r\n"])
    t.ask("1VA?")
    t.write("1VA1500")
    t._dll.file.append(b"parasite\r\n")             # réponse inattendue produite par l'écriture
    t._dll.apres = [b"0, NO ERROR DETECTED\r\n"]
    assert t.ask("TB?") == "0, NO ERROR DETECTED"
    assert len(t.orphelines) == 1
