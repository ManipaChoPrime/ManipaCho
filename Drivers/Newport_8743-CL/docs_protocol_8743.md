# Protocole 8743-CL et 8311 (USB, Windows)

Dernière mise à jour : 2026-10-15. Ce fichier consigne ce qui est lu dans les manuels, ce qui est mesuré sur le matériel et ce qui reste inconnu. Les commandes communes avec le 8742 sont décrites dans [protocol_8742.md](protocol_8742.md) (tableaux de commandes, codes d'erreur, section "Différences 8743-CL").

## Matériel et sources

| Élément | Valeur | Source |
|---|---|---|
| Contrôleur | 8743-CL, série 13097, firmware v4.06 01/19/17 | `*IDN?` mesuré |
| Firmware attendu | v4.06 pour une série supérieure à 11001 | [notes de firmware p. 2](manuals/8743-CL_firmware_notes.pdf#page=2) |
| Positionneur | 8311, picomoteur compact en boucle fermée, course 12,7 mm, résolution du codeur 49,6 nm | [8311 manuel](manuals/8311_user_manual.pdf) |
| Câbles du 8311 | moteur RJ-22 et codeur DB-15 haute densité | [8743 p. 29](manuals/8743-CL_user_manual.pdf#page=29) |
| Liaison | USB, `usbdll.dll` x64 par `ctypes`, produit `0x4000` | [probe_8743.py](../Instrument/probe_8743.py) |
| Manuel du contrôleur | [8743-CL](manuals/8743-CL_user_manual.pdf) | |

Le 8743-CL pilote un picomoteur à la fois ([8743 p. 29](manuals/8743-CL_user_manual.pdf#page=29)). Axe 1 : 8311. Axe 2 : vide, sert de témoin.

## Méthode et règles

- Lemma écrit le code et les commandes à lancer. L'utilisateur lance tout ce qui touche le matériel et colle la sortie.
- Lemma annonce avant tout test qu'il lance de son côté (faux pilote, sans matériel).
- Le sondage `probe_8743.py` refuse d'envoyer : mouvements (`PA`, `PR`, `MV`, `JA`, `MC`, `MT`, `MZ`, `OR`, `AF`), requêtes `PR?` et `MV?`, écritures de boucle et de configuration (`MM`, `CL`, `DB`, `FE`, `ZH`, `SN`, `SL`, `SR`, `AD`, `AE`), `SM`, `RS`, `XX`, `*RST`. Il écrit seulement `VA` et `AC`, restaurés dans un `finally`.
- Vérification de la garde sans matériel : [check_no_motion_8743.py](../Instrument/check_no_motion_8743.py), résultat [check_no_motion_8743.json](../Instrument/check_no_motion_8743.json). Ce faux contrôleur reproduit le manuel, pas des mesures.

## Journal des étapes

| Date | Étape | Résultat |
|---|---|---|
| 2026-10-15 09:24 | 8743-CL seul, première version du sondage | 10 conformes, 6 non conformes : réponses décalées à partir de T11 (chaque lecture donnait la réponse précédente). Valeurs de T11 à T16 inutilisables |
| 2026-10-15 09:30 | relance après ajout de la synchro | échec au démarrage : la DLL a lu `0, NO ERROR DETECTED` à la place de la description, réponse restée dans le contrôleur |
| 2026-10-15 09:35 | 8743-CL seul, sonde avec synchro et relecture de la liste | 16 conformes, 0 non conforme, aucune réponse orpheline ni tardive |
| 2026-10-15 09:55 | 8311 branché sur l'axe 1, lectures seulement | 16 conformes, 0 non conforme, aucune erreur en file, aucune note de synchro |

| 2026-10-15 | driver `Newport8743` écrit, tests logiques sur faux transport (Lemma, sans matériel) | 29 tests du 8743 et 14 du 8742 passent ; trois gardes cassées volontairement (allow_motion, max_move, garde de AF) font échouer les tests |
| 2026-10-15 | tests utilisateur : 43 tests logiques, 7 tests matériel du driver 8743-CL | tous passent ; transport : 0 orpheline, 1 réponse tardive (`1FE?`, 0,20 s) ; durée 68 s à cause du vidage avant chaque requête |
| 2026-10-15 | transport : vidage limité au démarrage et après une écriture | 45 tests logiques passent sur faux transport ; confirmé par l'utilisateur : 45 tests logiques et 7 tests matériel passent, 20,7 s au lieu de 68 s, 0 orpheline, 0 tardive |
| 2026-10-15 | `motion_8743.py` écrit : aller de +100 comptes puis retour de -100, axe 1, VA=200, boucle ouverte | vérifié sur faux contrôleur (5 scénarios : normal, refus avant mouvement, annulation, erreur du contrôleur, axe bloqué) ; pas encore lancé sur le matériel |
| 2026-10-15 10:44 | premier mouvement, `motion_8743.py`, axe 1, +100 puis -100 comptes, VA=200, boucle ouverte | aucune erreur ; TP 0 -> 100 -> 0 ; `PR?` -> 100 puis 0 ; `QM?` 0 -> 3 ; VA et AC restaurés ; `MD?` jamais vu à 0 |
| 2026-10-15 | `motion_8743.py` modifié : échantillons de `MD?` enregistrés, 3 lectures de TP après l'écriture de VA, vitesse affichée seulement si `MD?` est vu à 0 | vérifié sur faux contrôleur ; à relancer avec `--va 50` |
| 2026-10-15 11:05 | second mouvement, mêmes réglages que le premier (VA=200, l'option `--va 50` n'avait pas été passée) | aucune erreur ; TP -1 -> 99 (+100), 99 -> 0 (-99) ; TP -1 avant, -2 après, sans mouvement commandé ; `PR?` -> 100 puis 0 ; `MD?` jamais vu à 0 ; l'envoi du PR avec lecture de TB? prend 1,3 s ; l'utilisateur entend un bip et ne voit pas bouger l'axe (5 µm) |
| 2026-10-15 | `motion_8743.py` et driver modifiés : `PR` sans lecture de TB? avant le suivi de `MD?`, erreurs lues après, arrêt si erreur ; `--comptes` jusqu'à 20000 (1 mm) ; durée attendue affichée | 46 tests logiques et 5 scénarios du faux contrôleur passent ; à lancer sur le matériel |
| 2026-10-15 11:30 | troisième mouvement, `--va 50`, 100 comptes, `PR` envoyé sans lecture de TB? | aucune erreur ; `MD?` à 0 de 0,30 s à 3,34 s après l'envoi, axe arrêté à 3,54 s (aller et retour identiques à 2 ms) ; TP -1 -> 99 (+100), 99 -> 0 (-99) ; `PR?` -> 100 puis 0 ; VA et AC restaurés ; TP lu 3 fois au repos : -1, -1, -1 |
| 2026-10-15 | `motion_8743.py` modifié pour un essai de 2 mm : `--comptes` jusqu'à 45000, `--sens`, `--pause` (lecture d'une règle entre l'aller et le retour), TP lu toutes les 2 s pendant les grands mouvements, délai maximal automatique | vérifié sur faux contrôleur ; pas encore lancé sur le matériel |
| 2026-10-15 11:41 | mouvement de 40323 comptes demandé, `VA`=2000, interrompu par `Ctrl+C` de l'utilisateur après 10,6 s | `TP?` 1392 -> 13919 en 10,6 s (relevé toutes les 2,1 s : 3858, 6534, 9024, 11500, 13919), soit environ 1180 comptes/s ; arrêt par `ST` puis `AB`, `TP?` final 16796 (15404 comptes, 0,76 mm), VA et AC restaurés ; l'utilisateur a vu la vis tourner sur sa marque ; moteur très bruyant à `VA`=2000 |
| 2026-10-15 | `closed_loop_8743.py` écrit : A = départ, B = A + 2000 comptes, 3 cycles A/B en boucle ouverte puis en boucle fermée, `TP?` lu 2 s après chaque arrêt | vérifié sur faux contrôleur (normal, refus, annulation, erreur en boucle fermée) ; pas encore lancé sur le matériel |
| 2026-10-15 14:55 | `closed_loop_8743.py` : A = 16795, B = A + 2000 comptes, 3 cycles, `VA`=1000, `DB`=20, boucle ouverte puis fermée | aucune erreur. Écart TP - cible après 2 s : boucle ouverte A {0, +1, 0}, B {-1, -1, -1} ; boucle fermée A {0, 0, 0}, B {0, -1, -1}. Maximum 1 comptage (50 nm) dans les deux cas. `MM=1` activé sans mouvement (TP 16795 quatre fois). Durée de 2000 comptes : 3,4 s en B, 3,2 s en A. MM, VA, AC restaurés |
| 2026-10-15 | demande de l'utilisateur : retrouver A et B après mise hors tension, `PA` à `VA`=500 en boucle fermée, fonctions avance lente et rapide, incrément, distance et vitesse données | `absolute_8743.py` écrit (AF avec suivi de TP, arrêt au-delà de 20000 comptes, comparaison entre deux essais) et paramètre `absolute_search_mode` (AD) ajouté au driver ; vérifié sur faux contrôleur ; pas encore lancé sur le matériel |
| 2026-10-15 15:20 | `closed_loop_8743.py --amplitude 10000 --va 500 --deadband 2 --cycles 3`, boucle ouverte puis fermée, A = 0, B = 10000 comptes (496 µm) | 24 arrivées sur 24 à écart nul des deux côtés ; aucune erreur, aucune oscillation avec `DB`=2 ; `MM=1` sans mouvement. Durée de 10000 comptes : aller 28,1 à 29,5 s, retour 31,2 à 31,4 s, soit 353 et 318 comptes/s (0,71 et 0,64 par unité de `VA`). TP revenu à 0 après redémarrage du contrôleur (il valait 16795), `QM` à 0, `OF?` à 0 |
| 2026-10-15 | `sweep_8743.py` écrit : combinaisons VA:comptes en une exécution, une confirmation, tableau récapitulatif ; `AF` laissé de côté à la demande de l'utilisateur | vérifié sur faux contrôleur ; pas encore lancé sur le matériel |
| 2026-10-15 15:35 | `sweep_8743.py`, `DB`=2, 2 cycles : (`VA`=1000, 20000 comptes), (2000, 20000), (2000, 40000 comptes = 1,98 mm), boucle ouverte puis fermée | aucune erreur ; écart TP - cible maximal 1 comptage dans les 6 séries, ouverte ou fermée ; `MM`, `VA`, `AC` restaurés. Durées aller / retour : 29,6 / 27,8 s, 17,8 / 15,7 s, 35,7 / 30,0 s |
| 2026-10-15 16:16 et 16:18 | `absolute_8743.py`, `AD`=1, deux essais séparés par une mise hors tension du contrôleur | `AF` déplace l'axe dans le sens positif à environ 1250 comptes/s (la vitesse de `VA`=2000) et ne termine pas : `AF?` reste à 0 jusqu'à l'arrêt automatique à 20 245 puis 20 617 comptes d'excursion (1 mm). `ST` renvoie l'erreur `120` (HOMING ABORTED), ce qui est l'effet normal d'un arrêt pendant la recherche. `TP?` final 20 653 puis 21 045, `OF?` toujours 0. Au total l'axe s'est éloigné d'environ 41 700 comptes (2,07 mm) de sa position de départ |
| 2026-10-15 | relecture des documents après les deux essais `AF` ; ajout de la fiche technique [DS-102005, 831x](manuals/DS-102005_831x_datasheet.pdf) | voir « Codeur et référence du 8311 » ci-dessous |
| 2026-10-15 | fonctions de haut niveau ajoutées au driver 8743-CL : `where`, `move`, `forward`, `backward`, `nudge`, `goto`, `mark`, `forget`, `set_reference`, `set_limits`, plafond `max_velocity`=1000 ; fichier unique `newport_picomotors.py` généré par `build_single_file.py` | 62 tests logiques passent sur les modules et sur le fichier unique (faux contrôleur avec mouvement) ; quatre gardes coupées une à une font échouer les tests (le plafond de vitesse est doublé par la validation QCoDeS) ; `DH` comme référence jamais essayé sur le matériel |
| 2026-10-15 | `newport_picomotors.py --check`, puis `test_hardware_api_8743.py` sans puis avec mouvement | `--check` : Python 64 bits, qcodes 0.61.0, DLL, contrôleur 13097 vus. `TP` valait -20655 avant `set_reference` : le retour à la position de départ, calculé à -20653, a abouti à 2 comptages près. `DH` fixe `TP` à 1 000 000 sans mouvement, la référence persiste entre deux lancements. Mouvement : `move` +100 et -100 à écart 0, `goto("A")` à écart 0 (approche par 999500, 1 000 000), `nudge` à écart 0. Un test échoue (4 passés sur 5, puis 4 sur 5) : un `move` refusé avait changé `VA` de 2000 à 500, car `VA` était écrit avant les vérifications. Durées : `goto` 11 s, suite 52 s, à cause du vidage du transport après chaque écriture |
| 2026-10-15 | corrections : toutes les vérifications de `move` et `goto` avant la première écriture ; le transport ne vide plus après `VA`, `AC`, `DB`, `MM`, `PA`, `PR`, `DH`, `ST`, `AB`, `QM`, `SN`, `CL`, `FE`, `AD` (jamais de réponse mesurée) | 63 tests logiques sur les modules et sur le fichier unique ; remettre le défaut dans `move` fait échouer un test ; à relancer sur le matériel |
| 2026-10-15 | `test_hardware_api_8743.py` relancé avec mouvement après les corrections | 5 passés en 32,7 s (52,6 s avant) ; `goto` 7,2 s (11,1 s) ; `move` 1,2 s ; `nudge` 0,9 s ; écarts 0 ; 0 réponse orpheline, 1 tardive de 0,2 s |
| 2026-10-15 | `_attendre_arret` envoie `ST` sur `KeyboardInterrupt` (bouton Stop d'un notebook) ; notebook `demo_picomoteurs.ipynb` (généré par `build_demo_notebook.py`) | 64 tests logiques ; les 6 cellules de code exécutées contre le faux contrôleur (6 arrivées à écart 0, `MM` et `DB` restaurés, référence retrouvée après un « redémarrage du kernel ») ; pas encore lancé sur le matériel |

Cause du premier décalage : non identifiée. Il n'est pas réapparu. Le driver lira la file de réponses de façon défensive (vider avant une requête, relire avec délai).

## Mesures

Source : rapports collés par l'utilisateur, `probe_8743.py` (sans moteur à 09:35, avec 8311 à 09:55).

| Point | Sans moteur | 8311 sur l'axe 1 | Manuel |
|---|---|---|---|
| `*IDN?` | `New_Focus 8743-CL v4.06 01/19/17 13097` | idem | avec virgule et `SN` selon le manuel ([p. 80](manuals/8743-CL_user_manual.pdf#page=80)), absents ici |
| `VE?` | `8743-CL Version 4.06 01/19/17` | idem | conforme ([p. 117](manuals/8743-CL_user_manual.pdf#page=117)) |
| Terminaisons de commande | aucune, CR, LF, CR LF répondent | idem | le pilote ajoute CR |
| Terminaison de réponse | CR LF | idem | conforme |
| `VA?`, `AC?` axes 1 et 2 | 2000 et 100000 | idem | défauts du manuel |
| `1VA2001`, `1AC200001` | erreurs `110` et `111` | idem | x10 et x11 |
| `QM?` | 0, 0 | 0, 0 | le type n'est pas détecté sans mouvement |
| `SN?` | 1, 1 | 1, 1 | comptes codeur, défaut ([p. 111](manuals/8743-CL_user_manual.pdf#page=111)) |
| `MM?` | 0, 0 | 0, 0 | boucle fermée désactivée ([p. 94](manuals/8743-CL_user_manual.pdf#page=94)) |
| `ZH?` | 0, 0 | **4, 0** | bit 2 = codeur quasi-absolu présent ([p. 119](manuals/8743-CL_user_manual.pdf#page=119)) |
| `PH?` | 63 | **56** | bits 0 à 2 : axe 1, bits 3 à 5 : axe 2 ([p. 101](manuals/8743-CL_user_manual.pdf#page=101)) |
| `TP?` | 0, 0 | **1, 0** | comptes codeur (`SN`=1) |
| `CL?` | `0.1000` | `0.1000` | « entier » dans le manuel ([p. 87](manuals/8743-CL_user_manual.pdf#page=87)) |
| `DB?`, `FE?` | 0 et 1000 | 0 et 1000 | défauts ([p. 89](manuals/8743-CL_user_manual.pdf#page=89), [p. 92](manuals/8743-CL_user_manual.pdf#page=92)) |
| `MD?` | 1, 1 | 1, 1 | arrêté |
| `TB?` | file vide | file vide, pas de `x34` | |

### Lecture avec le 8311 branché

- **`PH?` 63 puis 56.** Avec le 8311, les bits 0 à 2 de l'axe 1 (limites positive et négative, index) passent à 0 : le 8311 est vu et n'est sur aucune limite. Les bits 3 à 5 de l'axe 2 restent à 1, comme sans positionneur.
- **`ZH?` axe 1 vaut 4.** Le bit 2 signale un codeur quasi-absolu. Le sondage n'écrit jamais `ZH`, et la valeur était 0 sans moteur. L'hypothèse probable est une détection du 8311 à la mise sous tension, mais une valeur sauvée plus tôt par l'application Newport ne peut pas être exclue.
- **`TP?` axe 1 vaut 1.** Un compte codeur au repos. Le sens physique de cette valeur reste à mesurer.
- **`QM?` reste à 0.** Le contrôleur met `QM` à jour au premier mouvement (détection automatique, `ZZ`=0).

### Conséquence pour le driver

Le 8311 a un codeur quasi-absolu. Les commandes de recherche d'absolu entrent donc dans le périmètre, ce que je classais hors périmètre avant cette mesure :

- `AF` lance la recherche de position absolue et **déplace** l'axe ([8743 p. 86](manuals/8743-CL_user_manual.pdf#page=86)). Elle exige `ZH` bit 2 et `SN`=1, sinon erreur `x36`.
- `AD` choisit le mode de recherche, `AF?` donne son état, `OF?` dit si la position absolue est trouvée ([p. 84](manuals/8743-CL_user_manual.pdf#page=84), [p. 86](manuals/8743-CL_user_manual.pdf#page=86), [p. 97](manuals/8743-CL_user_manual.pdf#page=97)).
- `OR`, `MT` et `MZ` donnent l'erreur `x37` avec un codeur quasi-absolu ([p. 131](manuals/8743-CL_user_manual.pdf#page=131)). Le driver ne doit pas les proposer pour le 8311.
- `ZZ` bit 2 lance la recherche d'absolu après reset. Il vaut 0 ici.

## Codeur et référence du 8311

Source : [fiche technique DS-102005, 831x](manuals/DS-102005_831x_datasheet.pdf), [manuel du 8311](manuals/8311_user_manual.pdf), [manuel du 8743-CL §3.3](manuals/8743-CL_user_manual.pdf#page=29).

- Le 8311 a un codeur rotatif optique **incrémental** (6400 comptes par tour de vis, 49,6 nm par comptage). Il n'a **pas** de fins de course : « Limit Switches Forward/Reverse : No/No », alors que le 8310CE en a. La fiche dit que le 8311 a des capacités similaires à celles du 8310CE, « except [...] it doesn't have the limit switches ».
- La répétabilité bidirectionnelle du 8311 est « N/A ». Seule la répétabilité dans un seul sens est donnée : ±0,5 µm sur toute la course, en approchant toujours du même côté.
- La fiche annonce « Closed loop steady-state error : 0 counts » avec le 8743-CL et un temps d'établissement inférieur à 100 ms. Cela concorde avec les écarts nuls mesurés.
- La boucle fermée du 8743-CL corrige la position **seulement à l'arrêt**, vers le nombre de comptes demandé ([8743 §3.3](manuals/8743-CL_user_manual.pdf#page=29)). Elle ne donne pas de position absolue. Le codeur compte des tours de vis depuis la mise sous tension.
- Le « positionnement absolu » du 8743-CL vient des fins de course du 8310CE et des méthodes `OR`, `MT`, `MZ`, listées pour les 8310 et 8410 mais pas pour le 8311.
- Conclusion : le 8311 n'a aucune référence électronique propre. La position en comptes est perdue à chaque mise hors tension. Une référence demande soit une butée mécanique (non documentée pour le 8311, risque de calage du moteur, couple limite 0,018 N·m), soit une référence externe.
- Le codeur mesure la rotation de la vis, pas le déplacement de l'embout : un jeu mécanique, une charge ou une particule sur l'embout peuvent donner 0,1 à 10 µm d'écart ([manuel du 8311](manuals/8311_user_manual.pdf)). Approcher chaque position du même côté réduit l'effet.

## Fonctions de haut niveau (driver `Newport8743`, fichier `newport_picomotors.py`)

Elles reposent sur ce qui est mesuré : `PA` et `PR` aboutissent à 1 comptage près à toutes les vitesses essayées, la position vit dans le contrôleur (conservée tant qu'il est allumé), le 8311 n'a pas de référence propre.

| Fonction | Rôle |
|---|---|
| `set_reference()` | `DH` à 1 000 000 : la position actuelle devient la référence, sans mouvement. À refaire après chaque redémarrage du contrôleur, sur la même référence physique. Refusé si une référence existe (`force=True` pour la déplacer) |
| `reference_valid` | vrai si `TP` est entre 500 000 et 1 500 000 ; faux si le contrôleur a redémarré (`TP` repart de 0) |
| `where()` | position en comptes et en µm depuis la référence, mouvement en cours, boucle fermée, vitesse, noms proches |
| `mark(nom)`, `forget(nom)`, `positions()` | positions mémorisées dans un fichier JSON par numéro de série et axe |
| `goto(cible)` | cible : nom, comptes, ou µm depuis la référence ; arrive toujours par le même côté (`approach`, recul de 500 comptes) ; boucle fermée pendant le déplacement avec `DB`=2, remise à 0 après ; refuse sans référence valide |
| `move(distance, speed, unit)`, `forward`, `backward` | déplacement relatif ; vitesses `lent` (VA 50), `normal` (500), `rapide` (1000) ou une valeur de VA ; unité `counts` ou `um` |
| `nudge(sens, steps)` | incrément (20 comptes par défaut, environ 1 µm) |
| `set_limits(bas_um, haut_um)` | limites logicielles depuis la référence, car le 8311 n'a pas de fins de course |

Sûreté : aucun mouvement sans `allow_motion=True` ; `max_move` par commande (60 000 comptes par défaut, environ 3 mm) ; `max_velocity`=1000 par défaut (le maximum du contrôleur est 2000, soit environ trois fois la vitesse spécifiée du 8311) ; limites logicielles ; arrêt `ST` si un mouvement dépasse sa durée maximale ; les positions mémorisées sont refusées si la référence est périmée.

## Écarts avec le manuel

| Écart | Détail |
|---|---|
| `*IDN?` | pas de virgule ni de `SN` avant la série |
| `MM?` et `FE?` | syntaxe écrite `xxDB?` dans le manuel ; `xxMM?` et `xxFE?` fonctionnent |
| `CL?` | réponse décimale `0.1000`, le manuel dit « entier » |
| `VA`, `AC` | `VA0` et `AC0` ne sont pas refusés sur le 8742 ; non testé sur le 8743-CL (le sondage n'envoie pas de valeur sous le minimum) |

## Incertitudes ouvertes

| Point | État |
|---|---|
| Sens de `PR?` | **résolu** (premier mouvement, 2026-10-15) : cible absolue. Après `PR` de -100 depuis TP=100, `PR?` rend 0, pas -100. À confirmer sur un second point de départ non nul |
| `MV?` non décrite dans les manuels | ouvert, mnémonique de mouvement exclu |
| Unité de `VA` et `AC` quand `SN`=1 | ouvert, exige un mouvement mesuré |
| Comportement de la boucle fermée (`MM`=1) | partiel : aucune oscillation ni erreur avec `DB`=20 puis `DB`=2, aucun mouvement à l'activation. Écarts identiques à la boucle ouverte : maximum 1 comptage à 2000 comptes (`DB`=20), 0 sur 24 arrivées à 10000 comptes (`DB`=2, `VA`=500). La boucle fermée n'apporte aucun gain mesurable dans ces conditions, parce que `PA` en boucle ouverte est déjà exact au comptage près. Non testé : grandes vitesses, distances de 1 à 2 mm, charge sur l'embout |
| Origine de `ZH`=4 (détection ou valeur sauvée) | à vérifier : éteindre, débrancher le 8311, rallumer, lire `ZH?` |
| `VA0` et `AC0` sur le 8743-CL | non testé |
| Type de moteur du 8311 (`QM`) | **résolu** : `QM` passe de 0 à 3 (Standard) au premier mouvement, détection automatique, non sauvé (aucun `SM`) |
| `MD?` pendant un mouvement | **résolu** (2026-10-15 11:30, `VA`=50) : 0 pendant le mouvement, 1 à l'arrêt, comme le manuel ([8743 p. 93](manuals/8743-CL_user_manual.pdf#page=93)). Avec `VA`=200 le mouvement de 100 comptes ne laissait pas à la boucle le temps de le voir |
| `TP?` en boucle ouverte avec `SN`=1 : codeur réel ou calcul ? | **lit le codeur, très probablement** : trois changements de 1 à 2 comptes sans aucune commande de mouvement (1 puis 0 au premier essai, 0 puis -2 pendant le second, -2 puis -1 entre le second et le troisième). Un compteur de pas commandés ne dérive pas au repos. Les deltas d'un aller-retour valent +100 puis -99 aux deux derniers essais, ce qui est reproductible : rebond du codeur de 1 comptage ou arrondi de la conversion. Pas de mesure indépendante du déplacement |
| `AF` avec le 8311 | **ne convient pas** (2026-10-15) : deux essais, aucune fin de recherche en plus de 1 mm. Le manuel du 8743-CL décrit `AE` comme propre au positionneur (défauts : premier incrément d'index 570, position de départ 8190, incrément 10, 25 repères au plus), ce qui suppose une recherche de quelques milliers de comptes au plus. Les notes du firmware ne citent que les codeurs MicroE à technologie Micro Motion Absolute. Le manuel du 8311 ne mentionne ni index, ni référence, ni position absolue. Le manuel du 8743-CL ne liste le 8311 pour aucune méthode de référencement (`OR` : 8310-V, `MZ` : 8410, `MT` : 8310 et 8310-V). `ZH` bit 2 vaut 1 sur l'axe 1 avec le 8311, origine inconnue. **Ne plus lancer `AF`** : sans fin de recherche, l'axe peut aller jusqu'en bout de course |
| Distance parcourue par `AF` (ancien point) | ouverte : le manuel ([8743 p. 86](manuals/8743-CL_user_manual.pdf#page=86)) ne la donne pas. `AD`=1 ramène l'axe à sa position de départ, `AD`=2 au zéro absolu. `ZZ` bit 2 lance la recherche à chaque reset et se sauve avec `SM` ([p. 120](manuals/8743-CL_user_manual.pdf#page=120)) |
| Position absolue après mise sous tension | `OF?` vaut 0 (position absolue non trouvée) le 2026-10-15 ; `AF` n'a jamais été lancé. Après un redémarrage du contrôleur, `TP?` repart de zéro : les positions A et B notées en comptes ne se retrouvent qu'avec `AF`, qui déplace l'axe |
| Déplacement réel du 8311 | non vérifié à l'œil : 100 comptes valent 5 µm (49,6 nm par comptage, [8311](manuals/8311_user_manual.pdf)). Le bip entendu à chaque mouvement n'est décrit dans aucun des manuels |
| Vitesse mesurée du 8311 | `VA`=50 : 1,6 µm/s ; `VA`=500 : 16 à 17 µm/s ; `VA`=1000 : 34 à 36 µm/s ; `VA`=2000 : 56 à 66 µm/s. Le sens positif est plus lent de 6 à 16 % à chaque `VA`. La vitesse n'est plus proportionnelle à `VA` au-delà de 1000 (x1,7 pour x2). Spécification du 8311 : 1,2 mm/min, soit 20 µm/s typique à 2 kHz, et la garantie exclut un usage « à une vitesse supérieure à la vitesse spécifiée » ([8311](manuals/8311_user_manual.pdf)). `VA`=2000 donne environ 3 fois la vitesse typique |
| Vitesse en fonction de `VA` | mesures : `VA`=50 -> 31,4 comptes/s ; `VA`=2000 -> environ 1180 comptes/s (2,1 s par 2476 comptes), soit 0,63 et 0,59 comptage/s par unité de `VA`. Proportionnel à 6 % près. Troisième point : `VA`=1000 -> 2000 comptes en 3,4 s, soit 0,59 comptage/s par unité de `VA`. Le manuel prévoit 0,40 (2,5 pas par comptage, `VA` en pas/s) : écart de 50 %, non expliqué |
| Unité de `VA` et rapport comptes sur pas | mesuré à `VA`=50 : 100 comptes durent environ 3,2 s, soit 31 comptes/s, contre 4,96 s attendues (manuel du 8311 : comptage 49,6 nm, pas moteur environ 20 nm, soit 2,5 pas par comptage, avec `VA` en pas/s). Écart de 35 %, un seul point. Pour distinguer une erreur d'unité d'une approximation du pas, mesurer à une autre `VA` : la durée de N comptes doit varier en 1/`VA` |
| Ethernet | hors périmètre, USB seulement |

## Prochaines étapes

1. Fait côté code, à lancer par l'utilisateur : driver `Newport8743` (QCoDeS) avec transport défensif, validation de `VA` et `AC`, unité affichée par paramètre (comptes ou pas selon `SN`), refus du mouvement sans `allow_motion`, refus de `OR`, `MT` et `MZ` avec codeur quasi-absolu. Tests logiques sur faux transport, puis tests matériel sans mouvement.
2. Script de mouvement court : 8311 libre, en position médiane, quelques dizaines de comptes, arrêt et restauration. Il tranche `PR?`, `MD?`, l'unité de `VA` et le premier `QM`.
3. Boucle fermée (`MM`=1) en dernier, après les mouvements en boucle ouverte.
