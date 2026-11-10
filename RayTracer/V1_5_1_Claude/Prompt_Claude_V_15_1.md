# Intégration des prescriptions réelles Thorlabs dans la V1.5

La V1.5 fonctionne avec des lentilles de substitution. Je veux maintenant remplacer ces lentilles fictives par les trois doublets réels de mon montage.

Tu dois utiliser les prescriptions ci-dessous. Elles proviennent des tableaux et dessins techniques Thorlabs.

## 1. Longueur d'onde

Longueur d'onde de simulation :

\[
\lambda_0=1030\ \mathrm{nm}.
\]

Indices calculés à cette longueur d'onde à partir des équations de dispersion SCHOTT :

- N-LAK22 : 1.637961
- N-BAF10 : 1.654584
- N-SF6HT : 1.774338

Ces valeurs correspondent à une température proche de 20 °C.

Ne remplace pas ces valeurs par les indices à 587.6 nm ou par les indices indiqués à une autre longueur d'onde.

## 2. AC254-040-B-ML

Collimateur convergent :

- diamètre : 25.4 mm
- R1 = +26.12 mm
- R2 = -21.28 mm
- R3 = -137.09 mm
- tc1 = 10.0 mm
- tc2 = 2.5 mm
- verre 1 : N-BAF10
- verre 2 : N-SF6HT
- EFL nominale : 40 mm
- BFL nominale : 32.8 mm
- ouverture claire : supérieure à 22.86 mm pour la version montée.

## 3. ACN127-030-B

Doublet divergent :

- diamètre : 12.7 mm
- R1 = -19.25 mm
- R2 = +18.41 mm
- R3 = +106.41 mm
- tc1 = 1.5 mm
- tc2 = 2.5 mm
- verre 1 : N-LAK22
- verre 2 : N-SF6HT
- EFL nominale : -30 mm
- BFL nominale : -32.0 mm
- ouverture claire indicative : supérieure à 11.43 mm.

## 4. AC254-060-B

Doublet convergent :

- diamètre : 25.4 mm
- R1 = +39.48 mm
- R2 = -33.00 mm
- R3 = -165.20 mm
- tc1 = 6.0 mm
- tc2 = 1.7 mm
- verre 1 : N-LAK22
- verre 2 : N-SF6HT
- EFL nominale : 60 mm
- BFL nominale : 55.8 mm
- ouverture claire indicative : supérieure à 22.86 mm.

## 5. Vérification géométrique obligatoire

Les rayons et épaisseurs sont donnés dans l'ordre des surfaces du constructeur :

air → R1 → verre 1 → R2 → verre 2 → R3 → air.

Vérifie que la construction de la classe Lens respecte exactement cette séquence.

Vérifie en particulier que :

- tc1 est bien l'épaisseur centrale du premier verre ;
- tc2 est bien l'épaisseur centrale du second verre ;
- R2 correspond à l'interface cimentée ;
- les indices sont affectés aux bons matériaux ;
- les conventions de signe des rayons sont compatibles avec celles du moteur.

Consulte les dessins techniques Thorlabs si nécessaire. Ne mesure pas les rayons sur une image lorsque les valeurs numériques sont déjà données dans les tableaux constructeur.

Ne confonds pas le diamètre mécanique et l'ouverture claire.

## 6. Organisation des données

Centralise les prescriptions dans `examples/lens_data.py` ou dans un module de données dédié.

Chaque lentille doit conserver :
- sa référence constructeur ;
- ses paramètres géométriques ;
- ses matériaux ;
- ses indices ;
- sa longueur d'onde de référence ;
- ses ouvertures ;
- ses références documentaires.

Les exemples doivent instancier les classes génériques à partir de ces données.

Ne hard-code aucune propriété particulière des trois références dans le moteur.

## 7. Orientation des lentilles

Commence par construire chaque lentille dans l'orientation du dessin constructeur.

Le retournement doit ensuite être géré uniquement par le paramètre `flip` déjà implémenté.

Teste les deux orientations pour les trois lentilles. Ne suppose pas que l'orientation optimale est nécessairement celle que nous avions choisie intuitivement.

Compare notamment :
- EFL ;
- BFL ;
- aberration sphérique ;
- dispersion angulaire ;
- clipping.

## 8. Validation

Pour chaque lentille, compare le résultat paraxial du modèle aux spécifications constructeur.

Les valeurs nominales de focale et de BFL servent de références de contrôle, pas de paramètres imposés au modèle.

Explique les éventuelles différences liées à la longueur d'onde de simulation et aux indices utilisés.

Ajoute des tests de cohérence géométrique et vérifie que les 58 tests précédents passent toujours.

## 9. Rapport final

Présente :
- les prescriptions effectivement intégrées ;
- les sources constructeur utilisées ;
- les orientations testées ;
- les EFL et BFL obtenues à 1030 nm ;
- les écarts par rapport aux spécifications nominales ;
- les éventuelles ambiguïtés restantes.

Ne conserve aucune lentille de substitution dans le scénario principal une fois les trois prescriptions intégrées.