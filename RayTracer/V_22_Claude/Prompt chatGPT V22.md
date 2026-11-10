# V2.2 — Nouvelle chaîne optique et étude complète du front d'onde

La V2.1 du simulateur est maintenant validée sur la chaîne précédente, avec 89 tests passants et une analyse complète de la puissance, du clipping, de l'OPD et du Strehl.

Je veux maintenant remplacer la chaîne optique par la suivante, à 1030 nm :

**Fibre → AC254-040-B → ACN254-040-B → AC254-080-B**

La première lentille **AC254-040-B reste inchangée** par rapport à la V2.1.

Les deux autres lentilles sont remplacées :

- ancien divergent : ACN127-030-B, f ≈ −30 mm, Ø12.7 mm
- nouveau divergent : **ACN254-040-B, f = −40 mm, Ø25.4 mm**
- ancien positif : AC254-060-B, f ≈ +60 mm
- nouveau positif : **AC254-080-B, EFL = +80.3 mm, Ø25.4 mm**

L'objectif est de refaire l'étude complète de la chaîne et de déterminer si cette nouvelle combinaison donne un meilleur faisceau et/ou un meilleur front d'onde.

---

## 1. Prescriptions optiques à utiliser

Ne réutilise pas les prescriptions des anciennes lentilles en changeant simplement leur focale.

Chaque lentille doit être définie à partir de sa prescription réelle.

### AC254-040-B — collimateur

Conserver exactement les données de la V2.1 :

- diamètre : 25.4 mm
- EFL nominale : +40.0 mm
- BFL nominale : 32.8 mm
- R1 = +26.12 mm
- R2 = −21.28 mm
- R3 = −137.09 mm
- tc1 = 10.0 mm
- tc2 = 2.5 mm
- verres : N-BAF10 / N-SF6HT
- ouverture claire conservatrice : 22.86 mm

### ACN254-040-B — nouveau divergent

Utiliser la prescription constructeur :

- diamètre : 25.4 mm
- EFL nominale : −40.0 mm
- BFL nominale : −43.4 mm
- R1 = −24.43 mm
- R2 = +27.86 mm
- R3 = +332.30 mm
- tc1 = 2.0 mm
- tc2 = 4.0 mm
- verres : N-BAF10 / N-SF6HT
- ouverture claire conservatrice : 22.86 mm

La fiche constructeur donne bien cette géométrie pour l'ACN254-040-B.

### AC254-080-B — nouveau positif

Utiliser la prescription constructeur :

- diamètre : 25.4 mm
- EFL nominale : +80.3 mm
- BFL nominale : 73.5 mm
- R1 = +38.7 mm
- R2 = −43.2 mm
- R3 = +374.0 mm
- tc1 = 6.6 mm
- tc2 = 2.0 mm
- verres : N-BAF10 / N-SF6HT
- ouverture claire conservatrice : 22.86 mm

Attention : l'EFL constructeur est 80.3 mm, pas exactement 80 mm. Ne remplace pas la prescription par une lentille mince de focale 80 mm.

---

## 2. Indices à 1030 nm

Conserver la table de matériaux déjà utilisée en V2.1.

À 1030 nm :

- N-BAF10 : n = 1.654584
- N-SF6HT : n = 1.774338

Les trois lentilles de cette nouvelle chaîne utilisent donc la combinaison :

N-BAF10 / N-SF6HT.

Les indices doivent rester associés aux noms de matériaux et non aux références de lentilles.

Ne duplique pas les valeurs d'indice dans chaque entrée de lentille.

---

## 3. Vérification préalable de la géométrie

Avant toute optimisation, ajoute des tests de cohérence spécifiques aux trois nouvelles prescriptions.

Pour chaque lentille, vérifier :

1. séquence :
   air → R1 → verre 1 → R2 → verre 2 → R3 → air ;

2. épaisseurs et rayons avec la convention de signe actuelle ;

3. épaisseur au bord calculée ;

4. EFL obtenu par le modèle à 1030 nm ;

5. BFL obtenu par le modèle à 1030 nm ;

6. cohérence avec les valeurs constructeur.

La convention de signe doit rester celle du moteur existant.

Teste également chaque lentille dans les deux orientations avec `flip=False` et `flip=True`.

Ne suppose pas à l'avance quelle orientation est optimale.

---

