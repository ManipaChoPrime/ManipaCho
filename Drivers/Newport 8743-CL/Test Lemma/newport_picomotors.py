# -*- coding: utf-8 -*-
"""newport_picomotors.py : pilotes QCoDeS des contrôleurs Newport 8742 (4 axes, boucle ouverte) et 8743-CL (2 axes,
boucle fermée) en USB sous Windows, dans un seul fichier. Fichier GÉNÉRÉ par build_single_file.py le 2026-10-15 15:15 :
ne pas le modifier à la main.

Installation sur un autre PC :
  1. Windows, Python 64 bits (3.10 ou plus) ; le pilote Newport USB installé (usbdll.dll, voir CHEMIN_DLL_DEFAUT ou la
     variable d'environnement NEWPORT_USBDLL) ; l'application Picomotor de Newport fermée (un seul programme à la fois).
  2. pip install qcodes
  3. Copier ce fichier à côté du notebook, puis le vérifier :  python newport_picomotors.py --check

Dans un notebook :
    from newport_picomotors import connect_8743
    pico = connect_8743("pico", allow_motion=True)      # allow_motion=False : lectures seulement
    ax = pico.axis1
    ax.set_reference()          # une fois par démarrage du contrôleur, sur ta référence physique
    ax.mark("A"); ax.move(500, speed="lent", unit="um"); ax.mark("B")
    ax.goto("A"); ax.goto("B"); ax.where()
Voir docs/protocol_8743.md pour les mesures, les limites et les règles de sûreté.
"""
from __future__ import annotations


# ====================================================================================================
# Module detect_usb.py
# ====================================================================================================
# -*- coding: utf-8 -*-
"""Détection des contrôleurs Newport 8742 / 8743-CL en USB, par ctypes.

STATUT : NON EXÉCUTÉ. Ce script n'a jamais tourné sur matériel. Il est
compilé (python -m py_compile) mais son comportement réel dépend de la sortie
que vous renverrez.

Il charge usbdll.dll (pilote Newport 64 bits) et utilise l'interface native
décrite dans « Newport USB Driver API User's Manual », pages 1 à 5 (NewpDll.h).
Il n'utilise pas UsbDllWrap.dll ni pythonnet.

Usage (PowerShell, environnement virtuel actif) :
    python detect_usb.py
    python detect_usb.py --dll "C:\\Program Files (x86)\\Newport\\Newport USB Driver\\Bin\\x64\\usbdll.dll"
    python detect_usb.py --produit 0x4000 --rapport rapport_usb.txt

Fermez l'application Picomotor (et TestUsb.exe) avant de lancer le script :
un seul programme à la fois peut ouvrir le contrôleur.
"""

import argparse
import ctypes
import os
import struct
import sys
import time
from ctypes import c_bool, c_char_p, c_int, c_long, c_ulong, POINTER, byref, create_string_buffer
from datetime import datetime

# --- Paramètres configurables -------------------------------------------------
# Variable d'environnement NEWPORT_USBDLL ou option --dll pour changer le chemin.
CHEMIN_DLL_DEFAUT = (
    r"C:\Program Files (x86)\Newport\Newport USB Driver\Bin\x64\usbdll.dll"
)
PRODUCT_ID_DEFAUT = 0x4000   # identifiant de produit des contrôleurs Picomotor
TAILLE_TAMPON = 4096         # octets réservés aux réponses
PAUSE_LECTURE_S = 0.1        # attente entre envoi et lecture
NB_ERREURS_MAX = 10          # la file d'erreurs du contrôleur garde 10 entrées


class ErreurDetection(Exception):
    """Erreur prévisible : le message est déjà en français, avec l'action à faire."""


# --- Chargement de la DLL -----------------------------------------------------
def machine_pe(chemin: str) -> str:
    """Lit l'architecture d'une DLL dans son en-tête PE ('x64', 'x86' ou 'inconnue')."""
    with open(chemin, "rb") as f:
        f.seek(0x3C)
        (offset,) = struct.unpack("<I", f.read(4))
        f.seek(offset)
        if f.read(4) != b"PE\0\0":
            return "inconnue"
        (machine,) = struct.unpack("<H", f.read(2))
    return {0x8664: "x64", 0x014C: "x86"}.get(machine, f"inconnue (0x{machine:04X})")


