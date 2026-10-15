# -*- coding: utf-8 -*-
"""Driver QCoDeS du contrôleur Newport 8743-CL (2 axes, boucle ouverte ou fermée), USB.

Références : docs/protocol_8743.md (mesures sur le 8743-CL série 13097, firmware v4.06) et
docs/protocol_8742.md (tableaux de commandes avec les pages du manuel).

Règles de sûreté :
  * Aucun mouvement sans allow_motion=True à la construction.
  * Un déplacement dépasse au plus max_move comptes (défaut 1000, environ 50 µm avec le codeur du 8311).
  * Type de moteur : QM=2 ou 3 suffit. Avec QM=0 ou 1, le mouvement n'est permis que si la détection
    automatique est active (ZZ bit 0 = 0), le contrôleur détecte alors le moteur au mouvement.
  * VA (1 à 2000 pas/s, 1750 pour un Tiny) et AC (1 à 200000 pas/s²) sont validés par le driver.
  * ZH (limites matérielles, suivi, codeur quasi-absolu) est en lecture seule : l'écrire peut couper les limites.
  * Boucle fermée : MM=1 exige SN=1 et allow_motion=True ; la couper est toujours permis.
  * OR, MT et MZ sont absents : le 8311 a un codeur quasi-absolu (ZH bit 2) et le contrôleur les refuse (erreur x37).
  * Après chaque écriture, la file d'erreurs (TB?) est lue ; une erreur lève Newport8742Error.
"""
from __future__ import annotations

import re

from qcodes.instrument import Instrument, InstrumentChannel
from qcodes.validators import Ints, Numbers

from newport_8742 import (AC_MAX, AC_MIN, INT32, MOTOR_STANDARD, MOTOR_TINY, VA_MAX, VA_MAX_TINY, VA_MIN,
                          Newport8742Error)

ZH_BIT_QUASI_ABSOLUTE = 4  # bit 2 de ZH
UNITE_COMPTES, UNITE_PAS = 1, 0


