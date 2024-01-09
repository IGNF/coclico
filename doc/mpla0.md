# MPLA0

## Description :

### Nom complet :

Métrique point à point 0

### But :

Comparer la loacalisation en 2d (x, y) recouverte par chaque classe entre une classification de référence et un classification à comparer.

Cette comparaison est faite à l'aide de cartes de classes / cartes d'occupation

### Métrique intrinsèque (calculée indépendemment pour le nuage de référence et le nuage classé à comparer):

Calcul de la carte de classe binaire (`occupancy_map`) pour chaque classe dans le nuage.

Cette carte contient 1 quand au moins un point du nuage est localisé dans le pixel, 0 sinon.

Résultat : pour chaque nuage, un fichier tif contenant un couche par classe, qui représente
la carte binade de la classe considérée.

### Métrique relative (calculée à partir des fichiers intermédiaires en sortie de métrique intrinsèque)

Calcul de l'union et de l'intersection entre la carte de classe de la référence et celle du nuage à comparer.

Les valeurs de sortie (dans un fichier csv) sont pour chaque classe :
- `intersection` : nombre de pixels ayant la valeur 1 dans les 2 cartes à la fois
- `union` : nombre de pixels ayant la valeur 1 dans au moins une des 2 cartes
- `ref_pixel_count` : nombre de pixels à 1 dans la carte de référence (utilisé comme seuil dans le
calcul de la note)

### Note

On utilise comme intermédiaire de calcul la variable `metric` qui dépend du nombre de pixels à 1 dans la carte de classe du nuage de référence (`ref_pixel_count`) :
- si `ref_pixel_count` est en dessous d'un certain seuil (`ref_pixel_count_threshold`), la note est calculée à partir de la différence entre intersection et union  (`union` - `intersection`)
- sinon elle est calculée à partir de la IoU (`intersection` / `union`)

Dans chacun des cas, la note finale (`note`) est dérivée de `metric` à partir d'une fonction affine bornée. C'est-à-dire une fonction du type :

```
              max ________
             /
            /
           /
   _____ min
```

ou
```
______min
         \
          \
           \
             max _______
```

En dessous d'une valeur `min` de `metric` et au dessus d'une valeur `max` de `metric`, la note vaut 0 ou 1, entre les 2 on utilise une fonction
affine pour calculer la valeur de `note`.

## Paramétrage

#### Poids des classes dans les métriques :
Dans le fichier de configuration.yaml, il faut indiquer les poids de chacune des classes dans le calcul des métriques comme ci dessous :
```yaml
mpla0:  # Nom de la métrique
  weights:
    "2": 28   # La classe 2 a un poids de 28
    "4_5": 16  # La classe composée des classes 3, 4 et 5 a un poids de 16
```

#### Calcul de la note et paramétrage de la fonction

Dans le fichier de configuration.yaml, il faut indiquer les paramètre de calcul de la note comme ci-dessous :

```yaml
  notes:
      # Seuil (nombre de pixels occupés de la référence) qui fait basculer la variable `metric` entre les 2 méthodes de calcul
    ref_pixel_count_threshold: 1000
    # Définition de la fonction affine bornée lorsque le nombre de pixels pour la classe donnée est EN DESSOUS de`ref_pixel_count_threshold`
    # On utilise alors directement `union - intersection` comme valeur de `metric`
    under_threshold:
      # Coordonnées du point correspondant à la borne min (valeur de `metric` en dessous de laquelle `note` vaut toujours la valeur précisée ici)
      # Dans l'exemple, si `union - intersection` est inférieur à 20, la note est à 1
      min_point:
        metric: 20
        note: 1
      # Coordonnées du point correspondant à la borne max (valeur de `metric` au dessus de laquelle `note` vaut toujours la valeur précisée ici)
      # Dans l'exemple, si `unioon - intersection` est supérieur à 100, la note est à 0
      max_point:
        metric: 100  # union - intersection
        note: 0
    # Définition de la fonction affine bornée lorsque le nombre de pixels référence pour la classe donnée est AU DESSUS de`ref_pixel_count_threshold`
    # On utilise alors `IoU` = `intersection / union` comme valeur de `metric`
    above_threshold:
      # Coordonnées du point correspondant à la borne min (valeur de `metric` en dessous de laquelle `note` vaut toujours la valeur précisée ici)
      # Dans l'exemple, si `IoU` est inférieur à 0.9, la note est à 0
      min_point:
        metric: 0.9
        note: 0
      # Coordonnées du point correspondant à la borne max (valeur de `metric` au dessus de laquelle `note` vaut toujours la valeur précisée ici)
      # Dans l'exemple, si `IoU` est supérieur à 1, la note est à 1
      max_point:
        metric: 1
        note: 1
```