def charger_dll(chemin: str) -> ctypes.CDLL:
    """Charge usbdll.dll après avoir vérifié le système, les bits de Python et ceux de la DLL."""
    if os.name != "nt":
        raise ErreurDetection(
            "Ce script ne fonctionne que sous Windows (le pilote Newport est une DLL Windows). "
            "Action : lancez-le dans PowerShell sur le PC où le pilote est installé."
        )
    bits_python = struct.calcsize("P") * 8
    if not os.path.isfile(chemin):
        raise ErreurDetection(
            f"DLL introuvable : {chemin}\n"
            "Action : vérifiez que le Newport USB Driver est installé et que le dossier existe. "
            "Dans l'Explorateur, ouvrez C:\\Program Files (x86)\\Newport\\Newport USB Driver\\Bin\\x64, "
            "puis relancez avec --dll \"<chemin complet de usbdll.dll>\"."
        )
    bits_dll = machine_pe(chemin)
    attendu = "x64" if bits_python == 64 else "x86"
    if bits_dll != attendu:
        raise ErreurDetection(
            f"Bits incompatibles : Python {bits_python} bits, mais la DLL est {bits_dll} ({chemin}).\n"
            "Action : utilisez la DLL du dossier Bin\\x64 avec un Python 64 bits, "
            "ou la DLL du dossier Bin (32 bits) avec un Python 32 bits. "
            "Vérifiez avec : python -c \"import struct; print(struct.calcsize('P')*8)\"."
        )
    try:
        # Les DLL dont dépend usbdll.dll sont cherchées dans son dossier.
        os.add_dll_directory(os.path.dirname(chemin))
        return ctypes.CDLL(chemin)
    except OSError as exc:
        raise ErreurDetection(
            f"Windows refuse de charger la DLL ({exc}).\n"
            "Action : réinstallez le Newport USB Driver (version x64), "
            "puis installez le « Microsoft Visual C++ Redistributable » 64 bits si le message persiste."
        ) from exc


def declarer_signatures(dll: ctypes.CDLL) -> None:
    """Signatures ctypes, d'après NewpDll.h (manuel de l'API, p. 1 à 5).

    Sous Windows, `long` fait 32 bits : c_long de ctypes (32 bits sous Windows) convient.
    `bool` du C++ occupe 1 octet : c_bool. `char*` : c_char_p ou tampon.
    Le manuel ne précise pas la convention d'appel ; en 64 bits il n'y en a qu'une.
    """
    # long newp_usb_init_product (int nProductID);                          [p. 1]
    dll.newp_usb_init_product.argtypes = [c_int]
    dll.newp_usb_init_product.restype = c_long

    # long newp_usb_open_devices (int nProductID, bool bUseUSBAddress, int* nNumDevices);  [p. 1]
    dll.newp_usb_open_devices.argtypes = [c_int, c_bool, POINTER(c_int)]
    dll.newp_usb_open_devices.restype = c_long

    # void newp_usb_uninit_system (void);                                   [p. 1]
    dll.newp_usb_uninit_system.argtypes = []
    dll.newp_usb_uninit_system.restype = None

    # long newp_usb_get_device_info (char* Buffer);                         [p. 3]
    dll.newp_usb_get_device_info.argtypes = [c_char_p]
    dll.newp_usb_get_device_info.restype = c_long

    # long newp_usb_get_ascii (long DeviceID, char* Buffer, unsigned long Length,
    #                          unsigned long* BytesRead);                   [p. 4]
    dll.newp_usb_get_ascii.argtypes = [c_long, c_char_p, c_ulong, POINTER(c_ulong)]
    dll.newp_usb_get_ascii.restype = c_long

    # long newp_usb_send_ascii (long DeviceID, char* Command, unsigned long Length);  [p. 4]
    dll.newp_usb_send_ascii.argtypes = [c_long, c_char_p, c_ulong]
    dll.newp_usb_send_ascii.restype = c_long


# --- Aides d'appel ------------------------------------------------------------
def verifier_code(code: int, action: str, conseil: str) -> None:
    """Lève une erreur française si le code de retour du pilote est non nul."""
    if code != 0:
        raise ErreurDetection(
            f"{action} a échoué (code de retour {code}, 0 = succès).\n{conseil}"
        )


def ouvrir(dll: ctypes.CDLL, product_id: int, utiliser_adresse: bool = True) -> int:
    """Ouvre les périphériques du produit demandé. Retourne le nombre ouvert."""
    n = c_int(0)
    # newp_usb_open_devices fixe le mode d'adressage et renvoie le nombre de périphériques.
    code = dll.newp_usb_open_devices(product_id, utiliser_adresse, byref(n))
    verifier_code(
        code,
        f"L'ouverture des périphériques (produit 0x{product_id:04X})",
        "Actions : (1) fermez l'application Picomotor, TestUsb.exe et tout autre programme "
        "qui utilise le contrôleur (un seul programme peut l'ouvrir à la fois) ; "
        "(2) débranchez puis rebranchez le câble USB, contrôleur sous tension ; "
        "(3) vérifiez dans le Gestionnaire de périphériques que le contrôleur est listé "
        "sans point d'exclamation ; (4) relancez ce script.",
    )
    return n.value