class Newport8743Axis(InstrumentChannel):
    def __init__(self, parent: "Newport8743", name: str, axis: int):
        super().__init__(parent, name)
        self.axis = axis
        self.add_parameter("velocity", unit="step/s", vals=Ints(VA_MIN, VA_MAX),
                           get_cmd=lambda: self._get_int("VA?"), set_cmd=self._set_velocity,
                           docstring="VA : 1 à 2000 pas/s (1750 pour un Tiny). Unité avec SN=1 non mesurée.")
        self.add_parameter("acceleration", unit="step/s^2", vals=Ints(AC_MIN, AC_MAX),
                           get_cmd=lambda: self._get_int("AC?"), set_cmd=lambda v: self._set("AC", v),
                           docstring="AC : 1 à 200000 pas/s².")
        self.add_parameter("motor_type", vals=Ints(0, 3), get_cmd=lambda: self._get_int("QM?"),
                           set_cmd=lambda v: self._set("QM", v),
                           docstring="QM : 0 aucun, 1 inconnu, 2 Tiny, 3 Standard. Mis à jour au mouvement si ZZ=0.")
        self.add_parameter("units", vals=Ints(0, 1), get_cmd=lambda: self._get_int("SN?"),
                           set_cmd=lambda v: self._set("SN", v),
                           docstring="SN : 1 = comptes codeur (défaut), 0 = pas (boucle ouverte seulement).")
        self.add_parameter("position", unit="count", get_cmd=self._get_position,
                           docstring="TP? : comptes codeur si SN=1, pas émis si SN=0. L'unité du paramètre suit SN.")
        self.add_parameter("is_moving", get_cmd=lambda: self._get_int("MD?") == 0,
                           docstring="MD? : 0 = en mouvement, 1 = arrêté.")
        self.add_parameter("closed_loop", vals=Ints(0, 1), get_cmd=lambda: self._get_int("MM?"),
                           set_cmd=self._set_closed_loop,
                           docstring="MM : 1 = boucle fermée. Exige SN=1 et allow_motion=True pour l'activer.")
        self.add_parameter("update_interval", unit="s", vals=Numbers(0.1, 100000), get_cmd=lambda: self._get_float("CL?"),
                           set_cmd=lambda v: self._set("CL", v),
                           docstring="CL : intervalle de correction, 0.1 à 100000 s. Le contrôleur répond en décimal (0.1000).")
        self.add_parameter("deadband", unit="count", vals=Ints(0, INT32[1]), get_cmd=lambda: self._get_int("DB?"),
                           set_cmd=lambda v: self._set("DB", v), docstring="DB : bande morte en comptes.")
        self.add_parameter("following_error", unit="count", vals=Ints(0, INT32[1]),
                           get_cmd=lambda: self._get_int("FE?"), set_cmd=lambda v: self._set("FE", v),
                           docstring="FE : seuil d'erreur de suivi en comptes (actif si ZH bit 1 = 0).")
        self.add_parameter("hardware_config", get_cmd=lambda: self._get_int("ZH?"),
                           docstring="ZH, lecture seule. Bit 0 limites matérielles coupées, bit 1 suivi coupé, "
                                     "bit 2 codeur quasi-absolu présent, bit 3 limites logicielles actives.")
        self.add_parameter("absolute_search_mode", vals=Ints(0, 2), get_cmd=lambda: self._get_int("AD?"),
                           set_cmd=lambda v: self._set("AD", int(v)),
                           docstring="AD : mouvement final de la recherche d'absolu AF. 0 aucun (défaut), 1 retour à la position "
                                     "de départ, 2 déplacement vers le zéro absolu.")
        self.add_parameter("absolute_found", get_cmd=lambda: self._get_int("OF?") == 1,
                           docstring="OF? : la position absolue a été trouvée depuis le reset.")
        self.add_parameter("absolute_search_done", get_cmd=lambda: self._get_int("AF?") == 1,
                           docstring="AF? : 0 recherche en cours, 1 terminée.")

    # -- bas niveau --
    def _cmd(self, suffixe: str) -> str:
        return f"{self.axis}{suffixe}"

    def _get_int(self, suffixe: str) -> int:
        return int(self.parent.ask(self._cmd(suffixe)))

    def _get_float(self, suffixe: str) -> float:
        return float(self.parent.ask(self._cmd(suffixe)))

    def _set(self, mnemonique: str, valeur) -> None:
        self.parent.write_checked(self._cmd(f"{mnemonique}{valeur}"))

    def _get_position(self) -> int:
        valeur = self._get_int("TP?")
        self.position.unit = "count" if self._get_int("SN?") == UNITE_COMPTES else "step"
        return valeur

    def _set_velocity(self, valeur: int) -> None:
        if valeur > VA_MAX_TINY and self._get_int("QM?") == MOTOR_TINY:
            raise Newport8742Error(f"Vitesse {valeur} > {VA_MAX_TINY} pas/s, maximum d'un moteur Tiny.")
        self._set("VA", int(valeur))

    def _set_closed_loop(self, valeur: int) -> None:
        if valeur == 1:
            self._exiger_mouvement_permis()
            if self._get_int("SN?") != UNITE_COMPTES:
                raise Newport8742Error("Boucle fermée refusée : SN doit valoir 1 (comptes codeur).")
        self._set("MM", int(valeur))

    def _exiger_mouvement_permis(self) -> None:
        if not self.parent.allow_motion:
            raise Newport8742Error("Mouvement refusé : construire l'instrument avec allow_motion=True.")

    def _autoriser_mouvement(self) -> None:
        self._exiger_mouvement_permis()
        qm = self._get_int("QM?")
        if qm not in (MOTOR_TINY, MOTOR_STANDARD):
            auto = (int(self.parent.ask("ZZ?")) & 1) == 0
            if not auto:
                raise Newport8742Error(
                    f"QM={qm} sur l'axe {self.axis} et détection automatique coupée (ZZ bit 0 = 1) : "
                    "définir motor_type à 2 ou 3, ou remettre ZZ à 0.")

    def _borner(self, comptes: int, depuis: int) -> int:
        comptes = int(comptes)
        if not INT32[0] <= comptes <= INT32[1]:
            raise Newport8742Error(f"{comptes} hors de l'entier 32 bits {INT32}.")
        if abs(comptes - depuis) > self.parent.max_move:
            raise Newport8742Error(
                f"Déplacement de {abs(comptes - depuis)} > max_move={self.parent.max_move} (construire avec un max_move plus grand).")
        return comptes

    # -- mouvement --
    def move_relative(self, counts: int, verifier_erreurs: bool = True) -> None:
        """PR : déplacement relatif (comptes si SN=1), retour immédiat.
        verifier_erreurs=False n'attend pas la lecture de la file d'erreurs (environ 1 s) : l'appelant doit
        appeler parent.drain_errors() lui-même. Sert à suivre MD? pendant le mouvement."""
        self._autoriser_mouvement()
        cmd = self._cmd(f"PR{self._borner(counts, 0)}")
        if verifier_erreurs:
            self.parent.write_checked(cmd)
        else:
            self.parent._transport.write(cmd)

    def move_absolute(self, counts: int) -> None:
        """PA : déplacement vers la position absolue (référence DH). Distance limitée à max_move depuis TP?."""
        self._autoriser_mouvement()
        self.parent.write_checked(self._cmd(f"PA{self._borner(counts, self._get_int('TP?'))}"))

    def find_absolute(self) -> None:
        """AF : recherche de la position absolue, DÉPLACE l'axe. Exige ZH bit 2 et SN=1 (sinon erreur x36)."""
        self._autoriser_mouvement()
        if not self._get_int("ZH?") & ZH_BIT_QUASI_ABSOLUTE:
            raise Newport8742Error("AF refusée : ZH bit 2 = 0, pas de codeur quasi-absolu déclaré sur cet axe.")
        if self._get_int("SN?") != UNITE_COMPTES:
            raise Newport8742Error("AF refusée : SN doit valoir 1 (comptes codeur).")
        self.parent.write_checked(self._cmd("AF"))

    def stop(self) -> None:
        """ST : arrêt avec décélération. Toujours permis."""
        self.parent.write_checked(self._cmd("ST"))

    def set_origin(self, counts: int = 0) -> None:
        """DH : la position courante devient `counts`. Ne bouge pas l'axe."""
        self.parent.write_checked(self._cmd(f"DH{int(counts)}"))


