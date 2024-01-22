# MALT0

## Description :

### Nom complet :

Métrique altimétrique 0

### But :

Comparer le profil de hauteur pour chaque classe entre une classification de référence et une classification à comparer.

Cette comparaison est faite à partir des modèles numériques de surface calculés à partir
des nuages filtrés pour ne contenir que la classe demandée.

### Métrique intrinsèque (calculée indépendemment pour le nuage de référence et le nuage classé à comparer) :

Calcul du MNx (modèle numérique de surface calculé à partir d'une classe donnée) et d'une carte
d'occupation (carte binaire à la même résolution que le MNx qui indique si le pixel contient au moins
un point de la classe représentée, cf [MPLA0](./mpla0.md)) pour chaque classe.

Le MNx est calculé par :
- génération d'une triangulation de Delaunay 2d des points de la classe
- interpolation des valeurs sur un raster à la taille de pixel désirée (pdal faceraster filter)

Résultat :
- pour chaque nuage (référence ou à comparer), un fichier tif contenant une couche par
classe qui représente le MNx de la classe donnée
- pour chaque nuage de référence, un fichier tif contenant une couche par classe qui représente la carte d'occupation de la classe donnée

### Métrique relative (calculée à partir des fichiers intermédiaires en sortie de métrique intrinsèque)

Pour chaque classe, comparer les valeurs des cartes de MNx (`height_maps`) entre la référence et le nuage à comparer,
uniquement sur les pixels où le nuage de référence a des points de cette classe (valeurs positives de la carte d'occupation).

Les valeurs de sortie (dans un fichier csv) sont pour chaque classe :
- `mean_diff` : différence moyenne en z entre les MNx pour chaque pixel (0 si aucun pixel dans la référence)
- `mean_diff` : différence maximum en z entre les MNx pour chaque pixel (0 si aucun pixel dans la référence)
- `std_diff` : l'écart-type de la différence en z entre les MNx pour chaque pixel (0 si aucun pixel dans la référence)

### Note

La note est calculée à partir des 3 composantes en sortie de la métrique relative (`mean_diff`, `max_diff`, `std_diff`).

Pour chacune des ces 3 composantes, on calcule une valeur intermédiaire (`note` entre 0 et 1), à partir d'une fonction affine bornée. C'est-à-dire une fonction du type :

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

En dessous d'une valeur `min` de `metric` et au dessus d'une valeur `max` de `metric`, la note vaut 0 ou 1, entre les 2 on utilise une fonction affine pour calculer la valeur de la `note`.

Ensuite, on calcule une somme pondérée entre ces 3 notes intermédiaires à partir des valeurs de `coefficient` données en paramètre.

## Paramétrage

### Poids des classes dans les métriques :

Dans le fichier de configuration.yaml, il faut indiquer les poids de chacune des classes dans le calcul des métriques comme ci dessous :
```yaml
matl0:  # Nom de la métrique
  weights:
    "2": 56     # La classe 2 a un poids de 56
    "3_4_5": 16  # La classe composée des classes 3, 4 et 5 a un poids de 16
```

### Calcul de la note et paramétrage de la fonction

Dans le fichier de configuration.yaml, il faut indiquer les paramètres de calcul de la note comme ci-dessous :

```yaml
  notes:
    # Paramètres pour la composante `max_diff` de la note (maximum des différences en z)
    max_diff:
      # Coefficient à appliquer dans le calcul de la note finale (somme pondérée)
      coefficient: 1
      # Coordonnées du point correspondant à la borne min de la fonction affine bornée (valeur de `metric` en dessous de laquelle `note` vaut toujours la valeur précisée ici)
      # Dans l'exemple, si `max_diff` est inférieur à 0.1, la note est à 1
      min_point:
        metric: 0.1
        note: 1
      # Coordonnées du point correspondant à la borne max de la fonction affine bornée (valeur de `metric` au dessus de laquelle `note` vaut toujours la valeur précisée ici)
      # Dans l'exemple, si `max_diff` est supérieur à 4, la note est à 0
      max_point:
        metric: 4
        note: 0
    # Paramètres pour la composante `mean_diff` de la note (moyenne des différences en z)
    mean_diff:
      # Coefficient à appliquer dans le calcul de la note finale (somme pondérée)
      coefficient: 2
      # Coordonnées du point correspondant à la borne min de la fonction affine bornée (valeur de `metric` en dessous de laquelle `note` vaut toujours la valeur précisée ici)
      # Dans l'exemple, si `mean_diff` est inférieur à 0.01, la note est à 1
      min_point:
        metric: 0.01
        note: 1
      # Coordonnées du point correspondant à la borne max de la fonction affine bornée (valeur de `metric` au dessus de laquelle `note` vaut toujours la valeur précisée ici)
      # Dans l'exemple, si `mean_diff` est supérieur à 0.5, la note est à 0
      max_point:
        metric: 0.5
        note: 0
    # Paramètres pour la composante `std_diff` de la note (écart-type des différences en z)
    std_diff:
      # Coefficient à appliquer dans le calcul de la note finale (somme pondérée)
      coefficient: 2
      # Coordonnées du point correspondant à la borne min de la fonction affine bornée (valeur de `metric` en dessous de laquelle `note` vaut toujours la valeur précisée ici)
      # Dans l'exemple, si `std_diff` est inférieur à 0.01, la note est à 1
      min_point:
        metric: 0.01
        note: 1
      # Coordonnées du point correspondant à la borne max de la fonction affine bornée (valeur de `metric` au dessus de laquelle `note` vaut toujours la valeur précisée ici)
      # Dans l'exemple, si `mean_diff` est supérieur à 0.5, la note est à 0
      max_point:
        metric: 0.5
        note: 0
   ```
