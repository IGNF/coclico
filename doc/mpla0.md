# MPLA0 
 
### Description : 
* Faire une Carte de Classe Binaire par classe pour la cible et la référence avec une résolution à définir.  
* Calculer l’Union et l’intersection des CCB T et REF (cf exemple en annexe) 

#### Poids des classes dans les métriques : 
Dans le fichier de configuration.yaml, il est possible d'indiquer les poids de chacune des classes dans le calcul des métriques comme ci dessous : 
```mpap0: Nom de la métrique 
  weights: 
    "2": 28   La classe 2 a un poids de 28
    "4_5": 16 Les classes 4 et 5 ont un poids de 16
```

#### Calcul de la note et paramétrage de la fonction

La fonction de calcul de la note se réprésente comme ceci : 
```
              max ________ or ______min
             /                         \\
            /                           \\
           /                             \\
   _____ min                                max _______
```

En dessous ou au dessus de certains seuils de métriques, les notes sont de 0 ou 1 et entre les deux, une fonction affine. 

Il faut donc définir ces seuils dans le fichier de configuration
```
notes:
 ref_pixel_count_threshold: 1000 Nombre de pixels de REF 
  under_threshold:
   min_point:
    metric: 20 En dessous d'une différence de 20 pixels, la note est à 1 (intersection sur l'union)
    note: 1
   max_point:
    metric: 100 Au dessus d'une différence de 100 pixels, la note est à 0 (intersection sur l'union)
    note: 0
```