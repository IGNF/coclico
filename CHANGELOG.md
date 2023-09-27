# dev
- archi: évite de refaire les job si le dossier de sortie existe, produit un log pour l'utilisateur
- ajout d'indicateurs d'options à une seule lettre dans main
- utilisation de "-" au lieur de "," comme séparateur des classes composées
- copie du fichier de poids plutôt que dump du dictionnaire parsé par coclico
- main: prend une liste de dossier de classification en entrée, pas obligatoirement 2 classifications (c1 et c2)
- résultat intermediaire, avec le score pondéré (une valeur pour chaque métrique)

# 0.2.1
- mpap0: correctif metrique relative, appliquée sur la liste des classes

# 0.2.0
- refactor
- utilisation de la GPAO
- déploiement de l'image docker sur dockerhub à chaque tag git

# 0.1.0
- première version minimale : rapport calculé à partir de 2 dossiers + un dossier de référence
- métrique MPAP0 seulement
- sans GPAO
