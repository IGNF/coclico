## Todo

### Remontée utisateur
- [ ] csv: utiliser le séparateur ';'. Quand on lit, et quand on écrit.
- [ ] classes composées: utiliser des '_' au lieu des '-' actuel

### Tests

- [ ] Utiliser pytest-timeout pour avoir un timeout global sur les tests
- [ ] Test en GPAO: ajouter un timeout quand on attend qu'un job se fasse (dans wait_running_jobs)

### Seconde métrique

- [ ] Réaliser une seconde métrique
- [ ] Penser à supprimer la metric Mpap0_test. et nettoyage dans la class Map0 (parametre à la création, option -t dans le main le mpap0 relative)

### Robustesse

- [x] rendre robuste aux fichiers terrascan mal encodés (job séparé avant les métriques avec option pour l'activer)

### Propositions

- [ ] Publier une lib

- Est-ce qu'on sort les paramètres de calcul des notes pour que l'utilisateur puisse les changer ?

### Nommage

- MetricIntrinsic (C1)
- MetricRelative (C1 / Ref)
- Note (C1 / Ref)
- Score (1 seule Note pour C1 / Ref ( Note pondérée, par classe, par metrique))

