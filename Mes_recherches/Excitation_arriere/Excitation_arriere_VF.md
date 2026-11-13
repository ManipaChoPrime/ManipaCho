# Création de l'excitation arrière :

## Bloc fibre :

- [Fibre custom](https://www.thorlabs.com/custom-fiber-optic-patch-cables-?tabName=Patch%20Configurator) :
    - Step 1 : SM
    - Step 2 : SM980-5.8-125-(0.14 NA; 970-1550 nm; Cladding: 125 um)
    - Step 3 : Tubing : None
    - Step 4 : Connectors : FC/APC et Scissor cut
    - Step 5 : Length : 3m

- Propriétés :
    - Taille du MFD (Mode field diameter) : MFD = 6 um à 1030 nm (environ)
    - Le waist $w_0$ vaut donc 3 um
    - Si on suppose le mode Gaussien, on a :
        - $\theta = \frac{\lambda}{\pi w_0}$
        - $\theta$ = 0.107 rad (6.1°) à peu près. Légerement différent de la N.A spécifiée, qui vaut 0.14 

- [SM1FCA2](https://www.thorlabs.com/item/SM1FCA2) :
    - Fibre vers 1", peut se visser sur un tube.

- [SM1L10V](https://www.thorlabs.com/item/SM1L10V)
    -On fera sortir la fibre du côté de la retaining lip. Il faudra donc faire passer le SM1FCA2 tout le long du tube.
    - SM1FCA2 en butée de la retaining lip (sinon il faut faire rentrer la fibre dans le spanner, pénible).

- [SM1T3](https://www.thorlabs.com/item/SM1T3)
    - Holder utilisé pour tenir la structure 
    - Permet de raccorder les 2 tubes
    - 2 raccords mâles

- [SM1M10](https://www.thorlabs.com/item/SM1M10) :
    - Tube de 2" (50mm en gros) de long
    - Accessible des 2 côtés pour venir mettre la lentille dans le bon sens.

- [AC254-040-B](https://www.thorlabs.com/item/AC254-040-B) :
    - 1" 
    - Position à régler dans le tube

Tenu par le centre : Ca ne peut pas être plus compact.

## Bloc Beam expander x2 :

- Dans un [SM1M10](https://www.thorlabs.com/item/SM1M10)
    - 1" (25.4 mm) de long
    - Lentille fixée d'un côté au bout.

- Un doublet divergent de 1":   
    - [ACN254-040-B](https://www.thorlabs.com/item/ACN254-040-B)
        - f = -40 mm
        - n = 1.6546 pour la première 
        - n = 1.7743 pour la deuxième
    - Position à régler dans le tube

- [SM1T3](https://www.thorlabs.com/item/SM1T3)

- [SM1L10V](https://www.thorlabs.com/item/SM1L10V)
    - 1" (25.4 mm) de long
    - Lentille fixée d'un côté au bout.

- Un doublet convergent de 1":
    - [AC254-080-B](https://www.thorlabs.com/item/AC254-080-B)
        - f = 80 mm
        - n = 1.6546 pour la première 
        - n = 1.7743 pour la deuxième
    - En butée

Deuxième lentille (Celle après laquelle le faisceau est gros) en butée à la fin, car avant le faisceau est petit par rapport au tube, c'est ok si il rentre dedans.

## Bloc lentille sur mesure et asphérique :



## Autres trucs intelligents :

- Un Shack-Hartmann pour regarder la tête du front d'onde :
    - [WFS31-5C_M](https://www.thorlabs.com/item/WFS31-5C_M)

- Une petite cible dans l'IR à mettre sur des tiges ?
    - [VRC2CPT](https://www.thorlabs.com/item/VRC2CPT)