def lire_infos(dll: ctypes.CDLL) -> list[tuple[int, str]]:
    """Retourne [(DeviceID, description *IDN?)], format '<id>,<desc>;<id>,<desc>;'."""
    tampon = create_string_buffer(TAILLE_TAMPON)
    code = dll.newp_usb_get_device_info(tampon)
    verifier_code(
        code,
        "La lecture de la liste des périphériques",
        "Action : relancez le script ; si l'échec persiste, débranchez et rebranchez le contrôleur.",
    )
    texte = tampon.value.decode("ascii", errors="replace")
    resultat = []
    for bloc in texte.split(";"):
        bloc = bloc.strip()
        if not bloc:
            continue
        ident, _, desc = bloc.partition(",")  # la description contient d'autres virgules
        try:
            resultat.append((int(ident.strip()), desc.strip()))
        except ValueError:
            raise ErreurDetection(
                f"Réponse inattendue de newp_usb_get_device_info : {texte!r}\n"
                "Action : copiez cette ligne dans votre retour, elle permet d'adapter l'analyse."
            )
    return resultat


def envoyer(dll: ctypes.CDLL, dev_id: int, commande: str) -> None:
    """Envoie une commande ASCII. Le pilote ajoute lui-même le retour chariot : on n'en met pas."""
    brut = commande.encode("ascii")
    code = dll.newp_usb_send_ascii(dev_id, brut, len(brut))
    verifier_code(
        code,
        f"L'envoi de « {commande} » au périphérique {dev_id}",
        "Actions : vérifiez que le contrôleur est sous tension et que le câble USB est branché ; "
        "fermez l'application Picomotor si elle est ouverte ; relancez le script.",
    )


def lire(dll: ctypes.CDLL, dev_id: int, commande: str) -> str:
    """Lit la réponse ASCII. get_ascii ne coupe pas au retour chariot : on le retire ici."""
    tampon = create_string_buffer(TAILLE_TAMPON)
    nb = c_ulong(0)
    code = dll.newp_usb_get_ascii(dev_id, tampon, TAILLE_TAMPON, byref(nb))
    verifier_code(
        code,
        f"La lecture de la réponse à « {commande} » (périphérique {dev_id})",
        "Actions : la commande n'est peut-être pas une requête (elle doit finir par « ? ») ; "
        "sinon vérifiez l'alimentation du contrôleur et le câble USB, puis relancez.",
    )
    return tampon.raw[: nb.value].decode("ascii", errors="replace").strip("\r\n\0 ")


def interroger(dll: ctypes.CDLL, dev_id: int, commande: str) -> str:
    """Envoie une requête puis lit sa réponse."""
    envoyer(dll, dev_id, commande)
    time.sleep(PAUSE_LECTURE_S)
    return lire(dll, dev_id, commande)


def lire_erreurs(dll: ctypes.CDLL, dev_id: int) -> list[str]:
    """Vide la file d'erreurs avec TB? (« code, MESSAGE ») jusqu'au code 0."""
    erreurs = []
    for _ in range(NB_ERREURS_MAX):
        rep = interroger(dll, dev_id, "TB?")
        code_txt = rep.split(",")[0].strip()
        if code_txt == "0":
            break
        erreurs.append(rep)
    return erreurs


