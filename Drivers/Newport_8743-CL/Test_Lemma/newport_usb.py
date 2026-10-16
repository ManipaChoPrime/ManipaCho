# -*- coding: utf-8 -*-
"""Transport USB pour les contrôleurs Newport 8742 et 8743-CL, via usbdll.dll (ctypes).

Réutilise le chargement de detect_usb.py. Le pilote ajoute lui-même le CR à la commande,
et les réponses se terminent par CR LF (mesuré le 2026-10-14 sur un 8742 v3.04).

Interface minimale attendue par le driver : write(cmd), ask(cmd) -> str, close().
"""
from __future__ import annotations

import time
from ctypes import byref, c_ulong, create_string_buffer

from detect_usb import (
    CHEMIN_DLL_DEFAUT, PRODUCT_ID_DEFAUT, TAILLE_TAMPON,
    ErreurDetection, charger_dll, declarer_signatures, lire_infos, ouvrir, verifier_code,
)

PAUSE_S = 0.15  # attente entre envoi et lecture, comme dans probe_8742.py


class UsbTransport:
    """Une connexion USB à un contrôleur. Un seul programme à la fois peut l'ouvrir."""

    def __init__(self, dll_path: str = CHEMIN_DLL_DEFAUT, product_id: int = PRODUCT_ID_DEFAUT,
                 index: int = 0, pause_s: float = PAUSE_S, defensive: bool = False,
                 match: str | None = None, poll_max_s: float = 2.0, poll_step_s: float = 0.1):
        """defensive=True : vide les réponses orphelines avant une requête, relit jusqu'à poll_max_s si la
        réponse tarde, et relit la liste des contrôleurs si une réponse parasite la remplace (décalage vu
        sur le 8743-CL le 2026-10-15). match="8743" choisit le contrôleur dont la description contient ce texte."""
        self.pause_s = pause_s
        self.defensive, self.poll_max_s, self.poll_step_s = defensive, poll_max_s, poll_step_s
        self.orphelines: list[str] = []
        self.tardives: list[str] = []
        self._vider_requis = True   # vider avant la première requête, puis après chaque écriture
        self._dll = charger_dll(dll_path)
        declarer_signatures(self._dll)
        self._open = False
        nombre = ouvrir(self._dll, product_id)
        self._open = True
        try:
            if nombre == 0:
                raise ErreurDetection("Aucun périphérique trouvé : lancez detect_usb.py.")
            infos = lire_infos(self._dll)
            for _ in range(10 if defensive else 0):
                if any("New_Focus" in d for _, d in infos):
                    break
                self.orphelines.append(f"liste : {infos}")
                infos = lire_infos(self._dll)
            if match is not None:
                trouves = [i for i in infos if match in i[1]]
                if len(trouves) != 1:
                    raise ErreurDetection(f"{len(trouves)} contrôleur(s) contenant {match!r} dans {infos}")
                self.device_id, self.description = trouves[0]
            else:
                if index >= len(infos):
                    raise ErreurDetection(f"Indice {index} hors liste : {infos}")
                self.device_id, self.description = infos[index]
        except Exception:
            self.close()
            raise

    def write(self, commande: str) -> None:
        self._vider_requis = True        # une écriture peut produire une réponse inattendue
        brut = commande.encode("ascii")
        code = self._dll.newp_usb_send_ascii(self.device_id, brut, len(brut))
        verifier_code(code, f"L'envoi de « {commande} »", "Vérifiez l'alimentation et le câble USB.")

    def ask(self, commande: str) -> str:
        """Envoie une requête (qui finit par '?') et renvoie la réponse sans CR LF."""
        if self.defensive:
            return self._ask_defensif(commande)
        self.write(commande)
        time.sleep(self.pause_s)
        code, brut = self._lire_une_fois()
        verifier_code(code, f"La lecture de la réponse à « {commande} »",
                      "La commande n'est peut-être pas une requête.")
        return brut.decode("ascii", errors="replace").strip("\r\n\0 ")

    def eviter_vidage(self) -> None:
        """Saute le vidage avant la prochaine requête (il coûte une lecture à vide, environ 1 s). À n'utiliser
        qu'après une écriture dont on sait qu'elle ne produit pas de réponse, par exemple PR."""
        self._vider_requis = False

    def _lire_une_fois(self) -> tuple[int, bytes]:
        tampon = create_string_buffer(TAILLE_TAMPON)
        nb = c_ulong(0)
        code = self._dll.newp_usb_get_ascii(self.device_id, tampon, TAILLE_TAMPON, byref(nb))
        return code, tampon.raw[: nb.value]

    def _ask_defensif(self, commande: str) -> str:
        if self._vider_requis:                    # coûte une lecture à vide : seulement au démarrage et après une écriture
            for _ in range(20):
                code, brut = self._lire_une_fois()
                if code != 0 or not brut:
                    break
                self.orphelines.append(f"avant {commande} : {brut!r}")
        self.write(commande)
        self._vider_requis = False                # la réponse attendue est lue plus bas : file synchrone
        t0 = time.monotonic()
        time.sleep(self.pause_s)
        while True:
            code, brut = self._lire_une_fois()
            if code == 0 and brut:
                break
            if time.monotonic() - t0 > self.poll_max_s:
                raise RuntimeError(f"Pas de réponse à « {commande} » après {self.poll_max_s} s.")
            time.sleep(self.poll_step_s)
        if time.monotonic() - t0 > self.pause_s + 0.05:
            self.tardives.append(f"{commande} : {time.monotonic() - t0:.2f} s")
        return brut.decode("ascii", errors="replace").strip("\r\n\0 ")

    def close(self) -> None:
        if self._open:
            self._dll.newp_usb_uninit_system()  # libère le contrôleur pour les autres programmes
            self._open = False
