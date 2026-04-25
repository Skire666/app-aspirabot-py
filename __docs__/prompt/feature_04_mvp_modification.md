# Feature

In Python :
Add a new module called "Modification" in the application interface.  
This module allows creating and editing a provider.

## Behavior

On application startup:
  - The "Modification" module is disabled (greyed out)

From the "Fournisseurs" tab:
  - Clicking "Créer un nouveau fournisseur":
    - Opens the "Modification" module
    - Enables the module
    - Loads empty fields (creation mode)

  - Clicking "Modifier" on an existing supplier:
    - Opens the "Modification" module
    - Enables the module
    - Loads the selected supplier data (edit mode)

From "Modification" tab :
- "Annuler" button:
  - Cancels all modifications
  - Clears all UI fields
  - Returns to "Fournisseurs" tab
  - Disables (greys out) the "Modification" module

- "Sauvegarder" button:
  - Saves supplier data as JSON via repository
  - Clears all UI fields
  - Returns to "Fournisseurs" tab
  - Disables (greys out) the "Modification" module
  - Special case:
    - If creating a new supplier and a file already exists:
      - Ask user confirmation before overwrite

## GUI

The "Modification" module uses vertical tabs layout and contains 4 zones:

### 1. Informations (Top-left, 50% width)

Fields:
- "Nom" → editable text (`provider_name`)
- "URL" → editable text (`url`)
- "Browser affiché" → checkbox (`browser_displayed`)
- "Automatisation obfusqué" → checkbox (`automation_obfuscated`)

### 2. Métadonnées (Top-right, 50% width)

Fields:
- "Guid" → read-only text (`provider_guid`)
- "Version" → editable text (`version`)
- "Création" → read-only date (`created_date`)
- "Modification" → read-only date (`modified_date`)

### 3. Workflow

- Placeholder empty frame
- No logic yet
- Reserved for future workflow configuration

### 4. Footer

Contains 2 buttons:
- "Annuler"
- "Sauvegarder"

## Technical

- Use `provider_model.py` as the data structure
- Use `providers_repository.py` for persistence
- JSON-based storage

- The Presenter must:
  - Handle mode (create vs edit)
  - Populate fields
  - Validate data before saving
  - Handle overwrite confirmation

- The Service layer must:
  - Handle business rules
  - Manage timestamps (created_date, modified_date)
  - Handle GUID generation for new providers
  - Validate uniqueness when required

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