class Newport8743(Instrument):
    """Newport 8743-CL. `transport` expose write(cmd), ask(cmd) et close() ; par défaut l'USB défensif."""

    def __init__(self, name: str, transport=None, allow_motion: bool = False, max_move: int = 1000,
                 axes: tuple[int, ...] = (1, 2), **kwargs):
        super().__init__(name, **kwargs)
        if transport is None:
            from newport_usb import UsbTransport
            transport = UsbTransport(defensive=True, match="8743")
        self._transport = transport
        self.allow_motion = allow_motion
        self.max_move = int(max_move)
        for a in axes:
            self.add_submodule(f"axis{a}", Newport8743Axis(self, f"axis{a}", a))
        self.connect_message()

    # -- communication --
    def ask(self, cmd: str) -> str:
        return self._transport.ask(cmd)

    def write_checked(self, cmd: str) -> None:
        self._transport.write(cmd)
        erreurs = self.drain_errors()
        if erreurs:
            raise Newport8742Error(f"{cmd!r} : {'; '.join(erreurs)}")

    def drain_errors(self) -> list[str]:
        erreurs = []
        for _ in range(11):
            rep = self._transport.ask("TB?")
            if rep.split(",")[0].strip() in ("0", ""):
                break
            erreurs.append(rep)
        return erreurs

    # -- instrument --
    def get_idn(self) -> dict:
        """*IDN? du 8743-CL v4.06 : 'New_Focus 8743-CL v4.06 01/19/17 13097' (pas de virgule ni de SN)."""
        rep = self._transport.ask("*IDN?")
        m = re.match(r"^(\S+)\s+(\S+)\s+v?(\S+)\s+\S+(?:,?\s*(?:SN)?(\S+))?$", rep)
        if not m:
            return {"vendor": None, "model": rep, "serial": None, "firmware": None}
        return {"vendor": m.group(1), "model": m.group(2), "firmware": m.group(3), "serial": m.group(4)}

    def hardware_status(self) -> int:
        """PH? : bits 0 à 2 axe 1 (limite +, limite -, index), bits 3 à 5 axe 2. 63 sans positionneur."""
        return int(self.ask("PH?"))

    def save_to_memory(self) -> None:
        """SM : sauve ZZ, QM, VA, AC, CL, DB, FE, SN, ZH pour tous les axes."""
        self.write_checked("SM")

    def abort(self) -> None:
        """AB : arrêt immédiat de tous les axes. Toujours permis."""
        self.write_checked("AB")

    def close(self) -> None:
        try:
            self._transport.close()
        finally:
            super().close()
