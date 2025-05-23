# BumbleBeeRun

## Introduction
Le projet doit permettre de compter dynamiquement les bourdons qui rentrent et sortent d'une ruche.

On compte le nombre de bourdons à l’extérieur de la ruche. On incrémente le compteur NBBout quand un bourdon sort. On décrémente NBBout quand un bourdon rentre. Le compteur est à zéro quand la ruche est pleine. 

On réalise une double barrière (S0 et S1) pour les bourdons. Les deux détecteurs sont espacés de moins de la moitié du corps d’un bourdon :
Si Front sur S1 et S0 actif : comptage
Si Front sur S0 et S1 actif : décomptage

![image](https://github.com/user-attachments/assets/96b815f9-e86f-4203-bd4b-fadc0a39cfae)

On ne peut relancer un comptage que si les détecteurs S0 et S1 repassent tous les deux à 0
## Configuration 

Le BumbleBeeRun est basé sur la configuration du projet [MiteThru](https://github.com/LR69/MiteThru). Il utilise la même architecture physique et matérielle :
- Méme raspberry 3B+,
- Même carte électronique d'interface homme/machine (Boutons poussoirs et voyants)

à quelques différences près :
- La caméra est inutile donc enlevée,
- Deux barrières infrarouges S0 et S1 sont utilisées pour détecter les bourdons. 
![image](https://github.com/user-attachments/assets/48a0e50c-a81c-4fb1-bae5-7731898915fb)
  

  Ces barrières infrarouges sont en fait des capteurs de proximité (des [MH Infrared Obstacle Sensor "Flying Fish"](https://einstronic.com/product/infrared-obstacle-sensor-module/) dont les deux leds (émettrices et réceptrices), sont déssoudées et placées de part et d'autre du tube de sortie. La lumière infrarouge émise est modulée avec une fréquence de 38kHz pour limiter l'influence de l'éclairage environnant.

## Interface Home Machine
Le raspberry est configuré pour se connecter automatiquement en WiFi à un réseau local (SSID = "MiteMap"). Si un téléphone ou un ordinateur se connecte au même réseau WiFi, il peut se connecter aux différents BumbleBeeRun en saisissant leur adresse IP (192.168.2.101 ; 192.168.2.102 ; 192.168.2.103 ; ...) dans un navigateur web. 

L’interface comporte : 
### Une page principale :
La page principale comporte :
- Un champ numérique donnant la valeur actuelle de NBBout
- Un graphique donnant l’évolution temporelle de NBBout 

### Une page Record
Lors d'un appui sur le bouton poussoir jaune "BP_Record" sur le raspberry, on enregistre à haute fréquence des deux détecteurs S0 et S1 ainsi que l’état de NBBout. Cette page comporte les liens de charger les fichiers ".csv" générés par l’appui sur BP_record.

### Une page capteur
Une page donnant l’état actuel des deux capteurs. 
  
