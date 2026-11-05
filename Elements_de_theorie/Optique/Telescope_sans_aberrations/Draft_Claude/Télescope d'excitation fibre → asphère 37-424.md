# Télescope d'excitation fibre → asphère 37-424

Nov 5, 2026 · @Paul

## 1. Résumé exécutif

**Décision : collimateur triplet Thorlabs TC25APC-1064 (Ø 5,49 mm) + télescope galiléen ×2 à deux singulets N-BK7 (LC1582-C f = −75 mm, puis LA1433-C f = +150 mm), longueur optique ≈ 80 mm, lentille L1 montée coulissante sur rails de cage 30 mm.** Le faisceau arrive sur l'asphère avec un diamètre 1/e² de 10 à 11 mm, pas 1".

- **Le « 1" » est à abandonner.** L'asphère 37-424 fait Ø 20 mm avec une ouverture utile de 18 mm. Un faisceau de 25,4 mm (1/e²) y perdrait 37 % de sa puissance par clipping. La cible pertinente est un diamètre 1/e² de 10–12 mm (a/w = 1,5–1,8, pertes < 1 %).
- **Le télescope retenu est quasi parfait** : tracé de rayons réel des lentilles catalogue à 1064 nm → 0,015 λ RMS (λ/65), Strehl 0,99. Il ne dégrade pas le faisceau.
- **Piège évité** : la règle n'est pas « le plus gros collimateur = le télescope le plus facile ». L'aberration sphérique d'un singulet varie comme h⁴/f³. Un ×1,5 « compact » (−50/+75 mm) donne 0,12 λ RMS (Strehl 0,73). Il faut f₂ ≥ 150 mm pour un faisceau de sortie de 11–12 mm.
- **Le vrai point faible est l'asphère finale, pas le télescope.** La 37-424 est conçue à 587,6 nm (N-SF6). Utilisée à 1064 nm, mon modèle prédit 0,24 λ RMS d'aberration sphérique pour un faisceau de 11 mm (Strehl 0,28). C'est 16 fois plus que le télescope.
- **Le télescope sert donc aussi de correcteur** : en raccourcissant l'espacement L1–L2 d'environ 42 mm, le faisceau devient légèrement divergent (R ≈ 0,4–0,5 m) et compense l'essentiel de cette aberration : 0,068 λ RMS au foyer, Strehl 0,90, diamètre ≈ 10 mm sur l'asphère. D'où la L1 coulissante.
- **Solution de repli la plus simple** : un faisceau de 8 mm sans compensation (F810APC-1064 seul, sans télescope) donne déjà un Strehl de 0,89 au foyer, au prix d'un spot \~1,35× plus gros (w ≈ 1,3 µm au lieu de ≈ 1,0 µm).

Tous les chiffres de front d'onde de ce document viennent d'un tracé de rayons 3D écrit pour l'occasion (surfaces réelles, indices Sellmeier, poids gaussien) ; les hypothèses sont signalées là où elles comptent.

## 2. Données des trois collimateurs

Les « waists » de 5,5 / 4,05 / 8,00 mm de tes notes sont en fait des **diamètres 1/e²** (Thorlabs : « Waist Diameter », 1/e², calculé à 1064 nm pour une fibre de MFD ≈ 6,2 µm). Toute la suite utilise le diamètre 1/e² D = 2w.

