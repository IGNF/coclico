## Todo

- deploiement: fonctionnel sous windows
  - fichier .bat update.bat (install & update basé sur mamba update)

- Mise en GPAO
  - Test de la GPAO
    - Serveur GPAO en local avec docker compose
    - Client GPAO qui lance le test (verifier temps d'attente du client)


## première métrique MPAP0 (métrique point à point): np point par class dans C1 / ref
  - ok un csv rempli avec des fausses notes par dalle
  - ok génération du compte de point (metrique intrinèque)
  - ok : comparaison entre les comptes de points (score / metric relative)
  - ok : note à partir de la métrique relative

## Merge des dalles et des métriques
    - done : merge les différentes métriques / classes /dalles dans un grand csv
    - done : stats sur l'ensemble des dalles pour chaque métrique en csv
    - done : notes pondérées à partir des stats pour chaque métrique / classe en csv
    - todo : donner les poids des différentes classes / des différentes métriques (dans un fichier de config?)


## Nommage

MetricIntrinsic (C1)

MetricRelative (C1 / Ref)

Score (= comparaison)

Note (= visible par l'utilisateur)
