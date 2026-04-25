# Feature

In Python :
Implement a logging UI feature using Tkinter and a strict MVP (Model - View - Presenter) architecture.

## Feature Description

### GUI 

Build a logging module with a graphical interface:

* Real-time log display (new entries appended from top to bottom)
* Logs displayed in a table with columns:
  * date
  * level with color (ERROR, WARNING, INFO, DEBUG)
  * origin (module / logger name)
  * message
* Filtering capabilities:
  * Toggle visibility of ERROR, WARNING, INFO, DEBUG
  * UI updates dynamically without restarting
  * New logs must respect active filters

## Devs

* Use Python `logging` module
* Configure file rotation:
  * Max 5 backup files
  * Max size: 8 MB per file
* Centralized logger configuration
* Logger must be reusable across the application

## Architecture (Strict MVP)

### Model

* Represents log data
* Stores logs in memory (list or similar structure)
* No dependency on View or Presenter
* No UI or logging logic

### View (Tkinter)

* Displays logs in a table
* Displays filter controls (checkboxes)
* No business logic
* No direct access to Model

Responsibilities:

* Render logs
* Capture user interactions (filter changes)
* Forward events to Presenter

### Presenter

* Central orchestrator
* Receives events from View
* Retrieves and filters data from Model
* Updates View accordingly
* Connects logging system to UI

Responsibilities:

* Handle new log events
* Apply filtering logic
* Update View in real time
* Maintain current filter state

### Service

* Configure, setup and expose logger
* Format logs properly
* Optionally push logs to Presenter (observer/callback)

### Repository

* abstraction layer for data access.
* Hides database or API details behind simple methods like get, save, and delete.
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