# 4. Refaire l'étude d'orientation complète

Il y a maintenant 2³ = 8 orientations possibles.

Pour chacune :

- AC254-040-B : orientation 1 ou 2 ;
- ACN254-040-B : orientation 1 ou 2 ;
- AC254-080-B : orientation 1 ou 2.

Pour chacune des huit configurations, réoptimise la position de la fibre.

Ne réutilise pas automatiquement la position optimale de la V2.1.

La position de fibre doit être optimisée indépendamment pour chaque configuration.

Calcule au minimum :

- divergence RMS ;
- divergence RMS par axe ;
- diamètre de sortie ;
- transmission totale ;
- puissance perdue à chaque surface ;
- OPD RMS ;
- OPD PV ;
- Strehl ;
- éventuel défocus résiduel ;
- position du plan de référence.

Présente ensuite un classement des huit configurations.

---

# 5. Refaire l'étude du collimateur

Pour l'AC254-040-B seule, conserver la procédure de la V2.1.

Déterminer :

- position paraxiale de la fibre ;
- position optimisée pour divergence minimale ;
- position optimisée pour OPD minimal ;
- divergence minimale ;
- diamètre du faisceau ;
- OPD RMS ;
- Strehl.

Ne suppose pas que l'optimum de divergence et l'optimum de front d'onde sont identiques.

---

# 6. Refaire l'étude du nouveau beam expander

La nouvelle paire est :

ACN254-040-B → AC254-080-B.

Le grandissement paraxial attendu est approximativement :

\[
G=-\frac{80.3}{-40.0}\approx2.0075.
\]

Mais le modèle doit utiliser les EFL réellement calculées à 1030 nm plutôt que cette approximation.

Déterminer :

- séparation afocale entre sommets ;
- séparation entre plans principaux ;
- grandissement paraxial ;
- grandissement réellement obtenu par ray tracing ;
- position des plans principaux ;
- divergence résiduelle ;
- aberrations introduites par le beam expander.

Ne suppose pas que la séparation mécanique est simplement :

\[
40+80.3=120.3\ \mathrm{mm}.
\]

La séparation entre sommets et la séparation entre plans principaux doivent être distinguées explicitement.

---

# 7. Clipping

C'est un point important car le divergent passe maintenant de Ø12.7 mm à Ø25.4 mm.

L'ouverture claire conservatrice de l'ACN254-040-B est donc beaucoup plus grande que celle de l'ancien ACN127.

Refais intégralement le bilan de puissance.

Pour chaque surface avec ouverture finie, calculer :

- puissance incidente ;
- puissance transmise ;
- puissance perdue ;
- transmission cumulée ;
- rayon RMS ;
- D4σ ;
- diamètre 1/e² lorsque le profil reste suffisamment gaussien.

Ne suppose pas que la formule analytique gaussienne est valable après une troncature.

Continue d'utiliser la règle de la V2.1 :

\[
T=1-\exp\left(-2a^2/w^2\right)
\]

uniquement lorsque les hypothèses sont vérifiées.

Effectue également une étude de convergence avec le nombre de rayons.

---

# 8. Front d'onde

Refaire exactement l'analyse géométrique de front d'onde de la V2.1, mais avec la nouvelle chaîne.

Pour chaque configuration, calculer :

\[
OPL=\sum_i n_i L_i
\]

puis :

\[
OPD_i=OPL_i-OPL_{\mathrm{ref}}.
\]

Pour un faisceau collimaté, utiliser une référence plane.

Pour un faisceau convergent/divergent, utiliser une référence sphérique centrée sur le point image de référence.

Calculer :

\[
\phi_i=\frac{2\pi}{\lambda_0}OPD_i.
\]

Puis :

- OPD RMS pondéré par puissance ;
- OPD RMS avec pupille uniforme ;
- OPD PV ;
- défocus ;
- OPD RMS après retrait du défocus ;
- Strehl ;
- Strehl avant/après retrait du défocus.

Le Strehl doit être calculé à partir de l'amplitude, donc avec une pondération proportionnelle à √P pour chaque élément de champ discret.

Vérifie la convergence du Strehl avec le nombre de rayons.

---

# 9. Attention aux conventions de diamètre et divergence

La V2.1 a montré que plusieurs définitions du diamètre peuvent diverger après clipping.

Il faut donc conserver séparément :

