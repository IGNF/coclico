## Todo

- deploiement: fonctionnel sous windows
  - done : install.bat basé sur conda update
  - todo : fichier .bat update.bat (install & update basé sur mamba update)

- Mise en GPAO
  - Test de la GPAO
    - Serveur GPAO en local avec docker compose
    - Client GPAO qui lance le test (verifier temps d'attente du client)


## première métrique MPAP0 (métrique point à point): np point par class dans C1 / ref
  - ok un csv rempli avec des fausses notes par dalle
  - ok génération du compte de point (metrique intrinèque)
  - ok : comparaison entre les comptes de points (score / metric relative)
  - ok : note à partir de la métrique relative
  - ok: regroupement de classes 3, 4, 5

## Merge des dalles et des métriques
    - done : merge les différentes métriques / classes /dalles dans un grand csv
    - done : stats sur l'ensemble des dalles pour chaque métrique en csv
    - done : notes pondérées à partir des stats pour chaque métrique / classe en csv
    - done : donner les poids des différentes classes / des différentes métriques (dans un fichier de config?)
    - todo: merge avec des résultats précédents
    - todo : fonctionner avec des classes différentes pour chaque métrique

## paramétrisation
    - done : donner les poids des différentes classes / des différentes métriques (dans un fichier de config)
    - todo : est-ce qu'on sort les paramètres de calcul des notes pour que l'utilisateur puisse les changer ? Est-ce qu'on les laisse en dur dans le code ? (pour le moment dans le code)

## Nommage

MetricIntrinsic (C1)

MetricRelative (C1 / Ref)

Score (= comparaison)

Note (= visible par l'utilisateur)