| Collimateur | Optique | f (mm) | NA lentille | D 1/e² (mm) | Distance du waist (mm, depuis la face) | Divergence pleine (°) | Traitement AR | Connecteur | Encombrement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [TC25APC-1064](https://www.gophotonics.com/products/collimators/thorlabs-inc/50-46-tc25apc-1064) | triplet espacé | 25,23 | 0,25 | 5,49 | 17,29 | 0,014 | plage d'usage 1035–1097 nm | FC/APC (TC25FC : FC/PC) | L = 43,3 mm |
| [F280APC-1064](https://www.thorlabs.com/fixed-focus-collimation-packages-fcapc-connectors?pn=F280APC-A) | asphère singulet moulée | 18,60 | 0,15 | 4,05 | 17,86 | 0,02 (+0,01/−0) | 650–1050 nm, Ravg < 0,5 % | FC/APC | Ø 11 mm, M11×0,5 |
| [F810APC-1064](https://www.thorlabs.com/air-spaced-doublet-collimators-fcapc-fcpc-sma) | doublet espacé | 36,60 | 0,25 | 8,00 | 36,66 | 0,010 (+0,010/−0) | 1050–1074 nm, Ravg < 0,25 % | FC/APC | L = 47,0 mm |

Ce que la fiche ne dit pas : aucun des trois ne donne de M² chiffré ni d'erreur de front d'onde chiffrée. Thorlabs indique seulement que les triplets ont un M² plus proche de 1 et moins d'erreur de front d'onde que les collimateurs asphériques ([page triplets](https://www.thorlabs.com/triplet-fiber-optic-collimatorscouplers-)). Je suppose M² = 1 (fibre monomode) dans les calculs.

Trois différences qui comptent pour la suite :

- **F280APC-1064 : traitement AR qui s'arrête à 1050 nm**, donc 1064 nm est hors bande, et son ouverture (NA 0,15, soit Ø ≈ 5,6 mm) **tronque** le mode de fibre (section 3).
- **F810APC-1064 : AR en V très étroit (1050–1074 nm)**. Si la longueur d'onde finale est 1000 ou 1100 nm, il est inadapté.
- **TC25 : la plage 1035–1097 nm** est la plus large des trois autour de 1064 nm. Attention au connecteur : TC25**FC** est FC/PC ; si ta jarretière est FC/APC, prends TC25**APC**-1064 (mêmes optiques ; les caractéristiques ci-dessus sont celles de la version APC).

## 3. Caractérisation du faisceau gaussien

Les trois faisceaux sont collimatés sur des dizaines de mètres : leur longueur de Rayleigh dépasse 12 m, donc la position exacte du waist n'a aucune importance sur une table optique. Convention : w = rayon 1/e² en intensité, D = 2w, θ = demi-angle de divergence 1/e², M² = 1.

```latex
z_R = \frac{\pi w_0^2}{\lambda}, \qquad \theta = \frac{\lambda}{\pi w_0}, \qquad w(z) = w_0\sqrt{1+\left(\frac{z-z_0}{z_R}\right)^2}, \qquad \frac{1}{q(z)} = \frac{1}{R(z)} - i\,\frac{\lambda}{\pi w(z)^2}
```

| Collimateur | w₀ (mm) | z\_R (m) | θ (µrad) | D à 0,5 / 1 / 2 m (mm) | MFD fibre déduit (µm) | a/w dans le collimateur | Puissance transmise |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TC25APC-1064 | 2,745 | 22,2 | 123 | 5,491 / 5,496 / 5,512 | 6,23 | 2,30 | ≈ 100 % |
| F280APC-1064 | 2,025 | 12,1 | 167 | 4,053 / 4,064 / 4,105 | 6,22 | 1,38 | 97,5 % |
| F810APC-1064 | 4,000 | 47,2 | 85 | 8,000 / 8,002 / 8,007 | 6,20 | 2,29 | ≈ 100 % |

Distances comptées depuis le waist. Le waist est au plan focal avant de chaque collimateur (17–37 mm devant la face, cf. tableau 2) ; à l'échelle de z\_R, c'est « à la sortie du collimateur ».

**Troncature dans le F280.** Le mode de fibre a une ouverture 1/e² NA = λ/(π·w\_fibre) ≈ 0,109. La lentille du F280 (NA 0,15) ne couvre que 1,38 w : 2,5 % de la puissance est coupée par un bord dur. Ce n'est pas une perte de puissance gênante, mais ce bord dur produit des anneaux de diffraction faibles et rend le faisceau non strictement gaussien. TC25 et F810 (NA 0,25, a/w ≈ 2,3) ne tronquent rien de mesurable.

**Le waist de plusieurs millimètres rend-il le télescope plus facile ?** Pour la propagation, oui : le faisceau est collimaté partout et un télescope afocal multiplie z\_R par M², donc la position du waist reste sans importance après le télescope. Pour les aberrations, non : ce qui compte est la hauteur du faisceau sur chaque lentille rapportée à sa focale (section 5), pas le waist d'entrée.

**Longueur d'onde (1000 / 1064 / 1100 nm).** D varie peu, car D = 4λf/(π·MFD) et le MFD d'une fibre monomode croît à peu près comme λ. En revanche la focale du collimateur change. Pour un singulet de dispersion type N-BK7 (hypothèse ; Thorlabs ne donne pas le verre du F280), le décalage de foyer vaut −32 µm à 1000 nm et +17 µm à 1100 nm pour f = 18,6 mm. C'est du même ordre que la longueur de Rayleigh côté fibre (≈ 30 µm) : le faisceau sort alors nettement convergent ou divergent. Le télescope recollimate cela en ajustant son espacement d'environ −0,13 à +0,07 mm (section 7). Triplet et doublet sont partiellement corrigés du chromatisme, donc moins touchés.

## 4. Détermination du diamètre final nécessaire

**Diamètre retenu : D(1/e²) ≈ 10–11 mm sur l'asphère.** Il découle de l'ouverture utile de 18 mm et de l'aberration de la 37-424 à 1064 nm, pas d'une valeur « 1" » : 1" vaut 25,4 mm, plus que le diamètre de la lentille elle-même (et la mention « 20 cm » de tes notes est sans doute un « 20 mm », le diamètre de la lentille).

**Fiche Edmund #37-424** ([page produit](https://www.edmundoptics.com/p/20mm-dia-067-numerical-aperture-uncoated-high-precision-aspheric-lens/44551/), [fiche FR](https://www.edmundoptics.fr/p/20mm-dia-067-numerical-aperture-uncoated-inked-high-precision-aspheric-lens/45389/)) :

| Paramètre | Valeur catalogue |
| --- | --- |
| Diamètre | 20,00 +0/−0,025 mm |
| Ouverture utile (CA) | 18,00 mm |
| EFL | 15,00 mm à 587,6 nm (≈ 15,6 mm à 1064 nm, calculé) |
| BFL | 8,12 mm à 587,6 nm |
| NA ; f/# | 0,67 ; 0,75 |
| Épaisseurs | CT 12,42 ± 0,10 mm ; ET 7,97 mm ; face arrière plane |
| Matériau | N-SF6 (n = 1,8052 à 587,6 nm ; 1,7733 à 1064 nm, Sellmeier) |
| Longueur d'onde de conception de l'asphère | 587,6 nm |
| Erreur de forme asphérique | 0,4λ RMS à 632,8 nm |
| Centrage ; qualité de surface | < 3 arcmin ; 40-20 |
| Traitement ; plage | aucun ; 390–2500 nm |
| Prix | 295 € (version encrée -INK, FR) ; 349 $ (US) |

La fiche ne donne ni diamètre de faisceau recommandé, ni aberration résiduelle hors de 587,6 nm. Trois conséquences directes :

- **Non traitée = 7,8 % de réflexion par face à 1064 nm** (Fresnel, n = 1,773), soit \~15 % de perte et des reflets renvoyés vers le télescope et la fibre. La même lentille existe traitée : #23-013 (SWIR+, 900–1700 nm, couvre 1000–1100 nm) et #22-999 (NIR+, 600–1050 nm, s'arrête avant 1064) ([famille Edmund](https://www.edmundoptics.com/f/PdfExport/39674)). Je recommande la #23-013.
- **L'erreur de forme de 0,4λ RMS (253 nm) est énorme à l'échelle du télescope.** Lue comme erreur de front d'onde, c'est 0,24 λ RMS à 1064 nm (Strehl ≈ 0,1 sur toute l'ouverture). Lue comme erreur de surface, ×(n−1) ≈ 0,77 → 0,18 λ (Strehl ≈ 0,27). La fiche ne dit pas laquelle, ni comment elle se répartit : sur un faisceau de 10 mm au centre d'une ouverture de 18 mm, elle sera probablement bien plus faible, mais je ne peux pas le chiffrer. À mesurer (section 15).
- **Conçue à 587,6 nm, elle est sphériquement aberrante à 1064 nm** (section 7) : c'est ce qui borne le diamètre utile.

**Faisceau gaussien et clipping.** Pour un faisceau de rayon w sur une pupille de rayon a = 9 mm :

```latex
T = 1 - e^{-2a^2/w^2}, \qquad \frac{I_\mathrm{pic}}{I_\mathrm{Airy}} = \frac{2\left(1-e^{-a^2/w^2}\right)^2}{(a/w)^2}, \qquad w_\mathrm{foyer} \approx \frac{\lambda f}{\pi w}
```

| D 1/e² (mm) | a/w | Transmis | Pic focal / Airy uniforme | w au foyer, paraxial (µm) | Strehl 37-424 à 1064 nm, sans compensation | avec compensation par divergence |
| --- | --- | --- | --- | --- | --- | --- |
| 8 | 2,25 | 100,0 % | 0,39 | 1,32 | 0,89 | 0,99 |
| 11 | 1,64 | 99,5 % | 0,65 | 0,96 | 0,28 | 0,91 |
| 12 | 1,50 | 98,9 % | 0,71 | 0,88 | 0,12 | 0,86 |
| 14 | 1,29 | 96,3 % | 0,79 | 0,76 | ≈ 0,01 | 0,78 |
| 16 | 1,12 | 92,0 % | 0,82 (max) | 0,66 | ≈ 0,02 | 0,72 |
| 18 (= CA) | 1,00 | 86,5 % | 0,80 | 0,59 | — | — |
| 25,4 (1") | 0,71 | 63,4 % | 0,62 | 0,42 | — | — |

Lecture : sans aberration, le pic focal serait maximal pour a/w = 1,12 (D ≈ 16 mm), mais avec bord dur et anneaux. Avec l'aberration réelle de la 37-424 à 1064 nm, un grand faisceau est pénalisé lourdement. **Sans compensation, le meilleur choix est D ≈ 8 mm. Avec compensation (L1 coulissante), D ≈ 10–11 mm** donne le spot le plus petit qui reste propre (Strehl ≥ 0,9) et un clipping < 0,5 %. Au-delà de NA ≈ 0,3 le w paraxial n'est qu'indicatif.

## 5. Dimensionnement du beam expander

**Grossissements retenus : ×2 pour le TC25 (5,49 → 11,0 mm), ×3 pour le F280 (4,05 → 12,2 mm), ×1,5 pour le F810 (8,0 → 12,0 mm), avec dans les trois cas une L2 de f = +150 mm.**

**Ce que signifie M pour un faisceau gaussien.** Un télescope afocal transforme le paramètre q d'un facteur M² exactement : w → M·w, z\_R → M²·z\_R, θ → θ/M. Le rapport M = D\_out/D\_in est donc exact en convention 1/e², sans facteur de forme, tant qu'aucune lentille ne tronque. Le calcul « 8 → 25 mm = ×3,1 » est faux non pas par la formule mais par la cible : 25 mm de diamètre 1/e² ne passe pas dans une ouverture de 18 mm.

**Marge avant clipping, à chaque optique.** Règle retenue : a/w ≥ 2 sur chaque lentille du télescope (perte 3·10⁻⁴, diffraction de bord négligeable) et a/w ≥ 1,6 sur l'asphère (perte < 0,5 %). Avec des lentilles Ø 1" (ouverture utile ≥ 90 % du diamètre, soit 22,9 mm), un faisceau de 11 mm donne a/w = 2,08 sur L2 : Ø 1" suffit, Ø 2" serait superflu.

**Le choix des focales est dicté par l'aberration sphérique, pas par la longueur.** Pour un singulet en faisceau collimaté, le coefficient d'aberration sphérique varie comme :

```latex
W_{040} \propto \frac{h^4}{f^3}
```

h = hauteur du faisceau sur la lentille. À grossissement fixé, multiplier toutes les focales par k divise l'aberration par k³. Le tracé de rayons le confirme :

| Télescope (orientation optimale) | Focales (mm) | Longueur entre sommets (mm) | Front d'onde RMS (λ) | Strehl |
| --- | --- | --- | --- | --- |
| ×1,5 « compact » | −50 / +75 | 20,4 | 0,123 | 0,73 |
| ×1,5 long | −100 / +150 | 46,2 | 0,015 | 0,99 |
| ×2 « compact » | −50 / +100 | 46,2 | 0,053 | 0,93 |
| ×2 long | −75 / +150 | 72,0 | 0,015 | 0,99 |
| ×3 | −50 / +150 | 99,8 | 0,013 | 0,99 |

À diamètre de sortie identique (11–12 mm), c'est **f₂ qui fixe la qualité** : avec f₂ = 150 mm, les trois scénarios tombent à λ/65–λ/75. Le collimateur ne change plus que la longueur : 46 mm (F810), 72 mm (TC25), 100 mm (F280).

## 6. Comparaison Keplerien / Galiléen / asphériques

**Architecture retenue : galiléen à deux singulets sphériques.** À focales comparables il est 3 à 10 fois moins aberrant que le keplerien, 2 à 3 fois plus court, sans foyer interne, et une asphère n'y apporterait rien de mesurable.

**A. Keplerien (deux convergentes, L ≈ f₁ + f₂).** Les deux lentilles ont une aberration sphérique de même signe, qui s'additionne. Tracé : ×1,5 avec f = +50 / +75 → 0,63 λ RMS ; ×3 avec +50 / +150 → 0,061 λ, contre 0,013 λ en galiléen avec la même L2. Longueur ≈ 200–225 mm pour ×2–×3. Le foyer interne a un rayon w = λf₁/(πw\_in) ≈ 8–9 µm et z\_R ≈ 0,2 mm : \~9·10⁵ W/cm² par watt, assez pour brûler une poussière. Son seul intérêt serait d'y placer un trou de filtrage spatial, inutile ici : la fibre monomode est déjà un filtre spatial parfait (mode LP₀₁).

**B. Galiléen (divergente + convergente, L ≈ f₂ − |f₁|).** La divergente a une aberration sphérique de signe opposé à la convergente : elles se compensent en partie, ce qui explique les 0,013–0,015 λ obtenus avec de simples plan-concave / plan-convexe. Pas de foyer réel, longueur minimale, et l'espacement L1–L2 est un réglage continu de la vergence de sortie (indispensable ici, section 7).

**C. Asphères dans le télescope.** Elles ne peuvent gagner que ce qui reste, soit ≤ 0,015 λ RMS (≈ 1 % de Strehl). En contrepartie :

- **Erreur de forme supérieure au gain.** Une asphère polie Edmund « Precision » est spécifiée à 0,4λ RMS (633 nm) ; un singulet sphérique Thorlabs à λ/4 d'irrégularité crête-crête par face (633 nm), soit ≈ 0,02 λ RMS par face à 1064 nm transmis, encore moins sur les 11 mm centraux. La sphère est meilleure que l'asphère qu'on lui substituerait.
- **Sensibilité au centrage bien plus forte** : une asphère décentrée produit directement de la coma ; un singulet sphérique décentré produit surtout un dépointage (section 8).
- Coût ×10 à ×20.

Conclusion : pas d'asphère dans le télescope ; l'asphère est déjà en bout de chaîne, et c'est elle qui limite.

**Par type d'aberration, sur l'axe :**

- **Sphérique** : seule aberration non nulle d'un télescope centré ; chiffrée ci-dessus et section 7.
- **Coma, astigmatisme** : nulles par symétrie de révolution ; n'apparaissent qu'avec un tilt ou un décentrement de lentille (section 8) ou un faisceau incliné sur l'asphère.
- **Chromatisme** : laser monochromatique, donc pas de flou chromatique ; un changement de λ décale seulement la collimation (réglé par l'espacement).
- **Hors axe** : un faisceau collimaté incliné de 10 mrad sur la 37-424 dégrade le front d'onde de 0,075 à 0,077 λ RMS (tracé) — négligeable ; un décentrement de 1 mm, de 0,075 à 0,103 λ — à éviter.
- **Propre au gaussien** : le bord de pupille pèse peu (intensité e⁻² à r = w), donc l'aberration effective est plus faible qu'en éclairage uniforme ; c'est pourquoi tous les RMS de ce document sont pondérés par l'intensité gaussienne et le « Strehl » est le recouvrement du champ aberré avec le champ parfait.

| Architecture | Avantages | Inconvénients | Aberrations (×2–×3, f₂ = 150) | Longueur | Alignement | Recommandation |
| --- | --- | --- | --- | --- | --- | --- |
| Galiléen 2 singulets sphériques | compensation partielle de l'aberration sphérique ; pas de foyer ; réglage de vergence continu | aucun notable | 0,013–0,015 λ RMS | 46–100 mm | facile (2 lentilles en cage) | **retenu** |
| Keplerien 2 singulets | foyer accessible (filtrage, repère) | aberrations additives ; foyer intense ; long | 0,06 λ (×3) à 0,6 λ (×1,5) | 200–225 mm | moyen | non |
| Galiléen avec asphère(s) | aucun gain mesurable | erreur de forme > gain ; coma au décentrement ; coût | ≥ erreur de forme (\~0,2 λ possible) | idem | délicat | non |

## 7. Analyse détaillée des aberrations

**Le télescope retenu introduit 0,015 λ RMS (λ/65) à 1064 nm, cinq fois sous le critère de Maréchal (0,071 λ, Strehl 0,8). L'asphère 37-424 utilisée à 1064 nm en introduit 0,24–0,32 λ si on ne fait rien, 0,068 λ si on la compense avec l'espacement du télescope.**

**Méthode.** Tracé de rayons 3D exact (Snell vectoriel) à travers les surfaces catalogue (rayons, épaisseurs, N-BK7 Sellmeier : n = 1,50663 à 1064 nm), environ 11 000 rayons sur r ≤ 2w. Front d'onde = chemin optique sur un plan de sortie, piston/tilts/défocus retirés (le défocus se règle à l'espacement), RMS pondéré par l'intensité gaussienne, Strehl = recouvrement du champ aberré avec le champ parfait. Critère : 0,071 λ RMS ≈ limite de diffraction ; 0,02 λ ≈ indétectable en pratique.

**1. Aberration sphérique et orientation des lentilles.** C'est le seul terme sur l'axe, et l'orientation des faces le change d'un facteur 7 (télescope ×2, LC1582-C + LA1433-C) :

| L1 (−75) : face courbe tournée vers | L2 (+150) : face courbe tournée vers | RMS (λ) | Strehl |
| --- | --- | --- | --- |
| la fibre | l'asphère | 0,015 | 0,991 |
| l'asphère | l'asphère | 0,029 | 0,972 |
| l'asphère | la fibre | 0,062 | 0,908 |
| la fibre | la fibre | 0,106 | 0,786 |

Règle : **les deux faces courbes vers l'extérieur, faces planes en regard** (L1 : face concave vers le faisceau incident ; L2 : face convexe vers le faisceau agrandi). Attention, ce n'est pas universel : pour le ×3 (F280), l'optimum est L1 plane côté fibre (0,013 λ contre 0,031 λ).

**2–3. Coma et astigmatisme.** Nuls par symétrie au nominal. Chiffrés section 8 en fonction des défauts de montage.

**4. Chromatisme.** À espacement figé sur 1064 nm, seul le défocus change ; une fois l'espacement réajusté, il reste 0,017 λ à 1000 nm et 0,015 λ à 1100 nm. Réajustement nécessaire : −0,13 mm (1000 nm) et +0,07 mm (1100 nm) pour le ×2.

**5–6. Diffraction et clipping.** a/w ≥ 2,08 sur toutes les lentilles du télescope : perte ≤ 2·10⁻⁴, aucune diffraction de bord visible. Sur l'asphère, a/w = 1,64–1,8 : perte 0,2–0,5 %.

**7. Déformation du front d'onde par la fabrication — que vaut « λ/4 » à 1064 nm ?** Les singulets Thorlabs sont spécifiés à λ/4 d'irrégularité crête-crête à 633 nm (158 nm) par face. Une erreur de surface h se transmet en (n−1)·h = 80 nm, soit 0,075 λ crête-crête à 1064 nm, soit ≈ 0,015–0,02 λ RMS (rapport crête/RMS typique 3,5–5). Avec quatre faces en somme quadratique, le pire cas reste ≤ 0,04 λ RMS (Strehl ≥ 0,94), et le faisceau de 11 mm n'utilise que le centre de l'ouverture de 22,9 mm. **Acceptable.**

**8–9. Centrage et tilt.** Section 8.

**10. Qualité du faisceau final, de la fibre au foyer.** C'est là que se joue tout. Modèle de l'asphère : la prescription exacte de la 37-424 n'est pas publiée dans les sources que j'ai pu lire (seuls R = 12,08 mm, CT, BFL et le verre le sont). J'ai donc reconstruit une surface parfaite à 587,6 nm (conique k = −0,569 + termes A₄…A₁₀, RMS < 10⁻⁴ λ sur 18 mm à 587,6 nm), puis évalué cette lentille à 1064 nm. L'aberration vient de l'écart d'indice (1,805 → 1,773), donc elle dépend peu des détails du dessin, mais le chiffre exact est à confirmer avec le fichier Zemax d'Edmund.

| Configuration (TC25 + ×2, asphère à 100 mm de L2) | Espacement L1–L2 (mm, sommets) | D sur l'asphère (mm) | RMS au foyer (λ) | Strehl |
| --- | --- | --- | --- | --- |
| Télescope afocal (collimaté) | 72,0 | 11,0 | 0,319 | 0,13 |
| Espacement optimisé (faisceau divergent, R ≈ 0,5 m) | 30,3 | 10,0 | 0,068 | 0,90 |
| Idem, asphère à 50 mm de L2 | 36,7 | ≈ 9,5 | 0,042 | 0,95 |
| Idem, asphère à 200 mm de L2 | 16,1 | ≈ 11 | 0,124 | 0,74 |

Lecture : une faible divergence d'entrée change le conjugué de l'asphère et génère une aberration sphérique de signe opposé à celle due à la longueur d'onde. **Placer l'asphère à ≤ 100 mm de L2** et régler l'espacement sur le foyer.

**Budget d'erreur au foyer (configuration recommandée, RMS en λ à 1064 nm) :**

| Contribution | RMS (λ) | Origine du chiffre |
| --- | --- | --- |
| Collimateur TC25 | non spécifié (« limité par la diffraction » selon Thorlabs) | à mesurer |
| Dessin du télescope | 0,015 | tracé |
| Fabrication des singulets | ≤ 0,04 (pire cas) | λ/4 crête-crête catalogue |
| Asphère : sphérique à 1064 nm, compensée | 0,068 | tracé, surface reconstruite |
| Asphère : erreur de forme 0,4λ RMS @633 | 0 à 0,24 selon interprétation et zone utile | fiche Edmund, ambiguë |

Le télescope n'est donc plus le facteur limitant dès qu'il est dessiné comme ci-dessus ; vouloir mieux que λ/65 n'aurait aucun effet visible au foyer.

## 8. Tolérances et alignement

**Le télescope tolère des défauts de montage grossiers pour le front d'onde (0,5 mm de décentrement, 2° de tilt) ; ce qui doit être soigné, c'est le pointage, l'espacement et le centrage du faisceau sur l'asphère.**

Tracé avec défaut (télescope ×2 TC25, faisceau de sortie 11 mm, défocus et tilt retirés) :

| Défaut | RMS (λ) | Strehl | Dépointage du faisceau |
| --- | --- | --- | --- |
| Nominal | 0,0153 | 0,991 | 0 |
| L2 décentrée 0,1 mm | 0,0155 | 0,991 | 655 µrad |
| L2 décentrée 0,25 mm | 0,0162 | 0,990 | 1,64 mrad |
| L2 décentrée 0,5 mm | 0,0185 | 0,988 | 3,28 mrad |
| L1 décentrée 0,25 mm | 0,0156 | 0,991 | 1,64 mrad |
| L1 tiltée 1° / 2° | 0,016 / 0,022 | 0,990 / 0,982 | 66 / 132 µrad |
| L2 tiltée 1° / 2° / 3° | 0,018 / 0,034 / 0,067 | 0,988 / 0,959 / 0,856 | 58 / 116 / 174 µrad |

Ce qu'il faut en retenir :

- **Décentrement → dépointage, presque pas d'aberration.** Un décentrement δ de L2 incline le faisceau de δ/f₂ (6,6 mrad/mm). Sur l'asphère, 655 µrad déplacent le foyer de ≈ 10 µm latéralement et, à 100 mm, le faisceau de 65 µm. Inoffensif pour la qualité (10 mrad d'incidence sur la 37-424 : 0,075 → 0,077 λ), mais à rattraper par deux miroirs de renvoi.
- **Tilt de L2 : rester sous 1°** (coma + astigmatisme croissent comme le carré du tilt). Une cage 30 mm le garantit sans réglage.
- **Espacement : c'est le réglage fin.** 0,1 mm d'espacement = vergence de 4,3·10⁻⁶ mm⁻¹ (R ≈ 230 m), 0,06 λ de défocus crête-crête sur w, et ≈ 1 µm de déplacement axial du foyer de l'asphère (z\_R au foyer ≈ 2,7 µm). Il faut donc une translation continue au 0,05 mm près sur \~45 mm de course.
- **Centrage du faisceau sur l'asphère : ≤ 0,25 mm.** 0,5 mm de décalage latéral fait passer le Strehl de 0,89 à 0,88 (D = 8 mm), 1 mm à 0,83.

**Montage.** Système de cage 30 mm sur 4 tiges : collimateur dans son adaptateur, L1 dans une plaque de cage coulissante (verrouillable, course libre de 0 à \~80 mm), L2 dans une plaque fixe. La cage assure concentricité et parallélisme ; le seul degré de liberté de réglage est l'espacement L1–L2. Deux miroirs Ø 1" sur montures cinématiques entre L2 et l'asphère (ou entre collimateur et télescope) pour le pointage. Encombrement : \~130 mm de long × 60 mm de côté, hors miroirs.

**Procédure d'alignement :**

1. Monter collimateur + L2 seule ; centrer le faisceau sur deux diaphragmes espacés de ≥ 0,5 m (définit l'axe).
2. Insérer L1, face concave vers la fibre ; la centrer jusqu'à ce que le faisceau ne bouge plus sur les diaphragmes (le dépointage est ×6,6 mrad/mm : très sensible, donc facile).
3. Collimater : faire coulisser L1 jusqu'à ce que le diamètre soit identique à 0,3 m et à 3 m (ou interféromètre à cisaillement). Noter cette position « afocale » (espacement ≈ 72,0 mm entre sommets).
4. Envoyer le faisceau dans l'asphère via les deux miroirs, centré à ≤ 0,25 mm et perpendiculaire (retour du reflet sur lui-même).
5. Raccourcir progressivement l'espacement (≈ −35 à −45 mm selon la distance L2–asphère) en optimisant le spot au foyer : intensité pic sur caméra derrière un objectif, couteau, ou signal d'un émetteur/bille fluorescente. Refaire la mise au point de l'asphère à chaque pas (le foyer s'éloigne de la lentille d'environ 0,47 mm au total : BFL 8,63 → 9,10 mm).

## 9. Composants commerciaux proposés

Toutes les lentilles sont des singulets N-BK7 Thorlabs Ø 1", traitement « -C » (1050–1700 nm, Ravg < 0,5 %), dont j'ai vérifié rayon et épaisseur — ce sont eux qui alimentent le tracé de rayons. Les prix marqués « non vérifié » n'ont pas pu être confirmés en ligne.

| Rôle | Référence | f (mm) | Ø (mm) | Géométrie (mm) | Matériau / AR | Qualité optique | Prix |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Collimateur (retenu) | Thorlabs [TC25APC-1064](https://www.gophotonics.com/products/collimators/thorlabs-inc/50-46-tc25apc-1064) | 25,23 | faisceau 5,49 | L = 43,3 | triplet ; 1035–1097 nm | « M² proche de 1 » (non chiffré) | non vérifié |
| L1 divergente (retenue) | Thorlabs [LC1582-C](https://www.3doptix.com/catalog/optics/lens/thorlabs/LC1582-C) | −75,0 | 25,4 | R = −38,6 ; CT 3,5 ; BFL −77,3 | N-BK7 ; 1050–1700 nm | λ/4 irrégularité, centrage ≤ 3′ (famille) | ≈ 30 $ (catalogue V20 : 17,40 $ + 12,20 $ de traitement, [p. 603](https://thorlabs.com/catalogpages/v20/603.pdf)) |
| L2 convergente (retenue) | Thorlabs [LA1433-C](https://www.gophotonics.com/products/optical-lenses/thorlabs-inc/33-46-la1433-c-ml) | 150,0 | 25,4 | R = 77,3 ; CT 3,1 ; ET 2,0 ; BFL 147,5 | N-BK7 ; 1050–1620/1700 nm | centrage 3′, CA ≥ 90 % | non vérifié |
| Lentille finale (recommandée) | Edmund [#23-013](https://www.edmundoptics.com/f/PdfExport/39674) | 15,0 | 20,0 | identique à #37-424 | N-SF6 ; SWIR+ 900–1700 nm | 0,4λ RMS figure | 379 $ |
| Lentille finale (actuelle) | Edmund [#37-424](https://www.edmundoptics.com/p/20mm-dia-067-numerical-aperture-uncoated-high-precision-aspheric-lens/44551/) | 15,0 | 20,0 | CT 12,42 ; BFL 8,12 | N-SF6 ; non traitée | 0,4λ RMS figure | 349 $ / 295 € (-INK) |
| Variante L1 pour F810 ×1,5 | Thorlabs [LC1120-C](https://3doptix.com/catalog/optics/lens/thorlabs/LC1120-C) | −100,0 | 25,4 | R = −51,5 ; CT 4,0 ; ET 5,6 | N-BK7 ; 1050–1700 nm | λ/4, centrage 3′ ([fiche](https://www.gophotonics.com/products/optical-lenses/thorlabs-inc/33-46-lc1120)) | non vérifié |
| Variante L1 pour F280 ×3 | Thorlabs [LC1715-C](https://www.3doptix.com/catalog/optics/lens/thorlabs/LC1715-C) | −50,0 | 25,4 | R = −25,7 ; CT 3,5 ; ET 6,9 | N-BK7 ; 1050–1700 nm | — | ≈ 30 $ (catalogue V20) |
| Variante L2 si λ ≈ 1000 nm | Thorlabs [LA1433-AB](https://www.3doptix.com/catalog/optics/lens/thorlabs/LA1433-AB) | 150,0 | 25,4 | idem LA1433 | N-BK7 ; 400–1100 nm | — | non vérifié |

Remarques :

- **Traitement selon la longueur d'onde finale.** -C commence à 1050 nm : parfait à 1064 et 1100 nm, pas à 1000 nm. Si λ descend vers 1000 nm, prendre -AB (400–1100 nm) ; je n'ai vérifié l'existence d'un -AB que pour la LA1433, pas pour la LC1582.
- **Pas de télescope commercial tout fait.** Les expanseurs galiléens du commerce ont des grossissements fixes et ne permettent pas le réglage de vergence nécessaire à la compensation de l'asphère. Je ne les ai pas évalués en détail.
- **Mécanique** (non chiffrée, catalogue standard) : 4 tiges de cage 30 mm de 150 mm, 3 plaques de cage à filetage SM1, adaptateur de collimateur adapté au TC25, deux montures cinématiques Ø 1" + miroirs à 1064 nm, éventuellement un diaphragme à iris en cage pour l'alignement.

## 10. Comparaison des trois solutions

**Si je construisais ce montage, je prendrais le TC25APC-1064.** Les trois télescopes optimisés ont la même qualité (λ/65–λ/75) : le choix se fait donc sur le collimateur lui-même, et le TC25 est le seul qui cumule optique la mieux corrigée (triplet), aucune troncature et la plage spectrale la plus large autour de 1064 nm.

| Collimateur | Diamètre 1/e² | Grossissement nécessaire | Télescope proposé | Longueur (sommets L1–L2) | Lentilles | Qualité attendue (télescope seul) | Complexité |
| --- | --: | --: | --- | --: | --: | --- | --- |
| TC25APC-1064 | 5,49 mm | ×2 | LC1582-C + LA1433-C | 72 mm | 2 | 0,015 λ RMS, Strehl 0,99 ; collimateur triplet | faible |
| F810APC-1064 | 8,00 mm | ×1,5 | LC1120-C + LA1433-C | 46 mm | 2 | 0,015 λ RMS, Strehl 0,99 ; collimateur doublet | faible |
| F280APC-1064 | 4,05 mm | ×3 | LC1715-C + LA1433-C | 100 mm | 2 | 0,013 λ RMS, Strehl 0,99 ; mais troncature 2,5 % et AR hors bande | faible, plus long |

Pourquoi pas les deux autres :

- **F810APC-1064, second très proche.** Télescope le plus court, et utilisable seul (sans télescope) pour la solution de repli à 8 mm. Mais son AR en V (1050–1074 nm) le rend inutilisable si la longueur d'onde finale s'écarte de 1064 nm de plus de \~10 nm. **Si λ = 1064 nm est certain, il est aussi bon que le TC25.**
- **F280APC-1064, à écarter.** Asphère moulée unique dont l'AR s'arrête à 1050 nm, ouverture qui coupe le mode à 1,38 w (bord dur, anneaux), chromatisme de singulet, et télescope le plus long (×3).

## 11. Architecture recommandée

**Fibre FC/APC → TC25APC-1064 → L1 = LC1582-C (concave vers la fibre, coulissante) → L2 = LA1433-C (convexe vers l'asphère, fixe) → 2 miroirs → asphère Edmund #23-013 (ou #37-424) à ≤ 100 mm de L2.**

Deux points de fonctionnement, sur le même montage :

- **Mode « afocal » (contrôle)** : espacement 72,0 mm entre sommets. Faisceau collimaté de 11,0 mm, front d'onde λ/65. Sert à vérifier l'alignement et la collimation, et donne le faisceau idéal si l'asphère est un jour remplacée par une optique conçue pour le proche IR.
- **Mode « compensé » (utilisation)** : espacement ≈ 30 mm (−42 mm), faisceau légèrement divergent, D ≈ 10 mm sur l'asphère. Strehl prédit 0,90 au foyer au lieu de 0,13, spot w ≈ 1,0 µm.

Repli si la compensation s'avère peu pratique : F810APC-1064 seul, faisceau de 8 mm directement sur l'asphère (Strehl 0,89, w ≈ 1,3 µm, une seule optique).

## 12. Calculs finaux

**Focales à 1064 nm** (f = R/(n−1), n = 1,50663) : f₁ = −76,19 mm, f₂ = +152,58 mm, M = 2,0026. Les deux lentilles étant du même verre, M ne dépend pas de λ. Séparation afocale des plans principaux f₁ + f₂ = 76,39 mm ; entre sommets réels (tracé, lentilles épaisses) : 72,01 mm.

**Transformation de q par le télescope (lentilles minces).**

```latex
M_\mathrm{tel} = \begin{pmatrix}1&0\\-1/f_2&1\end{pmatrix}\begin{pmatrix}1&f_1+f_2\\0&1\end{pmatrix}\begin{pmatrix}1&0\\-1/f_1&1\end{pmatrix} = \begin{pmatrix}M & f_1+f_2\\ 0 & 1/M\end{pmatrix}, \qquad q_\mathrm{out} = M^2 q_\mathrm{in} + M(f_1+f_2)
```

La partie imaginaire de q (donc z\_R) est multipliée par M² = 4,01 ; la distance au waist aussi, plus un décalage fixe M(f₁+f₂).

**Mode afocal, valeurs propagées** (waist d'entrée 17,29 mm devant la face du TC25, L1 à 30 mm de la face) :

| Grandeur | Entrée (sortie TC25) | Sortie de L2 |
| --- | --- | --- |
| w₀ | 2,745 mm | 5,497 mm |
| z\_R | 22,2 m | 89,2 m |
| θ (demi-angle 1/e²) | 123 µrad | 61,6 µrad |
| Position du waist | 17,3 mm devant la face | virtuel, ≈ 0,2 m en amont de L2 |
| D à 100 / 300 / 1000 mm après L2 | — | 10,994 / 10,994 / 10,995 mm |

**Mode compensé** (espacement 30,35 mm entre sommets) : à la sortie de L2, D = 7,99 mm et R = +406 mm (divergent, waist virtuel de 34 µm à 406 mm en amont). Puis D = 8,98 mm à 50 mm, 9,96 mm à 100 mm, 11,9 mm à 200 mm.

**Foyer de l'asphère à 1064 nm** : f ≈ 15,6 mm ; BFL 8,63 mm (afocal) → 9,10 mm (compensé), contre 8,12 mm catalogue à 587,6 nm. Spot w ≈ λf/(πw) ≈ 1,0 µm pour w = 5 mm (indicatif, NA ≈ 0,3). Longueur de Rayleigh au foyer ≈ 3 µm.

**Longueurs d'onde voisines** (même montage, espacement réajusté) :

| λ (nm) | n N-BK7 | Réajustement de l'espacement (mode afocal) | RMS télescope (λ) | Traitement adapté |
| --- | --- | --- | --- | --- |
| 1000 | 1,5073 | −0,13 mm | 0,017 | -AB ou -B, pas -C |
| 1064 | 1,5066 | 0 (72,01 mm) | 0,015 | -C |
| 1100 | 1,5063 | +0,07 mm | 0,015 | -C |

L'aberration de l'asphère à 1000 et 1100 nm est quasi identique à celle de 1064 nm (0,075 λ pour D = 8 mm ; 0,24 λ pour D = 11 mm ; même compensation à ±5 %).

## 13. Schéma optique

&#91;embedded content: schéma optique · fibre → TC25 → L1 → L2 → asphère 37-424\]

Le faisceau ne passe par aucun foyer avant l’asphère ; entre parenthèses, les valeurs du mode compensé (L1 rapprochée de L2 d’environ 42 mm, faisceau légèrement divergent). Deux miroirs de renvoi, non dessinés, se placent entre L2 et l’asphère.

## 14. Liste d'achat finale

- [ ] Thorlabs **TC25APC-1064** ×1 (ou TC25FC-1064 si la jarretière est FC/PC)
- [ ] Thorlabs **LC1582-C** ×1 (f = −75 mm, Ø 1")
- [ ] Thorlabs **LA1433-C** ×1 (f = +150 mm, Ø 1")
- [ ] Edmund **#23-013** ×1 (asphère 37-424 traitée SWIR+), si la 37-424 non traitée peut encore être remplacée
- [ ] Cage 30 mm : 4 tiges de 150 mm, 3 plaques SM1 (dont une libre de coulisser), adaptateur pour le TC25, un iris en cage
- [ ] 2 miroirs Ø 1" pour 1064 nm + 2 montures cinématiques
- [ ] Optionnel, repli : Thorlabs **F810APC-1064** (solution 8 mm sans télescope)

Coût optique hors collimateur et mécanique : ≈ 60–70 $ pour les deux lentilles (prix catalogue V20, à confirmer), + 379 $ pour l'asphère traitée.

## 15. Points restant à vérifier expérimentalement

1. **Longueur d'onde finale** : elle fixe les traitements (-C dès 1050 nm, -AB jusqu'à 1100 nm) et la variante du collimateur.
2. **Connecteur et fibre** : FC/PC ou FC/APC (TC25FC ou TC25APC) ; MFD réel de la fibre à la longueur d'onde, qui fixe le vrai diamètre (D ∝ λ/MFD).
3. **Collimation réelle du TC25** : la divergence catalogue est donnée sans tolérance chiffrée pour cette référence ; mesurer D à 0,3 m et 3 m (doit rester à ±1 %).
4. **Prescription réelle de la 37-424** : télécharger le fichier Zemax sur la page Edmund et refaire le calcul de la section 7 avec la vraie surface. C'est l'hypothèse la plus forte du document.
5. **Erreur de forme de l'asphère** : mesurer le spot focal (ou le front d'onde avec un Shack-Hartmann) pour savoir si les 0,4λ RMS de la fiche concernent la zone centrale de 10 mm.
6. **Ce qu'il y a entre l'asphère et l'émetteur** : hublot de cryostat, substrat, miroir de Bragg traversé ? Une lame à faisceau focalisé ajoute de l'aberration sphérique, que l'espacement du télescope peut aussi absorber en partie. Le calcul suppose de l'air.
7. **Obstruction centrale éventuelle** : dans le montage de la thèse, la fibre-cavité est montée à l'intérieur d'une lentille asphérique. Si c'est cette lentille, le trou central masque le centre du faisceau gaussien et change le choix du diamètre (il faudrait alors un faisceau plus large ou une mise en forme annulaire). À confirmer.
8. **Reflets** : avec la 37-424 non traitée, 7,8 % par face repart vers le télescope ; vérifier que rien ne revient dans la fibre (léger tilt de l'asphère tolérable : 10 mrad ne coûtent rien).

## Sources

- Thorlabs — [collimateurs FC/APC à focale fixe (F280APC-1064)](https://www.thorlabs.com/fixed-focus-collimation-packages-fcapc-connectors?pn=F280APC-A)
- Thorlabs — [collimateurs à doublet espacé (F810APC-1064)](https://www.thorlabs.com/air-spaced-doublet-collimators-fcapc-fcpc-sma)
- Thorlabs — [collimateurs triplets](https://www.thorlabs.com/triplet-fiber-optic-collimatorscouplers-) ; [TC25APC-1064 (GoPhotonics)](https://www.gophotonics.com/products/collimators/thorlabs-inc/50-46-tc25apc-1064)
- Edmund Optics — [#37-424](https://www.edmundoptics.com/p/20mm-dia-067-numerical-aperture-uncoated-high-precision-aspheric-lens/44551/) ; [#37-424-INK, prix FR](https://www.edmundoptics.fr/p/20mm-dia-067-numerical-aperture-uncoated-inked-high-precision-aspheric-lens/45389/) ; [famille Precision Aspheric (#23-013, #22-999)](https://www.edmundoptics.com/f/PdfExport/39674) ; [R₁ et verre N-SF6 (3DOptix)](https://www.3doptix.com/catalog/optics/lens/edmund-optics/37-424)
- Thorlabs, géométries de lentilles — [LC1582-C](https://www.3doptix.com/catalog/optics/lens/thorlabs/LC1582-C), [LA1433-C](https://www.3doptix.com/catalog/optics/lens/thorlabs/LA1433-C), [LA1433-C-ML](https://www.gophotonics.com/products/optical-lenses/thorlabs-inc/33-46-la1433-c-ml), [LC1120-C](https://3doptix.com/catalog/optics/lens/thorlabs/LC1120-C), [LC1120](https://www.gophotonics.com/products/optical-lenses/thorlabs-inc/33-46-lc1120), [LC1715-C](https://www.3doptix.com/catalog/optics/lens/thorlabs/LC1715-C), [LA1509-C](https://www.gophotonics.com/products/optical-lenses/thorlabs-inc/33-46-la1509-c), [LA1608-C](https://3doptix.com/catalog/optics/lens/thorlabs/LA1608-C), [LA1433-AB](https://www.3doptix.com/catalog/optics/lens/thorlabs/LA1433-AB), [catalogue p. 603](https://thorlabs.com/catalogpages/v20/603.pdf)

Les PDF Thorlabs donnés dans le cahier des charges n'étaient pas accessibles directement depuis mon outil ; les valeurs viennent des pages produit ci-dessus.
