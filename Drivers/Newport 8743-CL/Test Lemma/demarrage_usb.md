# Démarrage USB : Newport 8742 / 8743-CL

Dossier de travail : `C:\Users\argui\These\test_code_drivers_newport`.
Python 3.13.0 en 64 bits. Pilote dans `C:\Program Files (x86)\Newport\Newport USB Driver\Bin\x64`.

Le dépôt appelle `usbdll.dll` directement avec `ctypes`. `UsbDllWrap.dll` et pythonnet ne servent pas.
Rien de ce guide n'a été exécuté sur votre PC : les résultats attendus sont indicatifs.

## 1. Environnement virtuel

```powershell
cd C:\Users\argui\These\test_code_drivers_newport
py -3.13 --version
py -3.13 -c "import struct; print(struct.calcsize('P')*8, 'bits')"
py -3.13 -m venv .venv
```

Attendu : `Python 3.13.0` puis `64 bits`. Si le script d'activation est bloqué (erreur de stratégie d'exécution) :

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

L'invite doit commencer par `(.venv)`.

## 2. Installer QCoDeS, JupyterLab et les dépendances

```powershell
python -m pip install qcodes jupyterlab ipykernel pytest numpy matplotlib
```

Contrôle de l'installation de QCoDeS sur Python 3.13 :

```powershell
python -c "import sys, qcodes; print(sys.version); print('qcodes', qcodes.__version__)"
python -m pip check
```

Attendu : une version 3.13.0 et un numéro de version de QCoDeS, puis `No broken requirements found.`

Si `pip install qcodes` échoue (erreur de compilation, « no matching distribution », ou `pip check` signale un conflit), passez à Python 3.12 en 64 bits :

```powershell
deactivate
winget install Python.Python.3.12
Remove-Item -Recurse -Force .venv
py -3.12 -c "import struct; print(struct.calcsize('P')*8, 'bits')"
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install qcodes jupyterlab ipykernel pytest numpy matplotlib
python -c "import qcodes; print(qcodes.__version__)"
```

Le dossier `Bin\x64` du pilote convient aussi à Python 3.12 64 bits.

## 3. Vérifier le pilote avant Python

**Gestionnaire de périphériques** (clic droit sur Démarrer, Gestionnaire de périphériques) :

1. Contrôleur sous tension, câble USB branché.
2. Cherchez une entrée Newport (par exemple « Newport USB Devices »). Elle ne doit pas avoir de point d'exclamation jaune.
3. Sinon, installez le pilote avec l'installeur `x64` du paquet Newport USB Driver, contrôleur débranché ou éteint pendant l'installation (consigne du fichier Readme du pilote).

**TestUsb.exe** :

```powershell
& "C:\Program Files (x86)\Newport\Newport USB Driver\Bin\x64\TestUsb.exe"
```

1. Fermez l'application Picomotor avant.
2. Saisissez l'identifiant de produit `0x4000` (ou `16384` en décimal si l'outil refuse l'hexadécimal).
3. Ouvrez les périphériques, puis envoyez `*IDN?` et lisez la réponse. Attendu : une ligne du type `New_Focus 8742 v2.2 ... SN...`.
4. Fermez TestUsb.exe avant de lancer Python : un seul programme peut ouvrir le contrôleur.

## 4. Lancer le script de détection

```powershell
cd C:\Users\argui\These\test_code_drivers_newport
python .\Instrument\detect_usb.py
```

Autres usages :

```powershell
python .\Instrument\detect_usb.py --produit 0x4000 --rapport rapport_usb.txt
python .\Instrument\detect_usb.py --dll "C:\Program Files (x86)\Newport\Newport USB Driver\Bin\x64\usbdll.dll"
```

Le script écrit `rapport_usb.txt` dans le dossier courant. Renvoyez ce fichier en entier, même en cas d'erreur.
Les messages d'erreur sont en français et donnent l'action à faire :

| Situation | Message |
|---|---|
| `usbdll.dll` absente | DLL introuvable, vérifier l'installation ou passer `--dll` |
| Python et DLL de bits différents | Bits incompatibles |
| Contrôleur ouvert par Picomotor ou TestUsb | Ouverture échouée (code non nul), fermer l'autre programme |
| Contrôleur éteint ou non reconnu | Aucun périphérique trouvé |
| Autre code de retour non nul | Nom de l'appel, code, action |

## 5. Lancer JupyterLab

```powershell
cd C:\Users\argui\These\test_code_drivers_newport
.\.venv\Scripts\Activate.ps1
python -m ipykernel install --user --name newport-qcodes --display-name "Python (newport-qcodes)"
python -m jupyter lab
```

Choisissez le noyau « Python (newport-qcodes) » dans le notebook.
Fermez le noyau (ou le notebook) qui a ouvert le contrôleur avant de lancer `detect_usb.py`.

## Statut

| Élément | État |
|---|---|
| `detect_usb.py` compile | oui, `python -m py_compile` |
| `detect_usb.py` exécuté sur le matériel | non, en attente du `rapport_usb.txt` |
| Installation QCoDeS sur Python 3.13.0 | non exécutée sur votre PC |
