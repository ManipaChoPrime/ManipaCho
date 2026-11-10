Je veux construire progressivement un petit simulateur optique en Python, destiné à terme à me permettre de modéliser des systèmes optiques réels (lentilles simples, doublets, plusieurs lentilles en série) et de calculer non seulement les trajectoires des rayons mais aussi le chemin optique et le front d'onde.

Pour commencer, construis une **V0 minimale mais physiquement propre**.

## 1. Objectif de la V0

La V0 doit être un **ray tracer 2D non-paraxial** dans le plan x-z.

Le système doit permettre de :

- définir une source ponctuelle ;
- lancer un ensemble de rayons depuis cette source ;
- définir une ou plusieurs surfaces sphériques ;
- définir les indices de réfraction de part et d'autre de chaque surface ;
- calculer exactement l'intersection rayon/surface sphérique ;
- appliquer la loi de Snell vectoriellement ;
- propager les rayons jusqu'à la surface suivante ;
- tracer graphiquement les rayons et les surfaces ;
- vérifier que le comportement obtenu est physiquement correct.

Ne cherche surtout pas à faire une grosse architecture dès maintenant. Je veux une V0 courte, lisible et testable, qui servira de fondation aux versions suivantes.

---

# 2. Convention géométrique

Utilise un repère 2D :

- z = axe optique ;
- x = coordonnée transverse ;
- les rayons sont représentés par une position `(x, z)` et une direction unitaire `(dx, dz)`.

Une surface sphérique est définie par :

- position de son sommet `z_vertex` ;
- rayon de courbure `R`.

Adopte une convention de signe explicite et documente-la dans le code.

Par exemple :

- `R > 0` : centre de courbure situé vers +z ;
- `R < 0` : centre de courbure situé vers -z.

Le centre de courbure est donc :

`z_center = z_vertex + R`

et le rayon géométrique de la sphère est `abs(R)`.

La surface doit être représentée par le cercle correspondant, mais seules les intersections physiquement pertinentes dans la région de l'optique doivent être utilisées.

---

# 3. Classe Ray

Crée une classe simple du type :

`Ray`

avec au minimum :

- position `(x, z)`
- direction `(dx, dz)`
- indice du milieu courant `n`
- éventuellement une liste permettant d'enregistrer l'historique du rayon.

La direction doit toujours être normalisée.

Ajoute des méthodes simples comme :

- propagation jusqu'à un z donné ;
- calcul de la position du rayon ;
- éventuellement calcul de la distance parcourue.

---

# 4. Intersection avec une surface sphérique

Implémente une fonction robuste permettant de calculer l'intersection entre un rayon :

`r(t) = r0 + t d`

et une sphère de centre `C` et de rayon `|R|`.

Résous réellement l'équation quadratique.

Il faut :

- rejeter les solutions avec `t < 0` ;
- choisir l'intersection physiquement pertinente ;
- gérer proprement le cas où le rayon ne rencontre pas la surface.

Ne fais pas d'approximation paraxiale.

Je veux que cette partie soit indépendante et testable.

---

# 5. Loi de Snell

À chaque surface, calcule :

1. le point d'incidence ;
2. la normale locale à la surface ;
3. l'angle d'incidence ;
4. la direction réfractée.

Utilise une formulation vectorielle de la loi de Snell plutôt qu'une approximation angulaire.

La fonction doit prendre quelque chose comme :

`refract(ray_direction, surface_normal, n1, n2)`

et retourner la nouvelle direction.

Il faut gérer correctement :

- changement de milieu ;
- incidence oblique ;
- incidence normale ;
- réfraction vers un indice plus élevé ;
- réfraction vers un indice plus faible ;
- réflexion totale interne.

En cas de réflexion totale interne, retourne explicitement un état permettant de savoir que le rayon n'est pas transmis.

Fais très attention à l'orientation de la normale. Le code doit fonctionner aussi bien pour une surface traversée de gauche à droite que dans l'autre sens.

---

# 6. Classe SphericalSurface

Crée une classe :

`SphericalSurface`

contenant au minimum :

- `z_vertex`
- `R`
- `n1`
- `n2`
- éventuellement une ouverture/diamètre.

Elle doit fournir :

- son centre de courbure ;
- son équation ;
- sa normale locale ;
- son intersection avec un rayon ;
- la réfraction du rayon.

Je veux que cette classe reste suffisamment générique pour pouvoir ensuite l'utiliser dans une lentille réelle.

---

# 7. Classe OpticalSystem

Crée une classe simple :

`OpticalSystem`

qui contient une liste ordonnée de surfaces.

Elle doit permettre de faire :

`system.trace(ray)`

et de propager un rayon à travers toutes les surfaces successives.

À chaque étape, enregistre :

- position ;
- direction ;
- indice ;
- distance parcourue ;
- surface rencontrée.

Si un rayon est bloqué ou subit une réflexion totale interne, arrête proprement son parcours.

---

# 8. Source ponctuelle

Crée une fonction permettant de générer des rayons à partir d'un point :

