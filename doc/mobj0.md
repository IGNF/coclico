# MOBJ0

## Description :

### Nom complet :

Métrique sur les objets 0

### But :

Pour les classes représentant des objets "finis" (bâtiments, ponts, sursol perenne, ...), comparer les objets représentés/détectés pour chaque classe entre une classification de référence et un classification à comparer.

Cette comparaison est faite à l'aide de cartes de classes / cartes d'occupation post-traitée, et de détection de contours sur cette carte.

### Métrique intrinsèque (calculée indépendemment pour le nuage de référence et le nuage classé à comparer):

- Calcul de la carte de classe binaire (`occupancy_map`) pour chaque classe dans le nuage (voir métrique MPLA0).

- Opérations topologiques pour simplifier les formes des objets détectés et se débarrasser du bruit au niveau des limites d'objets.
**A COMPLETER !**

- Vectorisation des contours de la carte débruitée

Résultat : pour chaque nuage, un fichier geojson contenant un polygone par objet, qui a un attribut "layer"
correspondant à l'indice de la classe correspondante dans la liste (ordonnée alphabétiquement) des classes définies
dans le fichier de configuration.

### Métrique relative (calculée à partir des fichiers intermédiaires en sortie de métrique intrinsèque)

Pour chaque classe, appairage des polygones entre le geojson issu de la référence et celui issu du nuage
à comparer.

L'appairage se fait de la façon suivante :
- parmi les polygones de la référence, trouver les polygones du nuage à comparer avec lesquels il y a une intersection
- parmi les paires ainsi trouvées, ne garder qu'une paire par polygone de la référence (en supprimant d'abord les
paires dont la géométrie dans le nuage à comparer est appairée à plusieurs polygones de la référence)
- parmi les paires ainsi restantes, ne garder qu'une paire par polygone du nuage à comparer (en supprimant d'abord les
paires dont la géométrie dans la référence est appairée à plusieurs polygones du nuage à comparer)

Ainsi il ne devrait rester que des paires où un seul polygone de la référence correspond à un polygone du nuage à
comparer.

Les valeurs de sortie (dans un fichier csv) sont pour chaque classe :
- `ref_object_count`: nombre total d'objets dans le nuage de référence
- `paired_count`: nombre de paires trouvées
- `not_paired_count`: nombre d'objets dans la référence et le nuage à comparer qui n'appartiennent pas à une paire

## Note

On utilise comme intermédiaire de calcul la variable `metric` qui dépend du nombre d'objets détectés dans le nuage de référence (`ref_object_count`) :
- si `ref_object_count` est en dessous d'un certain seuil (`ref_object_count_threshold`), la note est calculée à partir du nombre d'objets non appairés `not_paired_count`
- sinon elle est calculée à partir du ratio liant le nombre de paires trouvées et le nombre
d'objets non appairés (`paired_count` / (`paired_count` + `not_paired_count`))
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
mobj0:  # Nom de la métrique
  weights:
    "2": 28   # La classe 2 a un poids de 28
    "4_5": 16  # La classe composée des classes 4 et 5 a un poids de 16
```

#### Calcul de la note et paramétrage de la fonction

Dans le fichier de configuration.yaml, il faut indiquer les paramètres de calcul de la note comme ci-dessous :


```yaml
  notes:
    # Seuil (nombre d'objets dans la référence) qui fait basculer la variable `metric` entre les 2 méthodes de calcul
    ref_object_count_threshold: 20
    under_threshold:
      # Définition de la fonction affine bornée lorsque le nombre de pixels pour la classe donnée est EN DESSOUS de`ref_object_count_threshold`
      # On utilise alors directement `not_paired_count` comme valeur de `metric`
      min_point:
        # Coordonnées du point correspondant à la borne min (valeur de `metric` en dessous de laquelle `note` vaut toujours la valeur précisée ici)
        # Dans l'exemple, si `not_paired_count` vaut 0, la note est à 1
        metric: 0
        note: 1
      # Coordonnées du point correspondant à la borne max (valeur de `metric` au dessus de laquelle `note` vaut toujours la valeur précisée ici)
      # Dans l'exemple, si `not_paired_count` est supérieur à 4, la note est à 0
      max_point:
        metric: 4
        note: 0
    # Définition de la fonction affine bornée lorsque le nombre de'objets dans la référence pour la classe donnée est AU DESSUS de`ref_object_count_threshold`
    # On utilise alors `ratio` = `(paired_count / (paired_count + not_paired_count))` comme valeur de `metric`
    above_threshold:
      # Coordonnées du point correspondant à la borne min (valeur de `metric` en dessous de laquelle `note` vaut toujours la valeur précisée ici)
      # Dans l'exemple, si `ratio` est inférieur à 0.8, la note est à 0
      min_point:
        metric: 0.8
      # Coordonnées du point correspondant à la borne max (valeur de `metric` au dessus de laquelle `note` vaut toujours la valeur précisée ici)
      # Dans l'exemple, si `ratio` vaut 1, la note est à 1
      max_point:
        metric: 1
        note: 1
```
