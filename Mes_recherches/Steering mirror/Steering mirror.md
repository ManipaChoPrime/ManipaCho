# Recherche d'un steering mirror ou d'un équivalent qui aille sous vide

## Le N-480 High-Precision Kinematic Mirror Mount de chez PI

### Quel serait le pas du scan ?

[Lien pour le miroir](https://www.pifrance.fr/fr/products/linear-actuators/piezomike-for-long-term-stability/n-480-high-precision-kinematic-mirror-mount-1000171)

- Les caractéristiques données sont (pour le N-480.210CV par exemple):
    - Un pas angulaire de 0.5 $\mu$ rad
    - Une course de $\pm$ 8°

- On veut savoir les caractéristiques du scan que ça représenterait.
    - On appelle la distance entre le "steering mirror" et l'échantillon L
    - On appelle le pas angulaire $\Delta \theta$
    - On appelle le pas du scan résultant $\Delta x$

Voici le schéma de la situation :

![alt text](image.png)

- Pas de $\Delta \theta$ du miroir correspond à un pas effectif du rayon de $2\Delta \theta$. On a alors :
    - $\Delta x = L \cdot tan(2\Delta \theta)$
    - Etant donné les faibles angles, on a l'approxiamtion $tan(\theta) \approx \theta$ :
        - $\Delta x = L \cdot 2\Delta \theta$ soit $\Delta x = L \cdot 2\Delta \theta$
    - $\Delta x \approx 0,1 \cdot 0,5*10^{-6}$
    - $\Delta x \approx 50 nm$

- On aurait un pas de 50 nm.

### Quelle serait la course du scan ?

- Quel est le nombre $N$ de pas ? 
    - La course du miroir est de $\pm$ 8°, avec des pas de 0,5 $\mu$ rad $\approx$ $3x10^{-5}$°
    - N $\approx 16/3 * 10^{-5} \approx 5,6*10^{5}$

- Quelle est la distance couverte par le scan dans une direction ?
    - Distance = distance pas * nombre de pas
    - $L_{SCAN} = 50*10^{-9} \cdot 5,6*10^5$
    - $L_{SCAN} = 28$ mm

- On aurait une course de 28 mm dans chaque direction.

