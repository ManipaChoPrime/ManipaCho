La V0 est validée : les 28 tests passent et le ray tracing non-paraxial fonctionne correctement.

Je veux maintenant construire la V1.

Cette fois, le but est de transformer le moteur de ray tracing en un outil capable de modéliser une **lentille épaisse réelle composée de plusieurs surfaces sphériques**, puis de calculer le **chemin optique (OPL)** de chaque rayon.

Ne réécris pas le moteur de la V0 inutilement. Pars du code existant et conserve les tests qui fonctionnent.

## 1. Objectif V1

Je veux pouvoir définir une lentille générique avec :

- plusieurs surfaces sphériques ;
- plusieurs matériaux ;
- des épaisseurs physiques ;
- des indices de réfraction ;
- une ouverture.

Par exemple :

```text
air
 ↓
surface sphérique R1
 ↓
verre 1
 ↓
surface sphérique R2
 ↓
verre 2
 ↓
surface sphérique R3
 ↓
air
```

Le système doit rester entièrement séquentiel.

---

## 2. Nouvelle notion : OpticalElement

Ajoute une abstraction simple permettant de regrouper plusieurs surfaces.

Par exemple :

```python
Lens(
    surfaces=[...],
    name="Example lens"
)
```

ou une architecture équivalente si tu trouves quelque chose de plus propre.

Je veux pouvoir créer ensuite :

```python
lens = ThickLens(...)
```

sans devoir manipuler manuellement chaque surface dans mon script utilisateur.

Mais ne rends pas l'architecture inutilement complexe.

---

## 3. Lentille épaisse générique

Implémente une fonction permettant de définir au minimum :

```python
ThickLens(
    R1,
    R2,
    thickness,
    n_glass,
    n_air=1.0,
    aperture=...
)
```

avec une convention de signe clairement documentée.

Pour commencer, utilise un seul verre.

Exemple :

```text
air
       R1              R2
        )              (
--------)---------------(--------
        <--- thickness --->
             verre
```

Le système doit générer automatiquement les deux surfaces correspondantes.

---

## 4. Validation analytique

C'est très important.

Ajoute des tests permettant de comparer le ray tracing exact à l'optique paraxiale.

Pour une surface sphérique, vérifie :

\[
\frac{n_1}{s}
+
\frac{n_2}{s'}
=
\frac{n_2-n_1}{R}.
\]

Pour une lentille épaisse, vérifie que dans la limite paraxiale, la puissance totale obtenue par le ray tracing est cohérente avec la formule de la lentille épaisse.

Si tu utilises une formule de lentille épaisse, écris-la explicitement et documente les conventions de signe.

Ne suppose jamais qu'une formule paraxiale est exacte pour les rayons marginaux.

---

# 5. Calcul de l'OPL

Chaque rayon possède déjà un historique de propagation.

Ajoute maintenant :

```python
ray.opl()
```

ou une fonction équivalente.

Pour chaque segment :

\[
OPL_i = n_i L_i
\]

et :

\[
OPL = \sum_i n_i L_i.
\]

Attention à bien utiliser l'indice du **milieu dans lequel le segment a été parcouru**, pas simplement l'indice après réfraction.

Documente clairement cette convention.

---

# 6. Plan de sortie commun

Ajoute la possibilité de propager tous les rayons jusqu'à un même plan :

```python
z_final
```

déjà présent dans la V0.

Pour chaque rayon survivant, je veux connaître :

```text
x_final
z_final
theta_final
OPL
```

Ainsi que les données nécessaires pour reconstruire son historique.

---

# 7. Première analyse d'aberration

Ajoute une fonction permettant d'étudier le foyer.

Pour chaque rayon lancé depuis une source ponctuelle :

1. trace le rayon à travers la lentille ;
2. extrapole sa trajectoire après la dernière surface ;
3. calcule où il coupe l'axe optique.

On doit alors pouvoir obtenir :

\[
z_f(\theta).
\]

Trace :

```text
z_f en fonction de theta
```

et éventuellement :

```text
z_f en fonction de x_pupil
```

Cela doit permettre de visualiser directement l'aberration sphérique.

Calcule également :

- foyer paraxial ;
- foyer marginal ;
- longitudinal spherical aberration (LSA).

---

# 8. Front d'onde : préparer correctement la V2

Ne prétends pas encore calculer un "front d'onde" complet si les données ne suffisent pas.

À ce stade, ajoute seulement les outils nécessaires pour calculer l'OPL sur un **plan commun**.

Je veux ensuite pouvoir faire :

```python
rays = system.trace_bundle(...)
data = system.intercept_at_plane(rays, z_final)

x = data.x
opl = data.opl
```

et disposer de :

\[
OPL(x).
\]

À partir de là, la V2 pourra construire l'OPD par rapport à une surface de référence.

---

# 9. Premier cas réel : AC254-060-B

Une fois la lentille générique validée, ajoute un exemple séparé :

```python
ac254_060_b.py
```

définissant la lentille réelle à partir des données constructeur que je fournis.

Ne hard-code pas les propriétés de cette lentille dans les classes génériques.

L'exemple doit simplement instancier les objets génériques avec les paramètres de l'AC254-060-B.

Pour les indices de réfraction, utilise explicitement les valeurs que je fournirai pour la longueur d'onde étudiée.

Ne suppose pas que la focale nominale du constructeur est exactement celle obtenue à une autre longueur d'onde.

---

# 10. Architecture souhaitée

Conserve une architecture simple du genre :

```text
optical_sim/
    ray.py
    refraction.py
    surface.py
    element.py
    lens.py
    system.py
    source.py
    opl.py
    plotting.py

tests/
    ...

examples/
    v0_basic.py
    v1_thick_lens.py
    ac254_060_b.py
```

Si tu juges cette architecture inutilement complexe, simplifie-la.

---

# 11. Tests supplémentaires obligatoires

Ajoute au minimum :

### Test A
Lentille avec deux surfaces planes.

### Test B
Lentille avec une seule surface sphérique.

### Test C
Lentille épaisse symétrique.

### Test D
Conservation de l'OPL dans un cas trivial.

### Test E
Deux rayons différents traversant un système homogène doivent avoir un OPL cohérent avec leur longueur géométrique.

### Test F
Vérification de la convergence vers l'optique paraxiale lorsque l'angle des rayons tend vers zéro.

### Test G
AC254-060-B : le comportement doit être cohérent avec les spécifications constructeur dans la limite où celles-ci sont comparables au modèle.

---

# 12. Important : ne pas introduire encore de diffraction

Ne fais toujours PAS :

- FFT ;
- PSF ;
- MTF ;
- propagation de Fresnel ;
- propagation de Fraunhofer ;
- Gaussian beam ;
- optimisation ;
- GUI.

Nous voulons d'abord avoir :

**ray tracing exact → OPL exact → OPD correctement défini.**

La diffraction viendra ensuite seulement si nécessaire.

---

## Critère de réussite

À la fin de la V1, je veux pouvoir écrire quelque chose comme :

```python
system = OpticalSystem()

system.add(ac254_060_b)

source = PointSource(
    x=0,
    z=-50e-3,
    theta_max=np.deg2rad(10),
    n_rays=201
)

rays = system.trace(source.generate_rays())

data = system.intercept_at_plane(
    rays,
    z_final=...
)

plot_rays(rays)
plot_focus(rays)
plot_opl(data)
```

et obtenir trois informations fiables :

1. les trajectoires réelles des rayons ;
2. la position du foyer en fonction du rayon ;
3. l'OPL de chaque rayon sur un plan commun.

Le code doit rester transparent et scientifique : chaque convention de signe et chaque équation doivent être documentées.