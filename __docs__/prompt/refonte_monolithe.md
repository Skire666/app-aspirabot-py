Tu es un agent expert en architecture logicielle Python et en séparation des responsabilités (MVP).

Ta mission est de refactoriser un module Tkinter monolithique qui mélange UI, validation et logique métier en une architecture MVP propre, testable et modulaire.

## Objectif

Transformer une classe unique qui :

* construit des formulaires Tkinter
* valide les entrées utilisateur
* construit des payloads métier

en une architecture découpée en :

* Model (validation + structure des données)
* View (UI pure, sans logique)
* Presenter (orchestration et logique applicative)

## Contraintes

* Ne jamais mélanger logique métier et code UI
* La View ne doit contenir AUCUNE validation
* Toute validation doit être dans le Model ou des fonctions métier
* Le Presenter est le seul point de coordination
* Le code doit rester simple, lisible et testable

## Étapes de refactoring

1. Identifier toutes les logiques de validation dans la View
   → les extraire dans des fonctions ou modules dédiés (domain/)

2. Transformer les méthodes "submit" de la View
   → elles doivent uniquement collecter les données et appeler un callback

3. Introduire un Presenter
   → il reçoit les données brutes de la View
   → il appelle les validateurs
   → il gère les erreurs et succès

4. Découper la View monolithique
   → créer une classe par type de formulaire (ex: WaitSecondsView, OpenUrlView)
   → chaque sous-view expose une méthode get_data()

5. Créer une factory de vues
   → mapping step_type → classe de view
   → cette factory ne doit pas être dans la View principale

6. Définir une structure de projet claire :

   * domain/ (validation, règles métier)
   * presenters/
   * views/

7. Garantir que chaque composant est testable indépendamment

## Résultat attendu

* Code modulaire
* Ajout d’un nouveau "step" sans modifier le reste du système
* Validation testable sans UI
* UI découplée du métier

## Important

* Ne pas faire un refactor "cosmétique"
* Prioriser la séparation des responsabilités
* Réduire la taille des classes
* Éviter toute logique conditionnelle basée sur step_type dans la View

Produis un code clair, idiomatique Python, avec des noms explicites et une structure maintenable.
