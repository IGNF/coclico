## Todo

### Tests

- [ ] Utiliser pytest-timeout pour avoir un timeout global sur les tests
- [ ] Test en GPAO: ajouter un timeout quand on attend qu'un job se fasse (dans wait_running_jobs)

### Metriques (objectif v1)
- [ ] ajouter MALT0 (mesure de différence altimétrique à base de modèle numérique pour chqaue classe)
- [ ] ajouter MOBJ0 (mesure de différence de nombre d'objets (amas 2D de points d'une même classe))


### Propositions

- [ ] Publier une lib

- Est-ce qu'on sort les paramètres de calcul des notes pour que l'utilisateur puisse les changer ?

### Nommage

- MetricIntrinsic (C1)
- MetricRelative (C1 / Ref)
- Note (C1 / Ref)
- Score (1 seule Note pour C1 / Ref ( Note pondérée, par classe, par metrique))

