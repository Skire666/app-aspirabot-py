
déployé avec toml (à découvrir)
https://realpython.com/python-toml/
https://stackoverflow.com/questions/62983756/what-is-pyproject-toml-file-for



converters, pour mapper du viewmodel sur du model
https://chatgpt.com/c/69e3835e-b140-83eb-99e3-2a2f6bb733ba



E:\app-py-life-selector\src_python_2026_03_sushi_scan


Ce qu'il manque : une aide, pour savoir quoi saisir
gner des exemples en bas, rapide à copier et à adapter

trop de menu, ça serait bien de faire moins de clique
le tableau, n'a pas de colonne, on pourrait imaginer le template : ID, action, value (est ootionnel) , goto special

concernant le goto special
si succès, déroule la suite
si erreur, jump quelque part, sur un ID
(un comme à l'époque de l'assembleur)

télécharger l'iamge c'est fait
mais il ne fait rien sur le disque dur
le WebBrowserUtil deviens bordélique, à voir pour refonte
rajouter les options de human_delay

tester chaque choix dans le tableau
et regarder commne ça se comporte.

dans l'édition d'un forunissseur avec les stesp
mettre l'enum a droit d'ajouter, arreter d'ouvrir la 1er fenetre.


problème d'architecture je pense (cf  lien sur le bureau)
le controller devrait call le repository (et non le model call le repository)
le model ne contient pas le repository de ce que je vois sur internet
le model c'est du métier pur


le _repository pour save
il est déguelasse, j'ai give up
j'ai aussi la logique du filename qui fait de la merde car à chaque fois il oublie le folder dans le prefixe
donc il plante souvent, faudrait refondre ça.

setter folder 
pas dans le model
il faut setter id
c'est le repository qui le cherche
ne plus faire la logique du filename
faut juste title et id

splashscreen avant de lancer l'application
avec vérif + chargement 
genre vérifier les fournisseurs
tout ce qui est invalide, les rename en BROKEN
fait un message qui résumé les erreurs

bonus :
lorqu'on edit
sauvegarder temporaire à chaque modif
et ainsi ne pas perdre le travail

ce que j'ai pas :
C'est pas un WYSIWIG en temps réel
c'est juste un éditeur de workflow
il faudrait run une page, et tester en live l'impact d'une action
genre un bouton test ?

journal
pouvoir filtrer les erreurs selon le niveau de log
genre error, warning, info
comme VS et ses filtres


fonction :
manque l'ouverture d'une autre URL
refondre le principe de click et y intégrer une fermeture automatique des autres onglet
le click, n'est assez résilient, reprendre le code d'avant (plus robuste)

// FIN
