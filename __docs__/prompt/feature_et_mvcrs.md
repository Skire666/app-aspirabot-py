Nous allons refondre l'onglet 'Fournisseurs' et le refaire intégralement.

J'ai besoin d'un cadre "Header" en haut, avec dedans :
- un bouton "Créer un fournisseur", aligné à gauche.
- aligné à droite un compteur qui liste le nombre de fournisseurs disponibles.

En dessous, dans un 2ème cadre :
- mettre un tableau qui liste les fournisseurs existants.
- Si vide, affiche "(Aucun fournisseur).
- Si existant, liste les fournisseurs.

Composition du tableau :
- Chaque ligne possède les colonnes suivantes : Nom, URL, Date de création. Bouton "Supprimer" (avec confirmation), et bouton "Modifier".

Lorsque l'utilisateur clique sur "Créer un fournisseur" il est redirigé vers l'onglet "Mettre à jour" avec des données par défaut.
Lorsque l'utilisateur clique sur le bouton "Modifier" dans une ligne, il est redirigé vers l'onglet "Mettre à jour" avec les données du fournisseurs.
Si l'utilisateur clique sur le bouton "Supprimer", une boite de confirmation de suppression apparait. Si oui, supprime le fournisseur en mémoire ainsi que sur le disque dur. Si non, ne fait rien.

Contrainte :
Respecte le design pattern architectural : Model, Controller, View, ViewModel, Service, et Repository.

- La partie lecture/écriture est géré par le Repository
- La partie donnée est gérée par le Model.
- Le Controller sert de passe plat.
- La View utilise le Controller.
- Le Service incarne le domaine.
- Le ViewModel est mappé sur la View, et sert à gérer les entrées de l'utilisateur.

