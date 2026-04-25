Je suis développeur python, et j'ai besoin d'un prompt agentique (affichage brut, en ascii, copier collable). 
Renseigne le prompt que je vais te donner avec les informations suivantes :

- Dans l'interface, ajouter un nouveau module 'Modification' dont les onglets verticaux.
- Ce nouveau module sert à modifier un fournisseur.
- Il est grisé au démarrage de l'application.
- Lorsque l'on est sur l'onglet 'Fournisseurs' : Cliquer sur le bouton 'Créer un nouveau fournisseur' ou sur l'action "Modifier' d'une ligne, ouvre le module 'Modifiation' (il n'est plus grisé).
- Un fournisseur est basé sur le model 'provider_model.py' et utilise le repository 'providers_repository.py'
- Cette interface contient 4 zones : "Informations", "Métadonnées", "Workflow", et "Footer"
- La zone "Informations" est en haut à gauche, et occupe 50% de la largeur. Il contient 4 champs 'Nom' (texte éditable 'provider_name'), 'URL' (texte éditable 'url'), 'Browser affiché' (case à cocher 'browser_displayed'), Automatisation obfusqué (case à cocher 'automation_obfuscated').
- La zone 'Métadonnées', située à droite de la zone 'Informations'. Occupe 50% de la largeur. Il contient 4 champs 'Guid' (texte en lecture seule 'provider_guid'), 'Version' (texte éditable 'version'), 'Création' (date en lecture seule 'created_date'), 'Modification' (date en lecture seul 'modified_date').
- La zone 'Workflow'. Pour l'instant, laisse un cadre vide (placeholder).
- La zone footer contient 2 boutons :
	-- "Annuler" : Annule les modifications, vide l'IHM des valeurs, et retourne sur l'onglet 'Fournisseurs', et grise le module "Modifications".
	-- "Sauvegarder" : Sauvegarde les données JSON, vide l'IHM des valeurs, et retourne sur l'onglet 'Fournisseurs', et grise le module "Modifications". Cas spécial : Si nouveau fichier, mais qu'il existe déjà un fichier, demander la confirmation à l'utilisateur.


Voici le prompt d'exemple (remplace les XXXX et extrapole les consignes) :

# Feature

In Python :

XXXX

## Behavior

XXXX

## GUI 

XXXX

## Technical

XXXX

## Architecture (Strict MVP)

### Model

* Represents data
* No dependency on View or Presenter
* No UI or logging logic

### View (Tkinter)

* No business logic
* No direct access to Model
* Capture user interactions
* Forward events to Presenter

### Presenter

* Central orchestrator
* Receives events from View
* Updates View accordingly
* Update View in real time

### Service

* A service encapsulates business logic.
* It processes data and applies domain rules independently of the UI.
* The Presenter calls services to perform actions and retrieve results.
* Services help keep the Presenter thin and focused on presentation logic.

### Repository

* abstraction layer for data access.
* Hides read/write details behind simple methods like read, create, update and delete.
* Keeps the presenters and business logic focused on behavior, not storage.
* No dependency on View
* No UI logic

### Forbidden:

* View → Model
* Model → View
* Business logic inside View

## Project Structure

__src__/
├── models/
├── views/
├── presenters/
├── repositories/
├── services/
└── main.py

## Code Quality Requirements

* Follow PEP8
* Use Google-style docstrings (in English) for all classes and methods
* Clear naming conventions
* Small, focused methods
* Type hints where relevant
* One class per file.
* Strict Python (VERY STRICT)

# Goal

* Implemented functionality
* Full working code with all files
* Proper separation of concerns (strict MVP)
* Clean, maintainable, and testable code