`PointSource(x0, z0)`

avec un ensemble d'angles.

Par exemple :

- 101 rayons ;
- angles uniformément répartis entre `-theta_max` et `+theta_max`.

Chaque rayon commence au même point mais avec une direction différente.

Je veux pouvoir faire quelque chose comme :

```python
source = PointSource(
    x=0,
    z=0,
    theta_max=np.deg2rad(15),
    n_rays=101
)

rays = source.generate_rays()
```

---

# 9. Premier système de test

Construis ensuite un exemple extrêmement simple :

```text
source ponctuelle
       \
        \
---------\---------------- surface plane
         \
          \
```

Commence par tester une simple interface plane air → verre.

Puis fais une seconde expérience avec une surface sphérique.

Le programme doit produire une figure montrant :

- la surface ;
- les rayons incidents ;
- les rayons réfractés ;
- la source.

---

# 10. Tests physiques obligatoires

Avant de passer à quoi que ce soit de plus complexe, écris quelques tests numériques.

### Test 1 — incidence normale

Un rayon arrivant normalement sur une interface ne doit pas changer de direction.

### Test 2 — loi de Snell

Pour un rayon passant de `n1 = 1.0` à `n2 = 1.5`, vérifie numériquement :

`n1 sin(theta1) = n2 sin(theta2)`

avec une tolérance raisonnable.

### Test 3 — réflexion totale interne

Pour un rayon passant de `n1 = 1.5` vers `n2 = 1.0`, avec un angle supérieur à l'angle critique, le programme doit détecter la réflexion totale interne.

### Test 4 — surface plane

Pour une surface plane, vérifie que les résultats sont cohérents avec Snell.

### Test 5 — surface sphérique

Vérifie que l'intersection rayon/sphère est correcte avec une géométrie simple dont on peut connaître analytiquement le résultat.

---

# 11. Visualisation

Utilise uniquement :

- NumPy
- Matplotlib

pour cette V0.

Fais une fonction :

`plot_system(system, rays)`

qui affiche :

- les surfaces ;
- les rayons ;
- la source ;
- éventuellement les points d'intersection.

Le graphique doit avoir une échelle identique en x et z lorsque c'est pertinent (`ax.set_aspect("equal")`).

Ajoute des labels et une légende suffisamment claire pour comprendre le système.

---

# 12. Organisation du code

Ne fais pas un unique énorme script.

Je veux quelque chose de raisonnablement structuré, par exemple :

```text
optical_sim/
    ray.py
    surface.py
    source.py
    system.py
    tracing.py
    plotting.py
    tests/
        test_refraction.py
        test_intersection.py
    examples/
        v0_basic.py
```

Mais si cette structure est excessive pour une V0, simplifie-la. Le critère principal est la lisibilité et la facilité d'évolution.

---

# 13. Ce que je NE veux PAS dans la V0

Ne mets pas encore :

- lentilles épaisses ;
- doublets ;
- aberrations ;
- Gaussian beams ;
- diffraction ;
- FFT ;
- wavefront maps ;
- GUI ;
- optimisation ;
- tolérancement ;
- ray tracing 3D ;
- Zemax-like interface.

Tout cela viendra plus tard.

La V0 doit uniquement établir un moteur de ray tracing fiable.

---

# 14. Validation

Une partie très importante du travail est de vérifier que le code est physiquement correct.

Pour chaque élément mathématique important :

- explique brièvement l'équation utilisée ;
- indique les conventions de signe ;
- écris un test numérique ;
- évite les formules "magiques" non justifiées.

Si tu hésites entre plusieurs conventions, choisis-en une, documente-la clairement et utilise-la partout.

Je préfère un code légèrement plus long mais physiquement transparent à un code compact difficile à vérifier.

---

# 15. Préparer la suite sans la coder

À la fin, explique très brièvement comment cette V0 pourra être étendue vers :

### V1
Une lentille épaisse composée de plusieurs surfaces sphériques :

```text
air
 ↓
surface 1
 ↓
verre 1
 ↓
surface 2
 ↓
verre 2
 ↓
surface 3
 ↓
air
```

### V2
Calcul de l'optical path length :

`OPL = Σ n_i L_i`

pour chaque rayon.

### V3
Calcul de l'OPD et du front d'onde sur un plan de sortie.

### V4
Passage à une vraie carte 2D/3D de phase et éventuellement à la diffraction/Fourier optics.

Mais ne code PAS ces extensions maintenant.

---

## Principe général

Je veux que tu te comportes comme si tu construisais le noyau d'un petit logiciel de ray tracing scientifique.

**Priorité absolue : exactitude physique, simplicité, tests et extensibilité.**

Ne cherche pas à optimiser prématurément le code.

Commence par expliquer brièvement l'architecture choisie, puis donne le code complet de la V0, puis les tests, puis un exemple d'utilisation permettant de voir les rayons sur une interface plane et une surface sphérique.

Le code doit pouvoir être exécuté directement après installation de NumPy et Matplotlib.