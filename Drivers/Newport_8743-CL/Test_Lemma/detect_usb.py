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
from __future__ import annotations

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


if __name__ == "__main__":
    sys.exit(main())
