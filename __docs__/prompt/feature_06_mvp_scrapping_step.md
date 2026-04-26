In Python :

Add a WYSIWYG interface to manage scraping workflow steps for a provider.

The steps are stored in `provider_model.py` inside the variable `steps`.
Each step is an instance of `step_scrapping_model.py`.

The goal is to allow users to visually create, edit, reorder, and delete scraping steps that will later be executed during web scraping.

Supported step types:
- Open a URL
- Wait for X seconds
- Refresh page

Each step must store its type and associated value (e.g., URL or duration).

## Behavior

- The user can view all steps in a list.
- The user can:
  - Add a new step via a dropdown selection.
  - Configure the step via a popup dialog (input value required).
  - Modify an existing step via the same dialog.
  - Delete a selected step.
  - Reorder steps (move up / move down).
  - Clear all steps with confirmation.

- The "Modify", "Delete", "Move Up", and "Move Down" buttons are only enabled when a step is selected.

- When adding or modifying a step:
  - A modal window opens.
  - The form adapts to the selected step type:
    - URL → text input
    - Wait → numeric input (seconds)
    - Refresh → no input or simple confirmation

- When saving the provider:
  - All steps are serialized and saved into JSON via the model.

## GUI

In `ProviderView`:

- In the "Workflow" section:
  - Add a full-width list displaying steps in order.

- Below the list, add controls:

Left-aligned buttons:
- "Ajouter"
  - Followed by a dropdown:
    - "Sélectionner..."
    - "Ouvrir une URL"
    - "Attendre X secondes"
    - "Rafraichir page"
  - On click:
    - If valid option selected → open corresponding modal dialog

- "Modifier"
  - Enabled only if a step is selected
  - Opens edit modal with pre-filled values

- "Supprimer"
  - Enabled only if a step is selected
  - Removes the selected step

- "Monter"
  - Enabled only if a step is selected and not first
  - Swap with previous step

- "Descendre"
  - Enabled only if a step is selected and not last
  - Swap with next step

Right-aligned:
- "Effacer tout"
  - Clears entire list after confirmation dialog

Modal dialogs:
- Dynamic based on step type
- Include validation before submission
- Return structured data to Presenter

## Technical

- Use Tkinter for UI
- Use Toplevel for modal dialogs
- Use messagebox for confirmations

- Steps must be represented as Python objects (StepScrappingModel)
- Serialization to JSON must be handled cleanly (via repository or service)
- Ensure UI state is always in sync with Presenter
- No direct mutation of Model from View

## Architecture (Strict MVP)

### Model

* `ProviderModel`
  - Contains `steps: List[StepScrappingModel]`

* `StepScrappingModel`
  - Attributes:
    - type (enum/string)
    - value (str/int/None)

* No dependency on View or Presenter
* No UI or logging logic

### View (Tkinter)

* Displays:
  - Steps list
  - Buttons
  - Dialogs

* Emits events:
  - on_add_step(type)
  - on_edit_step(index)
  - on_delete_step(index)
  - on_move_up(index)
  - on_move_down(index)
  - on_clear_all()

* No business logic
* No direct access to Model

### Presenter

* Central orchestrator
* Holds current steps state
* Handles:
  - Add / Edit / Delete / Reorder
  - Validation
  - UI updates

* Communicates with Services for transformations
* Updates View in real time

### Service

* StepService:
  - Create step from input
  - Validate step data
  - Serialize/deserialize steps

### Repository

* ProviderRepository:
  - Save/load provider JSON
  - Persist steps as JSON structure

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
* One class per file
* Strict Python (VERY STRICT)

# Goal

* Fully functional WYSIWYG workflow editor
* Steps persisted in JSON via ProviderModel
* Clean separation of concerns (strict MVP)
* Maintainable, testable, scalable code


