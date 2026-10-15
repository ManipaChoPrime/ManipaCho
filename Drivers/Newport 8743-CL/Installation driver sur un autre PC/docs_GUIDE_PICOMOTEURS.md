# Picomoteurs 8311 pilotés par le 8743-CL : installation sur un autre PC et utilisation

Dernière mise à jour : 2026-10-15. Pilotes QCoDeS en USB sous Windows, dans **un seul fichier Python**.
Mesures et limites détaillées : [protocol_8743.md](protocol_8743.md).

## 1. Ce qui est validé

| Point | Résultat (8743-CL série 13097, firmware v4.06, 8311 sur l'axe 1) |
|---|---|
| Communication USB | stable : 0 réponse orpheline, au plus 1 réponse tardive de 0,2 s sur les suites de tests |
| Précision de `PA` et `PR` | écart au plus 1 comptage (49,6 nm) de 0,1 à 2 mm, `VA` de 50 à 2000, boucle ouverte comme fermée |
| Notebook `demo_picomoteurs.ipynb` | 6 arrivées entre A et B (100 µm) : écart maximal 1 comptage |
| Vitesse | `VA` 500 : 16 à 17 µm/s ; 1000 : 34 à 36 ; 2000 : 56 à 66. Spécification du 8311 : 20 µm/s typique |
| Position après mise hors tension | **perdue** : le 8311 a un codeur incrémental et pas de fin de course. Contrôleur allumé en continu : conservée, même si le kernel ou le PC redémarre |

**Pas validé** : le déplacement physique mesuré indépendamment au µm (seul le codeur l'a mesuré, plus une marque sur la vis), le 8742 avec les moteurs 8301-V, la recherche d'absolu `AF` (inutilisable avec le 8311), Ethernet.

## 2. Contenu du dossier à copier

| Fichier | Rôle | Obligatoire |
|---|---|---|
| `newport_picomotors.py` | tout le code : transport USB, drivers 8742 et 8743-CL, fonctions de haut niveau | oui |
| `requirements_picomoteurs.txt` | dépendances Python | oui |
| `GUIDE_PICOMOTEURS.md` | ce guide | non |
| `demo_picomoteurs.ipynb` | notebook de démonstration (A, B, `goto`, `nudge`) | non |
| `test_hardware_api_8743.py` | test sur le matériel, pour vérifier la nouvelle installation | non |
| `manuals/` | manuels du 8311 et du 8743-CL, pour les liens du guide | non |
| `protocol_8743.md` | mesures, écarts avec le manuel, incertitudes. Les liens vers des manuels absents du dossier (8742, fiches techniques) ne s'ouvrent pas | non |

Aucun autre fichier n'est nécessaire. Le fichier unique est **généré** à partir des modules de développement (`detect_usb.py`, `newport_usb.py`, `newport_8742.py`, `newport_8743.py`) par `build_single_file.py` : ne le modifie pas à la main.

## 3. Installation sur le nouveau PC

### 3.1 Prérequis

- Windows 10 ou 11, 64 bits.
- Python **64 bits** 3.12 ou 3.13 (testé : 3.13.0 avec qcodes 0.61.0).
- Le pilote **Newport USB Driver** (version 5.0.7 du 7 mai 2018 sur le poste de développement) : il fournit `usbdll.dll`.
- Le contrôleur 8743-CL branché en USB, le 8311 sur l'axe 1 (moteur RJ-22 et codeur DB-15).

### 3.2 Pilote Newport USB

Si `usbdll.dll` n'existe pas encore sur le PC, installe le paquet Newport USB Driver (fourni par Newport avec le contrôleur ou sur sa page de support) :

1. Ferme toutes les applications. **Éteins et débranche le 8743-CL pendant l'installation** (consigne du Readme du pilote).
2. Lance l'installeur. Une alerte de sécurité doit citer Newport Corporation : autorise-la.
3. Branche et allume le contrôleur, puis ouvre le Gestionnaire de périphériques : une entrée Newport, sans point d'exclamation jaune. Sinon : clic droit, « Mettre à jour le pilote », « Parcourir mon ordinateur ».

Emplacement de la DLL 64 bits selon l'option d'installation (Readme du pilote) :

| Option choisie à l'installation | Chemin de la DLL 64 bits |
|---|---|
| mode 32 bits sur Windows 64 bits (poste de développement) | `C:\Program Files (x86)\Newport\Newport USB Driver\Bin\x64\usbdll.dll` |
| mode 64 bits | `C:\Program Files\Newport\Newport USB Driver\Bin\usbdll.dll` |

Le code essaie ces deux chemins tout seul. Pour un autre emplacement : `$env:NEWPORT_USBDLL = "C:\chemin\usbdll.dll"` avant de lancer Python, ou `connect_8743("pico", dll_path="C:\\chemin\\usbdll.dll")`.

**Ne remplace pas le pilote Newport par WinUSB ou libusb** : ce code appelle la DLL Newport et ne marcherait plus.

### 3.3 Environnement Python

Dans PowerShell, dans le dossier copié (par exemple `C:\Users\<nom>\picomoteurs`) :

```powershell
py -3.13 -c "import struct; print(struct.calcsize('P')*8, 'bits')"    # doit afficher 64 bits
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements_picomoteurs.txt
```

Si l'activation est bloquée : `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`. L'invite doit commencer par `(.venv)`.
Si `qcodes` ne s'installe pas sous Python 3.13, refais l'environnement avec `py -3.12`.

### 3.4 Vérifier l'installation

Contrôleur allumé, application Picomotor fermée :

```powershell
python newport_picomotors.py --check
```

Résultat attendu (une ligne `contrôleur` par contrôleur branché) :

```
[OK] Python 3.13.0, 64 bits (64 attendus)
[OK] qcodes 0.61.0
[OK] DLL chargée : C:\Program Files (x86)\Newport\Newport USB Driver\Bin\x64\usbdll.dll, architecture x64
[OK] contrôleur 1 : New_Focus 8743-CL v4.06 01/19/17 13097
```

`--check` n'envoie aucun mouvement. Option `--no-usb` : vérifie seulement Python et qcodes.

### 3.5 Test sur le matériel (facultatif)

8311 libre, en milieu de course, avec au moins 0,3 mm de marge de chaque côté :

```powershell
$env:NEWPORT_HARDWARE=1 ; python -m pytest test_hardware_api_8743.py -v -s                          # sans mouvement
$env:NEWPORT_HARDWARE=1 ; $env:NEWPORT_MOTION=1 ; python -m pytest test_hardware_api_8743.py -v -s  # mouvements de 100 comptes
```

Attendu : 4 passed et 1 skipped, puis 5 passed. Le test pose une référence par `DH` à la position actuelle.

### 3.6 Notebook

```powershell
python -m ipykernel install --user --name picomoteurs --display-name "Python (picomoteurs)"
python -m jupyter lab demo_picomoteurs.ipynb
```

Choisis le noyau « Python (picomoteurs) », puis exécute les cellules dans l'ordre. La dernière (`pico.close()`) libère l'USB.

## 4. Utilisation

```python
from qcodes.instrument import Instrument
from newport_picomotors import connect_8743

Instrument.close_all()                       # permet de relancer la cellule sans erreur de nom
pico = connect_8743("pico", allow_motion=True, positions_file="positions_8743.json")
ax = pico.axis1                              # le 8311
ax.set_reference()                           # une fois par démarrage du contrôleur
ax.mark("A"); ax.forward(100, unit="um"); ax.mark("B")
ax.goto("A"); ax.goto("B"); ax.where()
pico.close()
```

`allow_motion=False` (défaut) : lectures seulement, aucun mouvement possible.

### Fonctions de l'axe (`pico.axis1`, `pico.axis2`)

| Fonction | Rôle | Retour |
|---|---|---|
| `where()` | position en comptes et en µm depuis la référence, mouvement en cours, boucle fermée, vitesse, noms proches | dict |
| `set_reference(counts=1000000, force=False)` | la position actuelle devient la référence (`DH`, sans mouvement). Refusé si une référence existe, sauf `force=True` | rien |
| `reference_valid` | vrai si la référence est posée depuis le dernier démarrage du contrôleur | bool |
| `mark(nom)`, `forget(nom)`, `positions()` | mémorise, oublie, liste les positions (fichier JSON par numéro de série et axe) | dict |
| `goto(cible, speed="normal", approach="+", closed_loop=True, unit="counts")` | va à un nom mémorisé, à des comptes, ou à des µm depuis la référence (`unit="um"`) | dict |
| `move(distance, speed="normal", unit="counts")` | déplacement relatif signé | dict |
| `forward(distance, ...)`, `backward(distance, ...)` | `move` positif ou négatif | dict |
| `nudge(direction=1, steps=1, speed="normal")` | incréments de 20 comptes (environ 1 µm) | dict |
| `set_limits(bas_um, haut_um)` | limites logicielles depuis la référence (`None, None` les retire) | rien |
| `stop()` | arrêt avec décélération (toujours permis) | rien |

`pico.abort()` arrête tous les axes sans décélération. Vitesses : `"lent"` (VA 50, environ 1,5 µm/s), `"normal"` (VA 500, environ 16 µm/s), `"rapide"` (VA 1000, environ 35 µm/s), ou un nombre. Unités : `"counts"` (1 comptage = 49,6 nm) ou `"um"`.

Retour de `move` : `demande_comptes`, `TP_avant`, `TP_apres`, `ecart_comptes`, `duree_s`, `VA`. Retour de `goto` : `cible`, `TP_final`, `ecart_comptes`, `points`, `duree_s`, `VA`. La durée inclut quelques secondes de commandes.

`goto` arrive toujours par le même côté (`approach="+"` : recul de 500 comptes si la cible est dans le sens négatif), car la répétabilité de ±0,5 µm du 8311 n'est donnée que dans un seul sens. Il active la boucle fermée (`MM`=1, bande morte 2 comptes) pendant le déplacement, puis la coupe.

### Paramètres QCoDeS de l'axe (lecture et écriture)

`velocity` (VA), `acceleration` (AC), `motor_type` (QM), `units` (SN), `position` (TP), `is_moving`, `closed_loop` (MM), `update_interval` (CL), `deadband` (DB), `following_error` (FE), `hardware_config` (ZH, lecture seule), `absolute_search_mode` (AD). Exemple : `ax.position()`, `ax.velocity(500)`.

### Réglages de `connect_8743(...)`

| Argument | Défaut | Rôle |
|---|---|---|
| `allow_motion` | `False` | autorise les mouvements |
| `max_move` | 60000 | déplacement maximal par commande, en comptes (environ 3 mm) |
| `max_velocity` | 1000 | VA maximal accepté. Le maximum du contrôleur est 2000 (environ 60 µm/s, trois fois la vitesse spécifiée du 8311) |
| `increment` | 20 | comptes d'un `nudge` |
| `overshoot` | 500 | recul de l'approche par un seul côté |
| `positions_file` | `newport_positions.json` | fichier des positions mémorisées |
| `dll_path` | cherché | chemin de `usbdll.dll` |

## 5. Règles de sûreté

- Aucun mouvement sans `allow_motion=True`. `max_move` et `max_velocity` plafonnent chaque commande. Toutes les vérifications passent avant la première écriture au contrôleur.
- Le 8311 n'a **pas de fin de course** : pose des limites avec `set_limits`, et garde de la marge de chaque côté.
- Bouton Stop du notebook ou `Ctrl+C` : le code envoie `ST`, remet `MM` et `DB`. Sinon le contrôleur finirait le mouvement.
- Une position mémorisée est **refusée** si le contrôleur a redémarré (`TP` repart de 0) : on ne part jamais au hasard.
- `find_absolute` (`AF`) est refusée par défaut : avec le 8311 elle ne termine pas (plus de 1 mm, deux essais) et déplace l'axe sans borne connue.
- Un seul programme à la fois peut ouvrir le contrôleur : fais `pico.close()` ou arrête le kernel avant de lancer un script ou l'application Picomotor.
- Au-delà de `VA` 700 environ, l'embout dépasse la vitesse spécifiée du 8311, et la garantie exclut « une vitesse supérieure à la vitesse spécifiée » ([manuel du 8311](manuals/8311_user_manual.pdf)). `VA` 500 est un bon réglage courant.

## 6. Dépannage

| Message ou symptôme | Cause probable | Action |
|---|---|---|
| `DLL introuvable` | pilote absent ou installé ailleurs | installer le pilote ; `NEWPORT_USBDLL` ou `dll_path` |
| bits incompatibles | Python 32 bits | installer Python 64 bits |
| `Ouverture échouée` ou liste vide | contrôleur utilisé par un autre programme, éteint ou mal branché | fermer Picomotor et les autres kernels ; débrancher, rebrancher |
| `Référence absente (TP=...)` | contrôleur redémarré, ou référence jamais posée | placer l'axe sur ta référence physique, puis `ax.set_reference()` |
| `Another instrument with the name 'pico'` | cellule de connexion relancée | `Instrument.close_all()` avant `connect_8743` |
| `allow_motion` | mouvement demandé en lecture seule | `connect_8743(..., allow_motion=True)` |
| `max_move` | déplacement trop grand | agrandir `max_move`, ou fractionner |
| `VA=... hors de 1 à 1000` | vitesse au-dessus du plafond | `max_velocity=2000` seulement en connaissance de cause |
| `hors des limites logicielles` | cible hors de `set_limits` | revoir les limites |
| `encore en mouvement après ... s : ST envoyé` | mouvement trop long ou bloqué | vérifier la mécanique ; `ax.where()` |
| erreurs `110` ou `111` | `VA` au-dessus de 2000 ou `AC` au-dessus de 200000 | rester dans les plages |
| moteur très bruyant | `VA` élevé | `speed="normal"` ou `"lent"` |

## 7. Mettre à jour le fichier unique (développeur)

Les modules de développement sont dans le dossier `Instrument/` du poste d'origine. Après une modification :

```powershell
python build_single_file.py      # régénère newport_picomotors.py
python -m pytest test_driver_logic.py test_driver_logic_8743.py test_api_8743.py -q
```

Le test sur le matériel ne remplace pas les tests logiques : ceux-ci tournent sans contrôleur, contre un faux transport.
