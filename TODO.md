## Todo

### Archi et première métrique MPAP0

- [ ] résultat intermediaire manquant : score c1 pondéré (poids des classes). Une valeur pour chaque metrique.
- [ ] utiliser une liste de dossiers au lieu de `c1` et `c2` en utilisant le nom de dossier comme identifiant
- [ ] Ne pas refaire les jobs quand les dossiers existent déjà
- [ ] Ne pas écraser un fichier de score et le compléter
- [ ] Fonctionner avec des classes différentes pour chaque métrique
  - [ ] ajouter un test avec un fichier de config dans lequel : Une classe qui définie pour une métrique, mais pas dans une autre métrique. (pas definie= la ligne n'est pas écrite)
- [ ] Main, options à une seule lettre

### Tests

- [ ] Utiliser pytest-timeout pour avoir un timeout global sur les tests
- [ ] Test en GPAO: ajouter un timeout quand on attend qu'un job se fasse (dans wait_running_jobs)

### Seconde métrique

- [ ] Réaliser une seconde métrique
- [ ] Penser à supprimer la metric Mpap0_test. et nettoyage dans la class Map0 (parametre à la création, option -t dans le main le mpap0 relative)

### Robustesse

- [ ] rendre robuste aux fichiers terrascan mal encodés (job séparé avant les métriques avec option pour l'activer)

### Propositions

- [ ] Publier une lib

- Est-ce qu'on sort les paramètres de calcul des notes pour que l'utilisateur puisse les changer ?

### Nommage

- MetricIntrinsic (C1)
- MetricRelative (C1 / Ref)
- Note (C1 / Ref)
- Score (1 seule Note pour C1 / Ref ( Note pondérée, par classe, par metrique))

