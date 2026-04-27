
# Feature

In Python :

Add a new module called "Fournisseurs" in the application interface.

This module must:
* Display a list of providers
* Be based on the existing model 'provider_model.py'
* Use the repository 'providers_repository.py' for data access

The module must allow:
* Creating a new provider
* Opening the providers folder
* Viewing, sorting, and managing providers

## Behavior

When the user opens the Fournisseurs module:
* The list of providers is loaded via providers_repository.py
* The total number of providers is displayed at the top

If there are no providers:
* Display: "Aucun fournisseur"

The user can:
* Click "Créer un nouveau fournisseur" → triggers creation flow (placeholder behavior)
* Click "Ouvrir le dossier des fournisseurs" → opens providers directory (placeholder behavior)

Table behavior:
* Columns are sortable (ascending/descending)
* Each row represents a provider
* Clicking on column headers sorts data

Actions per provider (placeholders only):
* "Lancer"
* "Modifier"
* "Supprimer"

## GUI 

Add a new module "Fournisseurs" with vertical tabs navigation

Layout: Top bar
* Button: "Créer un nouveau fournisseur"
* Button: "Ouvrir le dossier des fournisseurs"
* Provider counter: Display "X fournisseurs" or "Aucun fournisseur" if empty

Main content:
* Table displaying providers

Table columns (sortable headers): Label	-> Field name
* Guid	-> id_file
* Nom	-> provider_name
* Url	-> url
* Création	-> created_date
* Modification	-> modified_date
* Actions	-> buttons (no binding)

Actions column:
* Contains 3 buttons (placeholders only): "Lancer", "Modifier", "Supprimer"

The providers table must implement zebra striping (alternating row colors) for better readability

## Technical

Use Tkinter for GUI

Use ttk.Treeview for the table

Implement column sorting logic

Use a Presenter to:
* Fetch providers
* Format data
* Handle sorting
* Update the view

Use repository:
* providers_repository.py for all CRUD operations

Use model:
* provider_model.py as the data structure

Add a service layer if needed for:
* Sorting logic
* Data transformation

Actions buttons:
* Implemented as UI placeholders (no backend logic required yet)

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
