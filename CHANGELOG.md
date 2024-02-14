# dev
- Changement de la définition de la zone où est calculée MALT0:
  - masquage du MNx à l'aide de la carte de classe dans MALT0 intrinsic
  - comparaison des MNx sur l'intersection des zones hors no-data (pour exclure les pixels en bord de maillage :
  inclus dans la carte de classe mais hors du maillage utilisé pour le MNx)
- Disparition de la distinction entre calcul de la référence et l'autre nuage de points (était nécessaire uniquement
pour le calcul de MALT0)
- MOBJ0: correction du cas où il n'y a aucune geométrie détectée dans l'ensemble des classes 

# 0.6.0
- ajout d'une 4e métrique : MOBJ0

# 0.5.1
- correctif MALT0 quand il n'y a pas de points dans la référence (+ test sur les autres métriques)

# 0.5.0
- correctif : MALT0 calcul de la métrique relative dans le cas où il n'y a pas de données dans une classe
- refactoring :
  - déplacement du calcul des notes en dehors du calcul des métriques
  - ajout des paramètres de calcul des notes dans le fichier de configuration (cf. `./README.md`)
- documentation : ajout d'une documentation plus complète sur les métriques et le calcul des
notes dans le dossier `./doc`

# 0.4.0
- fonctionnalités:
  - ajout d'une 3e métrique : MALT0
- correctifs :
  - correction de l'extension du fichier de sortir de la métrique intrinsèque de MPLA0
  - correction des poids par défaut dans configs/metrics_weights.yaml
  - documentation de l'ordre des couches dans la métrique intrinsèque de mpla0 intrinsic

# 0.3.1
- fix missing unix-style arguments

# 0.3.0
- ajout seconde métrique : MPLA0
- retrait métrique de test MPAP0-test
- les arguments sont maintenant passés en style unix. eg: --input-file

# 0.2.2
Améliorations architecture :
- score: si le fichier resultat existe, concatène ou remplace dans le fichier.
- archi: évite de refaire les job si le dossier de sortie existe, produit un log pour l'utilisateur
- ajout d'indicateurs d'options à une seule lettre dans main
- copie du fichier de poids plutôt que dump du dictionnaire parsé par coclico
- main: prend une liste de dossier de classification en entrée, pas obligatoirement 2 classifications (c1 et c2)
- résultat intermediaire, avec le score pondéré (une valeur pour chaque métrique)
- possibilité d'avoir des classes différentes pour des métriques différentes
- robustesse aux fichiers avec CRS mal encodé
- utilisation de `_` au lieu de `,` comme séparateur des classes composées
- utilisation de `;` au lieu de `,` comme separateur de colonnes poru les fichiers csv

# 0.2.1
- mpap0: correctif metrique relative, appliquée sur la liste des classes

# 0.2.0
- refactor
- utilisation de la GPAO
- déploiement de l'image docker sur dockerhub à chaque tag git

# 0.1.0
- première version minimale : rapport calculé à partir de 2 dossiers + un dossier de référence
- métrique MPAP0 seulement
- sans GPAO
