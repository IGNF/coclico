# coclico

COmparaison de CLassIfication par rapport à une référence COmmune

*Ce projet est en cours de développement*

# Principe

L'objectif de ce code est de pouvoir comparer les résultats de deux processus de classification de données LiDAR
par rapport à une classification de référence.

Les résultats sont comparés par le calcul de plusieurs métriques, dont sont ensuite tirés des scores compris entre
0 et 1. Ces métriques sont calculées de façon indépendante pour chaque classe mentionnée dans un fichier de
configuration.

Pour l'instant les métriques implémentées sont :
* MPAP0 (Métrique point à point 0) : calcul d'une note à partir de la comparaison du nombre de points pour chaque classe
entre le résultat et la référence
* MPLA0 (Métrique planimétrique 0) : calcul d'une note à partir de l'intersection et l'union de cartes de classes 2D
entre le résultat et la référence
* MALT0 (Métrique altimétrique 0) : calcul d'une note à partir de la différence en Z entre le résultat et la référence
sur un raster de type "modèle numérique de surface" à partir des points de la classe donnée, calculée uniquement pour
les pixels qui contiennent des points pour cette classe dans la dalle de référence.

Les différentes métriques associées aux différentes classes sont ensuite aggrégées à l'aide d'une somme pondérée par
l'importance de chaque métrique pour chaque classe

Plus de détails sur les métriques dans le fichier de définition de la classe représentant chaque métrique
(eg. `coclico/mpap0/mpap0.py` pour MPAP0)

Ce projet utilise une infracture de gestion de production par ordinateur [IGN GPAO](https://github.com/ign-gpao)
développée au sein de l'IGNF pour la parallélisation des calculs.


# Installation

Ce code utilise mamba pour l'installation de l'environnement python (et suppose qu'une version de mamba ou micromamba
existe sur l'ordinateur sur lequel on veut installer le programme)

Pour installer micromamba, voir https://mamba.readthedocs.io/en/latest/micromamba-installation.html#umamba-install

Sous windows :
* lancer `Miniforge Prompt`
* y exectuer `install_or_update.bat`

Sous linux :
* lancer un terminal
* y executer `make install`

# Usage

## Commande

Sous Windows : lancer `Miniforge Prompt`

Sous Linux : lancer un terminal

Dans les 2 cas :

Activer l'environnement conda :
```bash
conda activate coclico
```

Lancer l'utilitaire avec la commande suivante :

```bash
python -m coclico.main -i <C1> <C2> \
                       --ref <REF> \
                       --out <OUT> \
                       --gpao-hostname <GPAO_HOSTNAME> \
                       --local-store-path <LOCAL_STORE_PATH> \
                       --runner-store-path <RUNNER_STORE_PATH> \
                       --project-name <PROJECT_NAME> \
                       --config-file <WEIGHTS_FILE> \
                       --unlock
```

ou

```bash
python -m coclico.main -i <C1> <C2> \
                       -r <REF> \
                       -o <OUT> \
                       -g <GPAO_HOSTNAME> \
                       -l <LOCAL_STORE_PATH> \
                       -s <RUNNER_STORE_PATH> \
                       -p <PROJECT_NAME> \
                       -w <WEIGHTS_FILE> \
                       -u
```

options:
*  -i INPUT [INPUT ...], --input INPUT [INPUT ...]
                        Dossier(s) contenant une ou plusieurs classification(s) à comparer. ex: -i
                        /chemin/c1 chemin/c2
*  -r REF, --ref REF     Dossier contenant la classification de référence
*  -o OUT, --out OUT     Dossier de sortie de la comparaison
*  -l LOCAL_STORE_PATH, --local-store-path LOCAL_STORE_PATH
                        Chemin vers un store commun sur le PC qui lance ce script
*  -s RUNNER_STORE_PATH, --runner-store-path RUNNER_STORE_PATH
                        Chemin vers un store commun sur les clients GPAO (Unix path)
*  -g GPAO_HOSTNAME, --gpao-hostname GPAO_HOSTNAME
                        Hostname du serveur GPAO
*  -p PROJECT_NAME, --project-name PROJECT_NAME
                        Nom de projet pour la GPAO
*  -w WEIGHTS_FILE, --weights-file WEIGHTS_FILE
                        (Optionel) Fichier yaml contenant les poids pour chaque classe/métrique si on
                        veut utiliser d'autres valeurs que le défaut
*  -u, --unlock         Ajouter une étape de pré-processing pour corriger l'encodage des fichiers issus de TerraScan (unlock)
                        Attention: l'entête des fichiers d'entrée sera modifiée !



## Fichier des poids pour chaque classes (weights_file)

Le fichier des poids pour chaque classe / métrique est un fichier `yaml` du type :

```yaml
metric1:
  "1": 1
  "2": 2
  "3_4": 2

metric2:
  "1": 1
  "2": 0
  "3_4": 2
```

Au premier niveau : les métriques, qui doivent correspondre aux clés du dictionnaire `METRICS`
décrit dans `coclico/main.py`

Au 2e niveau : les classes
Chaque clé de classe peut contenir (placé entre guillemets):
* un nom de classe
* ou un sous-ensemble des classes contenues dans les fichiers LAS séparées par un tiret (`_`).
Dans ce cas, c'est dans le code de chaque métrique qu'est décidée la façon de regrouper les classes
(eg. somme du compte des points sur l'ensemble des classes pour MPAP0)

# Contribuer

Ce dépôt utiliser des pre-commits pour le formattage du code.
Avant de d'ajouter des changements, veillez à lancer `make install-precommit` pour installer les precommit hooks.

Pour lancer les tests : `make testing`