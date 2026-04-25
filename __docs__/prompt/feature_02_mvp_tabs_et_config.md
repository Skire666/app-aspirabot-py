
# Feature

In Python :
Create a desktop application using Tkinter that provides a vertical tab system with two main modules :
- Journal Module (uses the existing module log_view.py). Main module at startup.
- Configuration Module (based on model config_aspirabot_model.py)

The application must strictly follow the MVP architecture.

## GUI 

- Use Tkinter
- No business logic inside GUI

### Main layout:

Left side: Vertical tab menu
Buttons:
- "Journal"
- "Configuration"

Right side: Content area
Dynamically switches view depending on selected tab

### Journal tab:

Embed and display log_view.py

### Configuration tab:

Form-based UI:
- Label + input field for each config attribute
Buttons:
- "Save"
- "Reset"

## Devs

JSON file for configuration :

{
    "log_level": "DEBUG",
    "folder_providers": "./user_folder_providers",
    "folder_logs": "./tmp_logs",
    "user_data_dir": "./tmp_chromium_session"
}

## Architecture (Strict MVP)

### Model

* Represents data (config_aspirabot_model.py for configuration)
* No dependency on View or Presenter
* No UI or logging logic

### View (Tkinter)

* Vertical tab system
* Configuration form UI
* Controls for Configuration : Reset, Save.
* No business logic
* No direct access to Model
* Capture user interactions
* Forward events to Presenter

### Presenter

* Central orchestrator
* Receives events from View
* Retrieves for Configuration : Reset, Save.
* Updates View accordingly
* Update View in real time

### Service

* Configure, setup and expose configuration
* Call logging when needed.

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
