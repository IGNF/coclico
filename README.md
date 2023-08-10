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
Sous Windows : lancer `Anaconda Prompt`

Sous Linux : lancer un terminal

Dans les 2 cas :

Activer l'environnement conda :
```bash
conda activate coclico
```

Lancer l'utilitaire avec la commande suivante :

```bash
python coclico.main \
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

# Contribuer

Ce dépôt utiliser des pre-commits pour le formattage du code.
Avant de d'ajouter des changements, veillez à lancer `make install-precommit` pour installer les precommit hooks.

Pour lancer les tests : `make testing`