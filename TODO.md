## Todo

- deploiement: fonctionnel sous windows
  - fichier .bat update.bat (install & update basé sur mamba update)

- Mise en GPAO
  - Test de la GPAO 
    - Serveur GPAO en local avec docker compose
    - Client GPAO qui lance le test (verifier temps d'attente du client)


## première métrique MPAP0 (métrique point à point): np point par class dans C1 / ref
  
  - ok - 1 json vide par dalle
  - 1 JSON par dalle
    <!-- calculer metricRelative par classe (sol, bati) -->
    <!-- calculer score -->
    - note par classe (sol, bati)
    - note pondéréé

  - Merger les dalles :
    - geojson qui regroupe
      - les note
      - les notes poindérés
    - note globale (pour tous les las)
    - note globlale pondérées


## Nommage

MetricIntrinsic (C1)

MetricRelative (C1 / Ref)

Score (= comparaison)

Note (= visible par l'utilisateur)
