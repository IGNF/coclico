## Todo

### Programme utilisable

- Publier l'image Dockerhub
  - [x] Revérifier le code (chemin privé), qui devient public
  - [x] via Github Action, quand on fait un tag
  - [] tester l'image avant de publier sur github (implique d'isoler les tests qui doivent tourner dans l'image docker)

- Fonctionnel sous windows
  - install.bat basé sur MAMBA update
  - example.bat

- Environnement de Dev:
  - Script Ansible
  - Verifier à la main, que l'example fonctionne

### Archi et première métrique MPAP0

- Merger les scores de chaque classification: Notes pondérées à partir des résultats pour chaque métrique / classe en csv
- Merge avec des résultats précédents (pour plus tard)
- Fonctionner avec des classes différentes pour chaque métrique
  - ajouter un test avec un fichier de config dans lequel : Une classe qui définie pour une métrique, mais pas dans une autre métrique.


### Tests

  - Faire un test sous Windows (executé par une VM Windows)

  - Séparer les tests qui utilisent la GPAO (conftest.py run slow, ou plutôt run_gpao)

  - Test en GPAO: vérifier le timeout du client


### Seconde métrique
  - Réaliser une seconde métrique
  - Penser à supprimer la metric Mpap0_test. et nettoyage dans la class Map0 (parametre à la création, option -t dans le main le mpap0 relative)



### Poposition
    - Est-ce qu'on sort les paramètres de calcul des notes pour que l'utilisateur puisse les changer ?


### Nommage

MetricIntrinsic (C1)

MetricRelative (C1 / Ref)

Note (C1 / Ref)

Score (1 seule Note pour C1 / Ref ( Note pondérée, par classe, par metrique))

