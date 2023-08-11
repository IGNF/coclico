# coclico

COmparaison de CLassIfication par rapport à une référence COmmune

# Installation

Ce code utilise conda pour l'installation de l'environnement python (et suppose
qu'une version de conda existe sur l'ordinateur sur lequel on veut installer le
programme)

Sous windows :
* lancer `Anaconda Prompt`
* y exectuer`install.bat`

Sous linux :
* lancer un terminal
* y executer `make install`

Note : Sous linux, on utilise mamba pour gérer l'environnement conda.
Pour installer micromamba, voir https://mamba.readthedocs.io/en/latest/micromamba-installation.html#umamba-install

# Usage

## Commande

Sous Windows : lancer `Anaconda Prompt`

Sous Linux : lancer un terminal

Dans les 2 cas :

Activer l'environnement conda :
```bash
conda activate coclico
```

Lancer l'utilitaire avec la commande suivante :

```bash
python -m coclico.main \
    --c1 <C1> \
    --c2 <C2> \
    --ref <REF> \
    --out <OUT>  \
    --weights_file <WEIGHTS_FILE>
```


options:
  --c1 C1               Dossier C1 contenant une des classifications à comparer
  --c2 C2               Dossier C2 contenant l'autre classification à comparer
  --ref REF             Dossier contenant la classification de référence
  --out OUT             Dossier de sortie de la comparaison
  --weights_file WEIGHTS_FILE
                        (Optionel) Fichier yaml contenant les poids pour chaque classe/métrique si on veut utiliser d'autres valeurs que le défaut (les valeurs par défaut sont dans `configs/metrics_weights.yaml`)

## Fichier des poids pour chaque classes (weights_file)

Le fichier des poids pour chaque classe / métrique est un fichier `yaml` du type :

```yaml
metric1:
  "1": 1
  "2": 2
  "3,4": 2

metric2:
  "1": 1
  "2": 0
  "3,4": 2
```

Au premier niveau : les métriques, qui doivent correspondre aux clés du dictionnaire `METRICS`
décrit dans `coclico/main.py`

Au 2e niveau : les classes
Chaque clé de classe peut contenir (placé entre guillemets):
* un nom de classe
* ou un sous-ensemble des classes contenues dans les fichiers LAS séparées par une virgule (`,`).
Dans ce cas, c'est dans le code de chaque métrique qu'est décidée la façon de regrouper les classes
(eg. somme du compte des points sur l'ensemble des classes pour MPAP0)

# Contribuer

Ce dépôt utiliser des pre-commits pour le formattage du code.
Avant de d'ajouter des changements, veillez à lancer `make install-precommit` pour installer les precommit hooks.

Pour lancer les tests : `make testing`