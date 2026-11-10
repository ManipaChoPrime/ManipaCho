# Création de l'excitation arrière :

## Type de fibre 

- [P3-1064Y-FC-5](https://www.thorlabs.com/item/P3-1064Y-FC-5) :
    - Taille du MFD (Mode field diameter) : MFD = 6 um à 1030 nm (environ)
    - Le waist $w_0$ vaut donc 3 um
    - Si on suppose le mode Gaussien, on a :
        - $\theta = \frac{\lambda}{\pi w_0}$
        - $\theta$ = 0.107 rad (6.1°) à peu près. Légerement différent de la N.A spécifiée, qui vaut 0.14 

## Doublet pour collimater la fibre :

- On veut un faisceau d'à peu près 8.5 mm de diamètre avant le beam expander. Sachant que le diamètre du faisceau sera de $D = 2f\theta$, on a :
    - f = 39.7 mm 
- On veut une surface "claire" d'à peu près 10 mm. 

- Il existe la [AC254-040-B-ML](https://www.thorlabs.com/item/AC254-040-B-ML) :
    - 1" 
    - Grande mais au moins on ne clip pas. 
    - Je ne trouve rien d'autre en 40 mm de focale (pas de 1/2 ")
    - On peut quand même utiliser des miroirs de 1/2" derrière !

## Beam expander en x2 :

- Le [GBE02-B](https://www.thorlabs.com/item/GBE02-B) coche toutes les cases : 
    - Pour avoir un spot diffraction limited, il faut arriver avec un spot de 8.5 mm de diamètre
    - On va sortir avec un diamètre de 17 mm, parfait pour rentrer dans notre lentille faite sur mesure.
    - AR coated
    - Pas spécifier vide mais on peut le trouer j'imagine

## Renvoi

- Il faudra quelques miroirs de renvois à droite à gauche pour que tout rentre.

## Checker le profil du faisceau :

On peut checker le profil, normalement Gaussien, de notre faisceau, avec le [WFS31-5C_M](https://www.thorlabs.com/item/WFS31-5C_M)