# --- Programme principal ------------------------------------------------------
def executer(args: argparse.Namespace, rapport: list[str]) -> int:
    def note(ligne: str = "") -> None:
        print(ligne)
        rapport.append(ligne)

    note(f"Rapport detect_usb.py, {datetime.now():%Y-%m-%d %H:%M:%S}")
    note("STATUT : script non exécuté avant ce rapport ; les lignes ci-dessous sont la sortie réelle.")
    note(f"Python {sys.version.split()[0]}, {struct.calcsize('P') * 8} bits")
    note(f"DLL : {args.dll}")

    dll = charger_dll(args.dll)
    note(f"DLL chargée, architecture {machine_pe(args.dll)}")
    declarer_signatures(dll)

    ouverte = False
    try:
        nombre = ouvrir(dll, args.produit)
        ouverte = True
        note(f"Produit 0x{args.produit:04X} : {nombre} périphérique(s) ouvert(s)")
        if nombre == 0:
            raise ErreurDetection(
                "Aucun périphérique trouvé.\n"
                "Actions : (1) vérifiez que le contrôleur est sous tension et branché en USB ; "
                "(2) dans le Gestionnaire de périphériques, cherchez le contrôleur sous "
                "« Newport USB Devices » (ou « Périphériques USB Newport ») ; "
                "(3) lancez TestUsb.exe avec le produit 0x4000 pour comparer ; "
                "(4) si l'application Picomotor est ouverte, fermez-la, puis relancez."
            )
        infos = lire_infos(dll)
        if not infos:
            raise ErreurDetection(
                "Des périphériques sont ouverts mais la liste est vide.\n"
                "Action : débranchez et rebranchez le contrôleur, puis relancez."
            )
        note(f"{len(infos)} contrôleur(s) listé(s) par newp_usb_get_device_info :")
        for dev_id, desc in infos:
            note(f"  DeviceID {dev_id} : {desc}")

        for dev_id, _ in infos:
            note()
            note(f"--- DeviceID {dev_id} ---")
            note(f"*IDN? -> {interroger(dll, dev_id, '*IDN?')}")
            erreurs = lire_erreurs(dll, dev_id)
            if erreurs:
                note("File d'erreurs (TB?) :")
                for e in erreurs:
                    note(f"  {e}")
            else:
                note("File d'erreurs (TB?) : vide (0)")
        note()
        note("Terminé sans erreur.")
        return 0
    finally:
        if ouverte:
            dll.newp_usb_uninit_system()  # libère le contrôleur pour les autres programmes


def main() -> int:
    parseur = argparse.ArgumentParser(description="Détection USB Newport 8742 / 8743-CL (ctypes).")
    parseur.add_argument("--dll", default=os.environ.get("NEWPORT_USBDLL", CHEMIN_DLL_DEFAUT),
                         help="chemin complet de usbdll.dll (défaut : dossier Bin\\x64)")
    parseur.add_argument("--produit", type=lambda s: int(s, 0), default=PRODUCT_ID_DEFAUT,
                         help="identifiant de produit, défaut 0x4000 (0 = tous)")
    parseur.add_argument("--rapport", default="rapport_usb.txt", help="fichier du rapport texte")
    args = parseur.parse_args()

    rapport: list[str] = []
    try:
        code = executer(args, rapport)
    except ErreurDetection as exc:
        print(f"\nERREUR : {exc}")
        rapport.append(f"ERREUR : {exc}")
        code = 1
    except Exception as exc:  # erreur imprévue : on garde la trace dans le rapport
        msg = (f"ERREUR imprévue ({type(exc).__name__}) : {exc}\n"
               "Action : envoyez ce rapport en entier pour qu'on adapte le script.")
        print(f"\n{msg}")
        rapport.append(msg)
        code = 2
    with open(args.rapport, "w", encoding="utf-8") as f:
        f.write("\n".join(rapport) + "\n")
    print(f"\nRapport écrit dans {os.path.abspath(args.rapport)}")
    return code


# ====================================================================================================
# Module newport_usb.py
# ====================================================================================================
# -*- coding: utf-8 -*-
"""Transport USB pour les contrôleurs Newport 8742 et 8743-CL, via usbdll.dll (ctypes).

Réutilise le chargement de detect_usb.py. Le pilote ajoute lui-même le CR à la commande,
et les réponses se terminent par CR LF (mesuré le 2026-10-14 sur un 8742 v3.04).

Interface minimale attendue par le driver : write(cmd), ask(cmd) -> str, close().
"""

import re
import time
from ctypes import byref, c_ulong, create_string_buffer


PAUSE_S = 0.15  # attente entre envoi et lecture, comme dans probe_8742.py
# Écritures dont on a mesuré qu'elles ne produisent jamais de réponse (0 réponse orpheline sur plusieurs centaines
# d'écritures, 2026-10-15) : elles ne déclenchent pas de vidage avant la requête suivante, qui coûte environ 1 s.
_ECRITURE_SILENCIEUSE = re.compile(r"^\d?(VA|AC|DB|MM|PA|PR|DH|ST|AB|QM|SN|CL|FE|AD)(-?[\d.]*)$")


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
        if not _ECRITURE_SILENCIEUSE.match(commande):
            self._vider_requis = True    # une écriture inconnue peut produire une réponse inattendue
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


# ====================================================================================================
# Module newport_8742.py
# ====================================================================================================
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


# ====================================================================================================
# Module newport_8743.py
# ====================================================================================================
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

import json
import os
import re
import time
from datetime import datetime

from qcodes.instrument import Instrument, InstrumentChannel
from qcodes.validators import Ints, Numbers


ZH_BIT_QUASI_ABSOLUTE = 4  # bit 2 de ZH
UNITE_COMPTES, UNITE_PAS = 1, 0

