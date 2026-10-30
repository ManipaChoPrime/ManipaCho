# Procédure d'alignement du setup :

## A pression ambiante :

### Etape 1 : Aligner l'arrière 

- La première étape est d'aligner l'excitation arrière dans l'IR (1310 nm). Le but est d'utiliser le fait que le DBR agisse comme un miroir à cette longueur d'onde. Cela implique que le collimateur et la fibre utilisés soient ok pour excitation/1310 nm. 

- On peut contrôler l'alignement avec :
    - Un beamsplitter dans la boite, entre le collimateur et la lentille sur mesure de Yannick. Le bras du retour irait sur une caméra à l'exterieur de la boite pour checker l'image du DBR et le focus ? 
    - Un powermeter en dehors de la boite, en pariant sur le fait qu'on va réussir à coupler la reflection du DBR dans le collimateur ? 
    - Une caméra peut être utile pour voir les cercles concentriques autour de la tâche d'Airy en jouant avec le focus, ce qui garantit de rentrer en incidence normale, en plus d'être au focus.

### Etape 2 : Aligner l'avant 

- On peut utiliser le même principe (DBR qui reflete à 1310 nm) pour aligner l'excitation avant. 

### Etape 3 : Aligner l'avant sur l'arrière 

- Le DBR transmet avant 1310nm. On peut donc utiliser la source d'excitation depuis l'arrière, et aligner l'arrière dessus. Cela garantie le recouvrement des deux axes optiques. 

### Etape 4 : Pomper

- On descend la chambre à vide. On espère que ça ne bouge pas trop, et on optimise à nouveau le signal. 

- Si on utilise comme feedthrough pour les fibres optiques d'excitation / de collection des fibres qui supportent 1000 et 1310 nm, et qui sont "coupées" par le feedthrough, on peut switcher entre excitation et collection partout, et s'en servir pour aligner.

- Remarque : c'est pas forcement au feedthrough que ça doit être coupé. Mais ca serait bien d'avoir en sortie de boite, une fibre qui correspond ç l'arrière, une à l'avant, ... Qui arrivent dans un coupleur. Que l'on puisse changer sur mesure les excitations. En fait x'est probablement impossible sans.