### Méthode A
Rayons marqueurs / enveloppe géométrique.

### Méthode B
D4σ au sens ISO.

### Méthode C
Ajustement gaussien.

Ne donne jamais un unique « diamètre du faisceau » sans préciser la définition.

De même, distingue explicitement :

- divergence radiale RMS ;
- divergence RMS par axe ;
- divergence du paramètre gaussien ;
- divergence de diffraction d'un faisceau gaussien idéal.

Vérifie soigneusement les facteurs √2 et 2 dans toutes les relations entre :

- waist ;
- diamètre 1/e² ;
- variance ;
- D4σ ;
- divergence.

Une incohérence de facteur 2 avait été identifiée dans l'analyse précédente : ne réutilise aucun résultat de ce type sans le recalculer.

---

# 10. Comparaison avec la chaîne précédente

Une fois les calculs terminés, comparer directement :

### Ancienne chaîne

AC254-040-B → ACN127-030-B → AC254-060-B

### Nouvelle chaîne

AC254-040-B → ACN254-040-B → AC254-080-B

Comparer au minimum :

| Grandeur | Ancienne | Nouvelle |
|---|---:|---:|
| diamètre avant expander | | |
| diamètre après expander | | |
| grandissement | | |
| divergence RMS | | |
| transmission | | |
| perte au divergent | | |
| OPD RMS | | |
| OPD PV | | |
| Strehl | | |
| position optimale de fibre | | |

L'objectif est de déterminer si le passage à :

- divergent Ø1" ;
- f = −40 mm ;
- positif f = +80.3 mm

améliore réellement la qualité optique ou s'il ne fait que modifier le diamètre et la géométrie du faisceau.

---

# 11. Point particulièrement important : ne pas confondre optimisation géométrique et diffraction

Pour cette V2.2, reste dans le même cadre géométrique que la V2.1.

Le but est de répondre à :

> Quelle qualité de front d'onde produit cette nouvelle chaîne avant propagation ondulatoire ?

Ne simule pas encore les anneaux de diffraction.

En revanche, calcule les paramètres permettant de préparer cette étape :

- profil transverse de puissance ;
- profil d'amplitude ;
- OPD(x,y) ;
- phase ;
- diamètre effectif ;
- ouverture effective ;
- éventuelle troncature.

Ces données serviront ensuite de champ complexe d'entrée pour une simulation de propagation par FFT/angular spectrum.

---

# 12. Tests

Conserver tous les tests de la V2.1.

Ajouter au minimum :

- prescription exacte ACN254-040-B ;
- prescription exacte AC254-080-B ;
- EFL/BFL des deux nouvelles lentilles ;
- test des deux orientations de chaque nouvelle lentille ;
- cohérence du grandissement proche de 2 ;
- cohérence de la séparation afocale ;
- conservation de puissance sans clipping ;
- convergence du clipping ;
- convergence de l'OPD ;
- convergence du Strehl ;
- invariance de l'OPD à l'ajout d'une constante aux OPL ;
- retour inverse de la lumière ;
- cohérence de l'eikonale.

---

# 13. Rapport final attendu

Je veux un rapport permettant de répondre clairement à ces questions :

1. Quelle est l'orientation optimale des trois lentilles ?
2. Où faut-il placer la fibre ?
3. Quel diamètre obtient-on avant et après le beam expander ?
4. Quel est le grandissement réel ?
5. Quelle est la divergence résiduelle ?
6. Quelle puissance est perdue par clipping ?
7. Quel est l'OPD RMS ?
8. Quel est l'OPD PV ?
9. Quel est le Strehl ?
10. Quelle partie de l'aberration provient du collimateur ?
11. Quelle partie provient du beam expander ?
12. La nouvelle chaîne est-elle meilleure ou pire que l'ancienne ?
13. Quel est le principal avantage physique du passage à l'ACN254-040-B ?
14. Quel est le principal inconvénient éventuel ?
15. La nouvelle chaîne est-elle suffisamment proche d'un faisceau gaussien pour passer à une propagation ondulatoire ?

Ne modifie pas silencieusement les conventions physiques de la V2.1.

Si une grandeur de la V2.1 était ambiguë ou incorrecte, corrige-la explicitement et indique pourquoi.

**Priorité : exactitude physique et traçabilité des résultats, pas quantité de fonctionnalités.**