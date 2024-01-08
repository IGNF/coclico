# MPAP0
### Description : 
* Compter le nombre de points pour une classe 

#### Poids des classes dans les métriques : 
Dans le fichier de configuration.yaml, il est possible d'indiquer les poids de chacune des classes dans le calcul des métriques comme ci dessous : 
```mpap0: Nom de la métrique 
  weights: 
    "1": 0.5 La classe 1 a un poids de 0.5
    "2": 7   La classe 2 a un poids de 7
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
 ref_count_threshold: 1000 Nombre de points REF 
  under_threshold:
   min_point:
    metric: 20 En dessous de 20 points, la note est à 1 (valeur absolue de la différence : nb pts T - nb pts REF)
    note: 1
   max_point:
    metric: 100 Au dessus de 100 points, la note est à 0 (valeur absolue de la différence : nb pts T - nb pts REF)
    note: 0
```