# --- fonctions de haut niveau (8311 : codeur incrémental, 49,6 nm par comptage, pas de fin de course) ---
UM_PAR_COMPTE = 0.0496            # fiche DS-102005 : 49,6 nm par comptage
SENTINELLE = 1_000_000            # valeur de TP donnée à la référence par set_reference() (DH)
REFERENCE_MIN, REFERENCE_MAX = 500_000, 1_500_000   # TP hors de cet intervalle : le contrôleur a redémarré
VITESSES = {"lent": 50, "normal": 500, "rapide": 1000}   # VA ; mesures : environ 1,5, 15 et 30 µm/s
COMPTES_PAR_S_PAR_VA = 0.6        # mesures du 2026-10-15 : 0,59 à 0,71 comptage/s par unité de VA
POLL_S = 0.15                     # intervalle de lecture de MD?


class Newport8743Axis(InstrumentChannel):
    def __init__(self, parent: "Newport8743", name: str, axis: int):
        super().__init__(parent, name)
        self.axis = axis
        self.add_parameter("velocity", unit="step/s", vals=Ints(VA_MIN, min(VA_MAX, parent.max_velocity)),
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

    # ------------------------------------------------------------------
    # Fonctions de haut niveau. Positions en comptes codeur ; 1 comptage = 49,6 nm (valeur nominale, non mesurée
    # indépendamment). TP vit dans le contrôleur : il est conservé tant que le 8743-CL reste allumé.
    # ------------------------------------------------------------------
    @staticmethod
    def _comptes(distance, unit: str) -> int:
        if unit == "counts":
            return int(round(distance))
        if unit == "um":
            return int(round(distance / UM_PAR_COMPTE))
        raise ValueError("unit doit valoir 'counts' ou 'um'.")

    def _vitesse(self, speed) -> int:
        if isinstance(speed, str):
            if speed not in VITESSES:
                raise ValueError(f"Vitesse {speed!r} inconnue : {sorted(VITESSES)} ou une valeur de VA.")
            va = VITESSES[speed]
        else:
            va = int(speed)
        if not 1 <= va <= self.parent.max_velocity:
            raise Newport8742Error(
                f"VA={va} hors de 1 à {self.parent.max_velocity} (max_velocity). Le 8311 est spécifié à environ 20 µm/s, "
                "soit VA de 500 à 700 ; VA=2000 donne environ 60 µm/s.")
        return va

    @staticmethod
    def _duree_max(comptes: int, va: int) -> float:
        return max(20.0, 3 * abs(comptes) / (COMPTES_PAR_S_PAR_VA * va) + 10)

    def _attendre_arret(self, timeout_s: float) -> float:
        """Attend MD? = 1 deux fois de suite. Sur dépassement du délai ou interruption (bouton Stop d'un notebook,
        Ctrl+C), envoie ST : sinon le contrôleur terminerait le mouvement sans que Python l'attende."""
        t0, calmes = time.monotonic(), 0
        try:
            while True:
                calmes = calmes + 1 if not self.is_moving() else 0
                if calmes >= 2:
                    return time.monotonic() - t0
                if time.monotonic() - t0 > timeout_s:
                    try:
                        self.stop()
                    finally:
                        raise Newport8742Error(f"Axe {self.axis} encore en mouvement après {timeout_s:.0f} s : ST envoyé.")
                time.sleep(POLL_S)
        except KeyboardInterrupt:
            try:
                self.stop()
            finally:
                raise

    # -- référence et positions mémorisées --
    @property
    def reference_valid(self) -> bool:
        """Vrai si TP est dans l'intervalle de la référence (set_reference() a été appelé depuis le dernier démarrage)."""
        return REFERENCE_MIN <= self._get_int("TP?") <= REFERENCE_MAX

    def _exiger_reference(self) -> int:
        tp = self._get_int("TP?")
        if not REFERENCE_MIN <= tp <= REFERENCE_MAX:
            raise Newport8742Error(
                f"Référence absente (TP={tp}) : le contrôleur a redémarré ou la référence n'a jamais été posée. "
                "Place l'axe sur ta référence physique puis appelle set_reference().")
        return tp

    def set_reference(self, counts: int = SENTINELLE, force: bool = False) -> None:
        """Définit la position courante comme référence (DH, sans mouvement). Refusé si une référence existe déjà,
        sauf force=True, car cela décale toutes les positions mémorisées."""
        if self.is_moving():
            raise Newport8742Error("set_reference refusé : l'axe est en mouvement.")
        if not REFERENCE_MIN + 100_000 <= counts <= REFERENCE_MAX - 100_000:
            raise Newport8742Error(f"counts={counts} hors de {REFERENCE_MIN + 100_000} à {REFERENCE_MAX - 100_000}.")
        if self.reference_valid and not force:
            raise Newport8742Error("Une référence existe déjà : set_reference(force=True) décalerait A, B et les limites.")
        self.set_origin(counts)
        if self._get_int("TP?") != counts:
            raise Newport8742Error("DH n'a pas fixé TP à la valeur demandée.")
        self.parent.store_ecrire(self.axis, "reference", {"counts": counts, "date": datetime.now().isoformat(timespec="seconds")})

    def positions(self) -> dict:
        """Positions mémorisées de cet axe : nom -> {counts, um_depuis_reference, date}."""
        return dict(self.parent.store_lire(self.axis).get("positions", {}))

    def mark(self, name: str) -> dict:
        """Mémorise la position courante sous `name` (en comptes, dans le fichier de positions)."""
        if not name or not isinstance(name, str):
            raise ValueError("Le nom doit être une chaîne non vide.")
        tp = self._exiger_reference()
        pos = {"counts": tp, "um_depuis_reference": round((tp - SENTINELLE) * UM_PAR_COMPTE, 3),
               "date": datetime.now().isoformat(timespec="seconds")}
        donnees = self.parent.store_lire(self.axis)
        donnees.setdefault("positions", {})[name] = pos
        self.parent.store_ecrire(self.axis, None, None, donnees)
        return pos

    def forget(self, name: str) -> None:
        donnees = self.parent.store_lire(self.axis)
        donnees.get("positions", {}).pop(name, None)
        self.parent.store_ecrire(self.axis, None, None, donnees)

    def set_limits(self, low_um: float | None, high_um: float | None) -> None:
        """Limites logicielles en µm depuis la référence (le 8311 n'a pas de fins de course). None pour aucune."""
        self._exiger_reference()
        lim = None if low_um is None or high_um is None else [SENTINELLE + self._comptes(low_um, "um"),
                                                              SENTINELLE + self._comptes(high_um, "um")]
        if lim and lim[0] >= lim[1]:
            raise ValueError("low_um doit être inférieur à high_um.")
        self.parent.store_ecrire(self.axis, "limites", lim)

    def _verifier_limites(self, cible: int) -> None:
        lim = self.parent.store_lire(self.axis).get("limites")
        if lim and not lim[0] <= cible <= lim[1]:
            raise Newport8742Error(
                f"Cible {cible} hors des limites logicielles {lim} ({(cible - SENTINELLE) * UM_PAR_COMPTE:+.0f} µm depuis la référence).")

    def where(self) -> dict:
        """État de l'axe : position en comptes, en µm depuis la référence, validité de la référence, noms proches."""
        tp = self._get_int("TP?")
        ok = REFERENCE_MIN <= tp <= REFERENCE_MAX
        proches = [n for n, p in self.positions().items() if abs(p["counts"] - tp) <= 5] if ok else []
        return {"counts": tp, "um_depuis_reference": round((tp - SENTINELLE) * UM_PAR_COMPTE, 2) if ok else None,
                "reference_valide": ok, "en_mouvement": self._get_int("MD?") == 0, "boucle_fermee": self._get_int("MM?"),
                "vitesse_VA": self._get_int("VA?"), "positions_proches": proches}

    # -- déplacements --
    def move(self, distance, speed="normal", unit: str = "counts", timeout_s: float | None = None) -> dict:
        """Déplacement relatif (PR) puis attente de l'arrêt. distance signée : positif = sens des TP croissants.
        speed : 'lent' (VA 50), 'normal' (500), 'rapide' (1000) ou une valeur de VA ; unit : 'counts' ou 'um'."""
        n = self._comptes(distance, unit)
        if n == 0:
            raise ValueError("Distance nulle.")
        va = self._vitesse(speed)
        tp0 = self._get_int("TP?")
        if REFERENCE_MIN <= tp0 <= REFERENCE_MAX:
            self._verifier_limites(tp0 + n)
        self._autoriser_mouvement()          # toutes les vérifications avant la première écriture
        self._borner(n, 0)
        self.velocity(va)
        t0 = time.monotonic()
        self.move_relative(n)
        self._attendre_arret(timeout_s or self._duree_max(n, va))
        tp1 = self._get_int("TP?")
        return {"demande_comptes": n, "TP_avant": tp0, "TP_apres": tp1, "ecart_comptes": tp1 - tp0 - n,
                "duree_s": round(time.monotonic() - t0, 1), "VA": va}

    def forward(self, distance, speed="normal", unit: str = "counts") -> dict:
        return self.move(abs(distance), speed, unit)

    def backward(self, distance, speed="normal", unit: str = "counts") -> dict:
        return self.move(-abs(distance), speed, unit)

    def nudge(self, direction: int = 1, steps: int = 1, speed="normal") -> dict:
        """Avance (direction=1) ou recule (-1) de `steps` incréments ; l'incrément vaut parent.increment comptes."""
        if direction not in (1, -1) or steps < 1:
            raise ValueError("direction doit valoir 1 ou -1 et steps au moins 1.")
        return self.move(direction * steps * self.parent.increment, speed, "counts")

    def goto(self, target, speed="normal", approach: str | None = "+", closed_loop: bool = True,
             unit: str = "counts", timeout_s: float | None = None) -> dict:
        """Va à une position absolue : un nom mémorisé, des comptes (TP) ou, avec unit='um', des µm depuis la référence.
        approach '+' ou '-' : la dernière course se fait toujours dans ce sens (la répétabilité de ±0,5 µm du 8311
        n'est donnée que dans un seul sens) ; None pour aller droit. closed_loop : MM=1 avec DB=2 pendant le déplacement,
        remis à 0 après."""
        tp = self._exiger_reference()
        if isinstance(target, str):
            pos = self.positions()
            if target not in pos:
                raise Newport8742Error(f"Position {target!r} inconnue : {sorted(pos)}.")
            cible = int(pos[target]["counts"])
        elif unit == "um":
            cible = SENTINELLE + self._comptes(target, "um")
        else:
            cible = int(target)
        va = self._vitesse(speed)
        self._verifier_limites(cible)
        points = [cible]
        delta = cible - tp
        sur = self.parent.overshoot
        if approach == "+" and delta <= 0:
            points = [cible - sur, cible]
        elif approach == "-" and delta >= 0:
            points = [cible + sur, cible]
        elif approach not in ("+", "-", None):
            raise ValueError("approach doit valoir '+', '-' ou None.")
        for p in points:
            self._verifier_limites(p)
        if abs(delta) <= 1 and len(points) == 1:
            return {"cible": cible, "TP_final": tp, "ecart_comptes": tp - cible, "points": [], "duree_s": 0.0, "VA": va}
        self._autoriser_mouvement()          # toutes les vérifications avant la première écriture
        precedent = tp
        for p in points:
            self._borner(p, precedent)
            precedent = p
        if closed_loop and self._get_int("SN?") != UNITE_COMPTES:
            raise Newport8742Error("Boucle fermée refusée : SN doit valoir 1 (comptes codeur).")
        self.velocity(va)
        t0 = time.monotonic()
        db0 = self.deadband() if closed_loop else None
        try:
            if closed_loop:
                self.deadband(2)
                self.closed_loop(1)
            for p in points:
                self.move_absolute(p)
                self._attendre_arret(timeout_s or self._duree_max(p - self._get_int("TP?"), va))
            if closed_loop:
                time.sleep(1.0 if POLL_S else 0.0)
        finally:
            if closed_loop:
                try:
                    self.closed_loop(0)
                finally:
                    self.deadband(db0)
        tp1 = self._get_int("TP?")
        return {"cible": cible, "TP_final": tp1, "ecart_comptes": tp1 - cible, "points": points,
                "duree_s": round(time.monotonic() - t0, 1), "VA": va}


class Newport8743(Instrument):
    """Newport 8743-CL. `transport` expose write(cmd), ask(cmd) et close() ; par défaut l'USB défensif."""

    def __init__(self, name: str, transport=None, allow_motion: bool = False, max_move: int = 60000,
                 axes: tuple[int, ...] = (1, 2), max_velocity: int = 1000, increment: int = 20, overshoot: int = 500,
                 positions_file: str = "newport_positions.json", **kwargs):
        """max_move : déplacement maximal par commande, en comptes (défaut 60000, environ 3 mm).
        max_velocity : VA maximal accepté (défaut 1000 ; le maximum du contrôleur est 2000, soit environ 3 fois la
        vitesse spécifiée du 8311). increment : comptes d'un nudge. overshoot : recul de l'approche par un seul côté.
        positions_file : JSON des positions mémorisées, par numéro de série et par axe."""
        super().__init__(name, **kwargs)
        self.max_velocity = int(max_velocity)
        self.increment, self.overshoot, self.positions_file = int(increment), int(overshoot), positions_file
        if transport is None:
            transport = UsbTransport(defensive=True, match="8743")
        self._transport = transport
        self.allow_motion = allow_motion
        self.max_move = int(max_move)
        for a in axes:
            self.add_submodule(f"axis{a}", Newport8743Axis(self, f"axis{a}", a))
        self.connect_message()

    # -- fichier de positions --
    def _serie(self) -> str:
        if not getattr(self, "_serial", None):
            self._serial = str(self.get_idn().get("serial") or "inconnu")
        return self._serial

    def store_lire(self, axe: int) -> dict:
        try:
            with open(self.positions_file, encoding="utf-8") as f:
                return json.load(f).get(self._serie(), {}).get(str(axe), {})
        except FileNotFoundError:
            return {}

    def store_ecrire(self, axe: int, cle, valeur, donnees: dict | None = None) -> None:
        """Écrit le fichier de positions (remplacement atomique). Avec `cle`, remplace cette clé de l'axe ; sinon écrit `donnees`."""
        try:
            with open(self.positions_file, encoding="utf-8") as f:
                tout = json.load(f)
        except FileNotFoundError:
            tout = {}
        axe_d = tout.setdefault(self._serie(), {}).setdefault(str(axe), {})
        if cle is not None:
            axe_d[cle] = valeur
        else:
            axe_d.clear()
            axe_d.update(donnees)
        tmp = self.positions_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(tout, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.positions_file)

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


# ======================================================================================================
# Raccourcis de connexion et vérification de l'installation
# ======================================================================================================
def connect_8743(name: str = "pico8743", allow_motion: bool = False, **kwargs) -> "Newport8743":
    """Connecte le 8743-CL en USB (transport défensif). Arguments de Newport8743 : max_move, max_velocity, increment,
    overshoot, positions_file."""
    return Newport8743(name, transport=UsbTransport(defensive=True, match="8743"), allow_motion=allow_motion, **kwargs)


def connect_8742(name: str = "pico8742", allow_motion: bool = False, **kwargs) -> "Newport8742":
    """Connecte le 8742 en USB. Non éprouvé avec un moteur : voir docs/protocol_8742.md."""
    return Newport8742(name, transport=UsbTransport(match="8742"), allow_motion=allow_motion, **kwargs)


def main_check(argv=None) -> int:
    """Vérifie Python, QCoDeS, la DLL et les contrôleurs, sans envoyer de mouvement."""
    import argparse
    p = argparse.ArgumentParser(description="Vérification de l'installation de newport_picomotors.")
    p.add_argument("--check", action="store_true")
    p.add_argument("--dll", default=os.environ.get("NEWPORT_USBDLL", CHEMIN_DLL_DEFAUT))
    p.add_argument("--no-usb", action="store_true", help="ne pas ouvrir les contrôleurs")
    args = p.parse_args(argv)
    ok = True

    def ligne(etat, texte):
        print(f"[{etat}] {texte}")

    ligne("OK" if struct.calcsize("P") * 8 == 64 else "ECHEC", f"Python {sys.version.split()[0]}, {struct.calcsize('P') * 8} bits (64 attendus)")
    ok &= struct.calcsize("P") * 8 == 64
    try:
        import qcodes
        ligne("OK", f"qcodes {qcodes.__version__}")
    except Exception as exc:
        ligne("ECHEC", f"qcodes absent ({exc}) : pip install qcodes")
        ok = False
    if args.no_usb:
        ligne("--", "ouverture USB ignorée (--no-usb)")
        return 0 if ok else 1
    if not os.path.exists(args.dll):
        ligne("ECHEC", f"DLL introuvable : {args.dll} (installer le pilote Newport USB ou définir NEWPORT_USBDLL)")
        return 1
    try:
        dll = charger_dll(args.dll)
        declarer_signatures(dll)
        ligne("OK", f"DLL chargée : {args.dll}, architecture {machine_pe(args.dll)}")
    except Exception as exc:
        ligne("ECHEC", f"chargement de la DLL : {exc}")
        return 1
    ouverte = False
    try:
        n = ouvrir(dll, PRODUCT_ID_DEFAUT)
        ouverte = True
        infos = []
        for _ in range(10):                      # écarte les réponses parasites restées dans le contrôleur
            infos = lire_infos(dll)
            if any("New_Focus" in d for _, d in infos):
                break
        for ident, desc in infos:
            ligne("OK", f"contrôleur {ident} : {desc}")
        if not infos:
            ligne("ECHEC", f"{n} périphérique(s) ouvert(s) mais liste vide : débrancher, rebrancher, fermer l'application Picomotor")
            ok = False
    except Exception as exc:
        ligne("ECHEC", f"ouverture USB : {exc}")
        ok = False
    finally:
        if ouverte:
            dll.newp_usb_uninit_system()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main_check())
