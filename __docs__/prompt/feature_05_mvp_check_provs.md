
# Feature

In Python :
Add a validation feature inside the 'Fournisseurs' module (provider_view.py) that allows users to verify the integrity and consistency of supplier data files.

This feature must:
- Scan all files located in the providers directory
- Validate that each file contains a properly formatted GUID
- Ensure that the filename matches the GUID contained within the file
- Automatically handle invalid files by renaming and moving them to a broken folder
- Provide a clear report of the validation results to the user

## Behavior

- When the user clicks the validation button:
  - The system scans the providers directory
  - For each file:
    - Read its content
    - Extract the GUID from the data
    - Validate GUID format
    - Compare the GUID with the filename (without extension)

- Validation rules:
  - A GUID is valid
  - Filename must exactly match the GUID

- If invalid:
  - Rename file to: `invalid_<original_name><timestamp>`
  - Move it to `./broken/`
  - Log the reason (invalid GUID / mismatch filename)

- At the end:
  - Display a summary:
    - Total files processed
    - Number of valid files
    - Number of invalid files
    - List of errors per file

## GUI 

- Add a button in the `Fournisseurs` view:
  - Label: `Valider les fournisseurs`

- When clicked:
  - Disable button during processing
  - Show a progress indicator (loading state / count providers)
  - Display results in a popup with clear success / error.

## Technical

- Use repository and model for operations
- Ensure `broken` directory exists (create if missing)

- Handle edge cases:
  - Empty files
  - Missing GUID field
  - Corrupted content
  - Non-readable files

- do logging

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
