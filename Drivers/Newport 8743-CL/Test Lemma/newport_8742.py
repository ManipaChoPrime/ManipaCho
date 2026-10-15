# -*- coding: utf-8 -*-
"""Driver QCoDeS du contrôleur Newport 8742 (4 axes, boucle ouverte), USB.

Règles de sûreté :
  * Aucun mouvement sans allow_motion=True à la construction.
  * Aucun mouvement tant que le type de moteur (QM) n'est pas 2 (Tiny) ou 3 (Standard).
  * VA (1 à 2000 pas/s, 1750 pour un Tiny) et AC (1 à 200000 pas/s²) sont validés par le driver :
    le contrôleur réel accepte VA0 et AC0 sans erreur (mesuré 2026-10-14).
  * Après chaque écriture, la file d'erreurs (TB?) est lue ; une erreur lève Newport8742Error.
Références : docs/protocol_8742.md (pages du manuel et mesures).
"""
from __future__ import annotations

import re
from typing import Optional

from qcodes.instrument import Instrument, InstrumentChannel
from qcodes.validators import Ints

VA_MIN, VA_MAX, VA_MAX_TINY = 1, 2000, 1750
AC_MIN, AC_MAX = 1, 200000
INT32 = (-2147483648, 2147483647)
MOTOR_NONE, MOTOR_UNKNOWN, MOTOR_TINY, MOTOR_STANDARD = 0, 1, 2, 3


class Newport8742Error(RuntimeError):
    """Erreur renvoyée par le contrôleur (TB?) ou refus du driver."""


class Newport8742Axis(InstrumentChannel):
    def __init__(self, parent: "Newport8742", name: str, axis: int):
        super().__init__(parent, name)
        self.axis = axis
        self.add_parameter("velocity", unit="step/s", vals=Ints(VA_MIN, VA_MAX),
                           get_cmd=lambda: self._get_int("VA?"), set_cmd=self._set_velocity,
                           docstring="VA : vitesse, 1 à 2000 pas/s (1750 pour un moteur Tiny).")
        self.add_parameter("acceleration", unit="step/s^2", vals=Ints(AC_MIN, AC_MAX),
                           get_cmd=lambda: self._get_int("AC?"), set_cmd=lambda v: self._set("AC", v),
                           docstring="AC : accélération, 1 à 200000 pas/s².")
        self.add_parameter("motor_type", vals=Ints(0, 3),
                           get_cmd=lambda: self._get_int("QM?"), set_cmd=lambda v: self._set("QM", v),
                           docstring="QM : 0 aucun, 1 inconnu, 2 Tiny, 3 Standard. Valeur en mémoire, "
                                     "non sauvée tant que save_to_memory() n'est pas appelée.")
        self.add_parameter("position", unit="step", get_cmd=lambda: self._get_int("TP?"),
                           docstring="TP? : pas émis depuis la mise sous tension ou le dernier DH. "
                                     "Ce n'est pas une mesure de la position physique.")
        self.add_parameter("is_moving", get_cmd=self._get_is_moving,
                           docstring="MD? : 0 = en mouvement, 1 = arrêté (manuel rév. D, non mesuré).")

    # -- bas niveau --
    def _cmd(self, suffixe: str) -> str:
        return f"{self.axis}{suffixe}"

    def _get_int(self, suffixe: str) -> int:
        return int(self.parent.ask(self._cmd(suffixe)))

    def _get_is_moving(self) -> bool:
        return self._get_int("MD?") == 0

    def _set(self, mnemonique: str, valeur: int) -> None:
        self.parent.write_checked(self._cmd(f"{mnemonique}{int(valeur)}"))

    def _set_velocity(self, valeur: int) -> None:
        if valeur > VA_MAX_TINY and self.motor_type() == MOTOR_TINY:
            raise Newport8742Error(f"Vitesse {valeur} > {VA_MAX_TINY} pas/s, maximum d'un moteur Tiny.")
        self._set("VA", valeur)

    def _autoriser_mouvement(self) -> None:
        if not self.parent.allow_motion:
            raise Newport8742Error("Mouvement refusé : construire l'instrument avec allow_motion=True.")
        qm = self.motor_type()
        if qm not in (MOTOR_TINY, MOTOR_STANDARD):
            raise Newport8742Error(
                f"Type de moteur QM={qm} sur l'axe {self.axis}. Définir motor_type à 2 (Tiny) ou 3 "
                "(Standard) ; avec la détection automatique (ZZ=0), un mouvement la met à jour.")

    @staticmethod
    def _int32(valeur: int) -> int:
        if not INT32[0] <= valeur <= INT32[1]:
            raise Newport8742Error(f"{valeur} hors de l'entier 32 bits {INT32}.")
        return int(valeur)

    # -- mouvement --
    def move_relative(self, steps: int) -> None:
        """PR : déplacement relatif en pas, retour immédiat (le mouvement continue dans le contrôleur)."""
        self._autoriser_mouvement()
        self.parent.write_checked(self._cmd(f"PR{self._int32(steps)}"))

    def move_absolute(self, steps: int) -> None:
        """PA : déplacement vers la position absolue (référence DH), en pas."""
        self._autoriser_mouvement()
        self.parent.write_checked(self._cmd(f"PA{self._int32(steps)}"))

    def stop(self) -> None:
        """ST : arrêt avec décélération (AC). Toujours permis."""
        self.parent.write_checked(self._cmd("ST"))

    def set_origin(self, steps: int = 0) -> None:
        """DH : définit la position courante comme `steps`. Ne bouge pas l'axe."""
        self.parent.write_checked(self._cmd(f"DH{self._int32(steps)}"))


