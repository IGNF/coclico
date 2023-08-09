# coclico

COmparaison de CLassIfication par rapport à une référence COmmune

# Usage
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
  --c2 C2               Dossier C2 contenant l'autre classifications à comparer
  --ref REF             Dossier contenant la classification de référence
  --out OUT             Dossier de sortie de la comparaison
  --weights_file WEIGHTS_FILE
                        (Optionel) Fichier yaml contenant les poids pour chaque classe/métrique si on veut utiliser d'autres valeurs que le défaut (les valeurs par défaut sont dans `configs/metrics_weights.yaml`)

# Contribuer
Ce dépôt utiliser des pre-commits pour le formattage du code.
Avant de d'ajouter des changements, veillez à lancer `make install-precommit` pour installer les precommit hooks.