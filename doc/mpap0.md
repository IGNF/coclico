# MPAP0

## Description :

### Nom complet :

Métrique point à point 0

### But :

Comparer le nombre de points pour chaque classe entre une classification de référence et un classification à comparer.

### Métrique intrinsèque (calculée indépendemment pour le nuage de référence et le nuage classé à comparer):

Calcul du nombre de points de chaque classe dans le nuage.

Résultat : fichier json contenant les nombre de points de chaque classe dans un dictionnaire

### Métrique relative (calculée à partir des fichiers intermédiaires en sortie de métrique intrinsèque)

Pour chaque classe, comparer le nombre de points de chaque classe entre les 2 nuages.

Les valeurs de sortie (dans un fichier csv) sont pour chaque classe :
- `absolute_diff` : la différence entre les nombres de points entre le nuage classé et le nuage de référence
- `ref count` : le nombre de points dans le nuage de référence

### Note

On utilise comme intermédiaire de calcul la variable `metric` qui dépend du nombre de points dans le nuage de référence (`ref_count`) :
- si `ref_count` est en dessous d'un certain seuil (`ref_count_threshold`), la note est calculée à partir de la différence absolue en nombre de points (`absolute_diff`)
- sinon elle est calculée à partir de la différence relative en nombre de points (`absolute_diff / ref_count`)

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

### Poids des classes dans les métriques :

Dans le fichier de configuration.yaml, il faut indiquer les poids de chacune des classes dans le calcul des métriques comme ci-dessous :

```yaml
mpap0:  # Nom de la métrique
  weights:
    "1": 0.5  # La classe 1 a un poids de 0.5
    "2": 7  # La classe 2 a un poids de 7
    "3_4": 1  # La classe composée des classes 3 et 4 a un poids de 1
```

### Calcul de la note et paramétrage de la fonction

Dans le fichier de configuration.yaml, il faut indiquer les paramètres de calcul de la note comme ci-dessous :
```yaml
  notes:
    # Seuil (nombre de points référence) qui fait basculer la variable `metric` entre les 2 méthodes de calcul
    ref_count_threshold: 1000
    # Définition de la fonction affine bornée lorsque le nombre de points référence pour la classe donnée est EN DESSOUS de`ref_count_threshold`
    # On utilise alors directement `absolute_diff` comme valeur de `metric`
    under_threshold:
      # Coordonnées du point correspondant à la borne min (valeur de `metric` en dessous de laquelle `note` vaut toujours la valeur précisée ici)
      # Dans l'exemple, si `absolute_diff` est inférieur à 20, la note est à 1
      min_point:
        metric: 20
        note: 1
      # Coordonnées du point correspondant à la borne max (valeur de `metric` au dessus de laquelle `note` vaut toujours la valeur précisée ici)
      # Dans l'exemple, si `absolute_diff` est supérieur à 100, la note est à 0
      max_point:
        metric: 100
        note: 0
    # Définition de la fonction affine bornée lorsque le nombre de points référence pour la classe donnée est AU DESSUS de`ref_count_threshold`
    # On utilise alors `relative_diff` = `absolute_diff` / `ref_count` comme valeur de `metric`
    above_threshold:
      # Coordonnées du point correspondant à la borne min (valeur de `metric` en dessous de laquelle `note` vaut toujours la valeur précisée ici)
      # Dans l'exemple, si `relative_diff` est inférieur à 0, la note est à 1
      min_point:
        metric: 0
        note: 1
      # Coordonnées du point correspondant à la borne max (valeur de `metric` au dessus de laquelle `note` vaut toujours la valeur précisée ici)
      # Dans l'exemple, si `relative_diff` est supérieur à 0.1, la note est à 0
      max_point:
        metric: 0.1
        note: 0
```