class Newport8742(Instrument):
    """Newport 8742. `transport` expose write(cmd), ask(cmd) et close() ; par défaut l'USB."""

    def __init__(self, name: str, transport=None, allow_motion: bool = False,
                 axes: tuple[int, ...] = (1, 2, 3, 4), **kwargs):
        super().__init__(name, **kwargs)
        if transport is None:
            from newport_usb import UsbTransport
            transport = UsbTransport()
        self._transport = transport
        self.allow_motion = allow_motion
        for a in axes:
            self.add_submodule(f"axis{a}", Newport8742Axis(self, f"axis{a}", a))
        self.connect_message()

    # -- communication --
    def ask(self, cmd: str) -> str:
        return self._transport.ask(cmd)

    def write_checked(self, cmd: str) -> None:
        """Écrit puis lit la file d'erreurs ; lève Newport8742Error s'il y en a."""
        self._transport.write(cmd)
        erreurs = self.drain_errors()
        if erreurs:
            raise Newport8742Error(f"{cmd!r} : {'; '.join(erreurs)}")

    def drain_errors(self) -> list[str]:
        """Vide la file d'erreurs (10 entrées au plus) avec TB?."""
        erreurs = []
        for _ in range(11):
            rep = self._transport.ask("TB?")
            if rep.split(",")[0].strip() in ("0", ""):
                break
            erreurs.append(rep)
        return erreurs

    # -- instrument --
    def get_idn(self) -> dict:
        """*IDN? du 8742 v3.04 : 'New_Focus 8742 v3.04 09/09/16 108042' (pas de virgule ni de SN)."""
        rep = self._transport.ask("*IDN?")
        m = re.match(r"^(\S+)\s+(\S+)\s+v?(\S+)\s+\S+(?:,?\s*(?:SN)?(\S+))?$", rep)
        if not m:
            return {"vendor": None, "model": rep, "serial": None, "firmware": None}
        return {"vendor": m.group(1), "model": m.group(2), "firmware": m.group(3), "serial": m.group(4)}

    def save_to_memory(self) -> None:
        """SM : sauve ZZ, QM, VA, AC de tous les axes en mémoire non volatile."""
        self.write_checked("SM")

    def abort(self) -> None:
        """AB : arrêt immédiat de tous les axes, sans décélération. Toujours permis."""
        self.write_checked("AB")

    def close(self) -> None:
        try:
            self._transport.close()
        finally:
            super().close()
