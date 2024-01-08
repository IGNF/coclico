# MALT0
### Description :
* Faire un MNx pour la classe considérée (en fonction de la classe considérée, méthode d’interpolation et résolution à affiner)
* Calculer la différence entre le MNx de la cible et la référence
  
#### Poids des classes dans les métriques : 
Dans le fichier de configuration.yaml, il est possible d'indiquer les poids de chacune des classes dans le calcul des métriques comme ci dessous : 
```mpap0: Nom de la métrique 
  weights: 
    "2": 56     La classe 2 a un poids de 56
    "3_4_5": 16 Les classes 3, 4 et 5 ont un poids de 16    
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

Il faut donc définir ces seuils dans le fichier de configuration. 
Pour MALT0, il y a 3 valeurs calculées pour la note et donc des paramètres à rentrer pour 3 courbes (La différence des moyennes, l'écart type et la différence des maximums).
Il est possible d'indiquer des coefficients pour ces 3 courbes qui interviendront dans le calcul final.
```
notes:
 max_diff: Différence des maximums
  coefficient: 1
   min_point:
    metric: 0.1 En dessous d'une différence de 0.1, la note est à 1 
    note: 1
   max_point:
    metric: 4 Au dessus d'une différence de 4, la note est à 0 
    note: 0
 mean_diff: Différence des moyennes
  coefficient: 2
   min_point:
    metric: 0.01
    note: 1
   max_point:
    metric: 0.5 
    note: 0
 std_diff: Ecart type
  coefficient: 2
   min_point:
    metric: 0.01 
    note: 1
   max_point:
    metric: 0.5 
    note: 0
```