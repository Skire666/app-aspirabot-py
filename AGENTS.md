# AGENTS.md — Aspirabot

## Project Description

**Aspirabot** is a web scraping tool with a Tkinter-based GUI.
It allows users to create, configure, and execute data extraction or web automation workflows visually.
The browser is simulated via **Playwright** (Chromium) to bypass standard antibot detection.

---

## Architecture

The project follows a strict **Model-View-Presenter** pattern adapted to Tkinter.

### Folder layout

```
__src__/
├── models/         # Business entities and data structures (domain)
├── views/          # Tkinter GUI components (passive, no logic)
├── view_models/    # UI state holders built around tk.*Var
├── presenters/     # Orchestration: wires ViewModel callbacks to services
├── repositories/   # Data read/write layer (files, JSON…)
├── services/       # Business logic and domain rules
├── interfaces/     # Protocol-based contracts
├── validators/     # FluentValidation-style domain validators
├── shared/         # Cross-cutting utilities (enums, i18n, helpers)
└── main.py         # Application entry point and composition root
```

### MVP — roles

| Layer        | Responsibility                                                                                              | Forbidden                                                  |
|--------------|-------------------------------------------------------------------------------------------------------------|------------------------------------------------------------|
| `Model`      | Domain entities and value objects.                                                                          | Knowing about UI, Tkinter, or persistence format.          |
| `Repository` | Read/write persistent data (JSON files, config). Sole owner of I/O.                                         | Business rules, Tkinter, UI strings.                       |
| `Service`    | Business logic, domain rules, orchestration of repositories. UI-agnostic (would survive a CLI rewrite).     | Importing `View`, `Presenter`, `ViewModel`, or `tkinter`.  |
| `ViewModel`  | Holds **all** UI state as `tk.StringVar` / `BooleanVar` / `IntVar`. Computes derived state via `trace_add`. Exposes action methods (`submit()`, `cancel()`…) and `bind_xxx(callback)` registration hooks. | Calling services, calling repositories, touching widgets.  |
| `Presenter`  | Receives the `ViewModel` and a `Service`. Registers callbacks on the VM, mutates the VM's Vars in response. | Touching widgets, importing `tkinter`, importing a `View`. |
| `View`       | Builds widgets and binds them to VM Vars (`textvariable=`, `variable=`) and adds `trace_add` for non-Var bindings (e.g. enabling/disabling a button). Forwards user actions by calling VM methods. | Any conditional logic, any service call, any direct mutation of state. |

### MVP + rules (strictly enforced)

- The `View` is **passive**: widget construction + binding. No `if/else` on domain data, no service call, no validation.
- All UI state — including derived state like `can_submit` — lives in the `ViewModel` as `tk.*Var`.
- Derived state is recomputed inside the ViewModel via `trace_add("write", ...)` on the source Vars, **never** in the View.
- User actions (button clicks, etc.) call a method on the ViewModel (`vm.submit()`), which dispatches to a handler registered by the Presenter through `vm.bind_xxx(callback)`.
- The `Presenter` never touches a widget — it only mutates VM Vars.
- The `Repository` is the **only** layer allowed to read/write persistent data.
- Every `tk.*Var` must be stored as an **instance attribute** on the ViewModel — local-only Vars get garbage-collected and silently break bindings.

---

## Dependency Map

**Allowed import direction — strictly one way:**

| Importing layer | May import from                                              | Must NEVER import from                                   |
|-----------------|--------------------------------------------------------------|----------------------------------------------------------|
| `View`          | `ViewModel`, `interfaces/`, `shared/`, `tkinter`             | `Service`, `Repository`, `Model`, `Presenter`            |
| `ViewModel`     | `shared/`, `tkinter`                                         | `View`, `Presenter`, `Service`, `Repository`, `Model`    |
| `Presenter`     | `ViewModel`, `Service`, `Model`, `interfaces/`, `shared/`, `validators/` | `View`, `Repository`, `tkinter`              |
| `Service`       | `Repository`, `Model`, `interfaces/`, `shared/`, `validators/` | `View`, `ViewModel`, `Presenter`, `tkinter`            |
| `Repository`    | `Model`, `shared/`                                           | `View`, `ViewModel`, `Presenter`, `Service`, `tkinter`   |
| `Model`         | `shared/`                                                    | Everything else                                          |
| `ViewModel` (Vars only) | `tkinter`                                            | `Service`, `Repository`, `Model`                         |

> If adding an import creates a cycle or runs against an arrow above, the design is wrong — refactor.

> Presenter can also reads/writes ViewModel Vars

> **Why ViewModel cannot import Model:** the ViewModel speaks Tkinter Vars, the Model speaks domain objects. Mapping between the two is the **Presenter's job**. Keeping the VM Model-free guarantees the VM stays a pure UI-state container.

---

## File Naming Convention

Every Python file in an MVP layer is suffixed with its layer name. This makes layer identity readable from any import statement.

| Folder          | File suffix         | Example                                |
|-----------------|---------------------|----------------------------------------|
| `models/`       | `_model.py`         | `provider_model.py`, `app_state_model.py` |
| `services/`     | `_service.py`       | `scraping_service.py`                  |
| `repositories/` | `_repository.py`    | `config_repository.py`                 |
| `presenters/`   | `_presenter.py`     | `executor_presenter.py`                |
| `view_models/`  | `_view_model.py`    | `scenario_edit_view_model.py`          |
| `views/`        | `_view.py`          | `scenario_edit_view.py`                |
| `validators/`   | `_validator.py`     | `scraping_validator.py`                |
| `interfaces/`   | `i_*.py`            | `i_scraping_view.py`                   |

The class inside a file is always the PascalCase counterpart of the file name (e.g. `provider_model.py` → `ProviderModel`, `scenario_edit_view_model.py` → `ScenarioEditViewModel`).

---

## Service vs Presenter — Decision Rule

A condition or transformation belongs in the **Service** if it is a **domain rule**:
it would still be true if the application had no GUI at all (CLI, API, test runner).

A condition belongs in the **Presenter** if it is a **coordination decision**:
it only exists because the UI needs to decide what to show or what to call next.

| Question                                                       | Answer → layer  |
|----------------------------------------------------------------|-----------------|
| "Would this rule exist in a headless version of the app?"     | Yes → **Service**   |
| "Does this only make sense because of what the View expects?" | Yes → **Presenter** |
| "Am I transforming or validating domain data?"                | → **Service**       |
| "Am I deciding which VM Var to update, or in what order?"     | → **Presenter**     |

```python
# BAD — business rule hidden inside a Presenter
def on_submit(self) -> None:
    url = self._vm.url_var.get()
    if not url.startswith("https://"):   # ← domain rule, belongs in a Service
        self._vm.error_message_var.set("URL invalide.")
        return
    self._service.start_scraping(url)

# GOOD — Presenter coordinates only; Service owns the rule
def on_submit(self) -> None:
    url = self._vm.url_var.get()
    try:
        self._service.start_scraping(url)        # raises ScrapingError if URL invalid
    except ScrapingError as e:
        self._vm.error_message_var.set(str(e))
```

---

## ViewModel — UI State Container

The `ViewModel` is the **only** owner of UI state. It is built around Tkinter's variable classes
(`tk.StringVar`, `tk.BooleanVar`, `tk.IntVar`) and exposes:

1. **Source Vars** — bound to user inputs via `textvariable=` / `variable=`.
2. **Derived Vars** — recomputed via `trace_add("write", ...)` on source Vars.
3. **Action methods** — `submit()`, `cancel()`, etc., which invoke handlers registered by the Presenter.
4. **Binding hooks** — `bind_submit(callback)`, `bind_cancel(callback)`, … called once by the Presenter at composition time.

### Location and naming

- Folder: `__src__/view_models/`
- File: `<module>_view_model.py` (e.g. `scenario_edit_view_model.py`)
- Class: `<Module>ViewModel` in PascalCase (e.g. `ScenarioEditViewModel`)

### Definition rules

- Every `tk.*Var` must be assigned to `self.` — never use a local-scoped Var (silent GC).
- Derived state is computed **inside** the VM via `trace_add("write", ...)`; never in the View.
- Action methods are short and only dispatch to a registered callback.
- Guard the setters of derived Vars against binding loops (re-entrancy).
- Debounce `trace_add` reactions that are expensive to recompute.
- The VM never imports a Service, a Repository, a Model, or a View.

### Canonical pattern

```python
# view_models/scenario_edit_view_model.py
import tkinter as tk
from typing import Callable

class ScenarioEditViewModel:
    """UI state and action hooks for the scenario edit form.

    Source Vars are bound to widgets via textvariable=/variable=.
    Derived Vars (e.g. can_submit) are recomputed automatically on every write
    to the relevant source Vars and never touched by the View.
    """

    def __init__(self, master: tk.Misc) -> None:
        # Source Vars — bound to widgets in the View
        self.name_var = tk.StringVar(master=master, value="")
        self.url_var = tk.StringVar(master=master, value="")
        self.is_active_var = tk.BooleanVar(master=master, value=False)

        # Status / message Vars
        self.error_message_var = tk.StringVar(master=master, value="")
        self.is_busy_var = tk.BooleanVar(master=master, value=False)

        # Derived Vars — recomputed via trace_add, never set from the View
        self.can_submit_var = tk.BooleanVar(master=master, value=False)

        # Re-entrancy guard for derived Vars
        self._updating_derived = False

        # Registered Presenter callbacks
        self._on_submit: Callable[[], None] | None = None
        self._on_cancel: Callable[[], None] | None = None

        # Wire derived-state recomputation
        for var in (self.name_var, self.url_var, self.is_busy_var):
            var.trace_add("write", self._recompute_can_submit)
        # Initial computation
        self._recompute_can_submit()

    # ----- Derived state -----

    def _recompute_can_submit(self, *_: object) -> None:
        """Recompute can_submit_var whenever a source Var changes."""
        if self._updating_derived:
            return
        self._updating_derived = True
        try:
            name_ok = bool(self.name_var.get().strip())
            url_ok = bool(self.url_var.get().strip())
            ready = name_ok and url_ok and not self.is_busy_var.get()
            if self.can_submit_var.get() != ready:
                self.can_submit_var.set(ready)
        finally:
            self._updating_derived = False

    # ----- Presenter binding hooks -----

    def bind_submit(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler invoked on submit()."""
        self._on_submit = callback

    def bind_cancel(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler invoked on cancel()."""
        self._on_cancel = callback

    # ----- Action methods called by the View -----

    def submit(self) -> None:
        """Dispatch the submit action to the registered Presenter callback."""
        if self._on_submit is not None:
            self._on_submit()

    def cancel(self) -> None:
        """Dispatch the cancel action to the registered Presenter callback."""
        if self._on_cancel is not None:
            self._on_cancel()
```

### View — binds to the ViewModel, contains zero logic

```python
# views/scenario_edit_view.py
import tkinter as tk
from tkinter import ttk

from view_models.scenario_edit_view_model import ScenarioEditViewModel

class ScenarioEditView(ttk.Frame):
    """Passive widget tree bound to the ScenarioEditViewModel."""

    def __init__(self, master: tk.Misc, vm: ScenarioEditViewModel) -> None:
        super().__init__(master)
        self._vm = vm

        # Build static widget tree
        ttk.Label(self, text="Nom :").grid(row=0, column=0, sticky="w")
        ttk.Entry(self, textvariable=vm.name_var).grid(row=0, column=1)

        ttk.Label(self, text="URL :").grid(row=1, column=0, sticky="w")
        ttk.Entry(self, textvariable=vm.url_var).grid(row=1, column=1)

        ttk.Checkbutton(self, text="Actif", variable=vm.is_active_var) \
            .grid(row=2, column=0, columnspan=2, sticky="w")

        ttk.Label(self, textvariable=vm.error_message_var, foreground="red") \
            .grid(row=3, column=0, columnspan=2, sticky="w")

        self._submit_btn = ttk.Button(self, text="Valider", command=vm.submit)
        self._submit_btn.grid(row=4, column=0)
        ttk.Button(self, text="Annuler", command=vm.cancel).grid(row=4, column=1)

        # Non-Var binding: button enabled state mirrors can_submit_var
        vm.can_submit_var.trace_add("write", self._sync_submit_enabled)
        self._sync_submit_enabled()

    def _sync_submit_enabled(self, *_: object) -> None:
        """Mirror vm.can_submit_var onto the submit button's state."""
        state = "normal" if self._vm.can_submit_var.get() else "disabled"
        self._submit_btn.configure(state=state)
```

### Presenter — registers callbacks, mutates Vars only

```python
# presenters/scenario_edit_presenter.py
import logging

from services.scenario_service import ScenarioService
from shared.exception_util import AppError, ScenarioNotFoundError
from view_models.scenario_edit_view_model import ScenarioEditViewModel

class ScenarioEditPresenter:
    """Wires ScenarioEditViewModel actions to ScenarioService calls."""

    def __init__(self, vm: ScenarioEditViewModel, service: ScenarioService) -> None:
        self._vm = vm
        self._service = service
        self._logger = logging.getLogger(__name__)

        # Register handlers — the VM will dispatch user actions to them
        vm.bind_submit(self._on_submit)
        vm.bind_cancel(self._on_cancel)

    def load_scenario(self, id_scenario: str) -> None:
        """Fetch a scenario and populate the ViewModel Vars."""
        try:
            scenario = self._service.get_scenario(id_scenario)
        except ScenarioNotFoundError as e:
            self._vm.error_message_var.set(str(e))
            return
        # Map domain model → VM Vars (the only allowed coupling point)
        self._vm.name_var.set(scenario.name)
        self._vm.url_var.set(scenario.url)
        self._vm.is_active_var.set(scenario.active)
        self._vm.error_message_var.set("")

    def _on_submit(self) -> None:
        """Triggered by vm.submit(); read Vars, call service, update Vars."""
        self._vm.is_busy_var.set(True)
        self._vm.error_message_var.set("")
        try:
            self._service.save_scenario(
                name=self._vm.name_var.get(),
                url=self._vm.url_var.get(),
                active=self._vm.is_active_var.get(),
            )
        except AppError as e:
            self._logger.error("Erreur lors de l'enregistrement : %s", e, exc_info=True)
            self._vm.error_message_var.set(str(e))
        finally:
            self._vm.is_busy_var.set(False)

    def _on_cancel(self) -> None:
        """Reset the form Vars to a clean state."""
        self._vm.name_var.set("")
        self._vm.url_var.set("")
        self._vm.is_active_var.set(False)
        self._vm.error_message_var.set("")
```

### Composition root — `main.py`

```python
# main.py — assemble VM, View, and Presenter; keep references to prevent GC
import tkinter as tk

from presenters.scenario_edit_presenter import ScenarioEditPresenter
from repositories.scenario_repository import ScenarioRepository
from services.scenario_service import ScenarioService
from view_models.scenario_edit_view_model import ScenarioEditViewModel
from views.scenario_edit_view import ScenarioEditView

def main() -> None:
    root = tk.Tk()

    # Wiring (bottom-up): Repository → Service → ViewModel → View → Presenter
    repository = ScenarioRepository()
    service = ScenarioService(repository=repository)

    vm = ScenarioEditViewModel(master=root)
    view = ScenarioEditView(master=root, vm=vm)
    presenter = ScenarioEditPresenter(vm=vm, service=service)

    # Keep a reference to the Presenter on the root so the GC does not collect it
    root._presenter = presenter   # noqa: SLF001 — intentional GC anchor
    view.pack(fill="both", expand=True)
    root.mainloop()

if __name__ == "__main__":
    main()
```

### Anti-patterns — ViewModel

❌ Never store a Var as a local variable in a method — it must be `self.xxx_var`
```python
# BAD — local Var is GC'd after __init__ returns; binding silently breaks
def __init__(self, master):
    name_var = tk.StringVar(master=master)
    ttk.Entry(self, textvariable=name_var)

# GOOD
def __init__(self, master):
    self.name_var = tk.StringVar(master=master)
```

❌ Never compute derived state inside the View
```python
# BAD — the View reads two Vars and writes to a third
def _on_name_change(self, *_):
    self._vm.can_submit_var.set(bool(self._vm.name_var.get()) and bool(self._vm.url_var.get()))

# GOOD — derived state belongs in the VM via trace_add
```

❌ Never call a Service or a Repository from the ViewModel
```python
# BAD
class ScenarioEditViewModel:
    def submit(self):
        self._service.save_scenario(...)   # ← VM must not know services exist

# GOOD — VM dispatches to a Presenter-registered callback
def submit(self):
    if self._on_submit is not None:
        self._on_submit()
```

❌ Never mutate a Var inside its own `trace_add` callback without a re-entrancy guard
```python
# BAD — write triggers the callback which writes again → infinite loop
def _recompute(self, *_):
    self.derived_var.set(self.source_var.get().upper())

# GOOD — guard with self._updating_derived flag (see canonical pattern above)
```

❌ Never let the Presenter touch a widget directly
```python
# BAD
self._view._submit_btn.configure(state="disabled")

# GOOD — mutate a VM Var; the View's trace_add reflects it
self._vm.is_busy_var.set(True)
```

❌ Never let the View import or call a Service or Presenter
```python
# BAD
from services.scenario_service import ScenarioService

# GOOD — the View only knows its ViewModel
from view_models.scenario_edit_view_model import ScenarioEditViewModel
```

---

## Python Version

This project targets **Python 3.14+**. Do not use syntax or features incompatible with this version.
Python 2 is strictly prohibited.

> **Note for AI agents:** `except ExcType1, ExcType2:` (without parentheses) is valid Python 3.14
> syntax accepted by the project linter (ruff ≥ 0.15). Do **not** flag it as a Python 2
> anti-pattern — it is the project's accepted form for catching multiple exception types.

---

## Environment & Installation (Windows 11)

### 1. Create the virtual environment
```bash
python -m venv venv
```

### 2. Activate the virtual environment
```bash
.\venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r './__src__/requirements.txt'
```

### 4. Install Chromium for Playwright
```bash
playwright install chromium
```

### 5. Deploy the project (editable mode)
```bash
pip install -e .
```

---

## Run the Application

```bash
python __src__/main.py
```

---

## Project Cleanup

Removes compiled Python files (`__pycache__`, `.pyc`, etc.):

```bash
python -m pyclean ./ -v
```

---

## Runtime-Generated Files and Folders

These resources are created automatically at launch — **do not version them** and **do not add them manually**.
They must be present in `.gitignore` — the AI must never create or commit them.

| Path                          | Description                          |
|-------------------------------|--------------------------------------|
| `./tmp_app_logs/`             | Temporary execution logs             |
| `./data_scraping/`            | Output for scraping                  |
| `./data_scenarios/`           | User scenario data                   |
| `./config-aspirabot.json`     | Main application configuration       |

---

## Language

This file and all agent instructions are in **English**.

Language rules by content type:

| Content                   | Language                              | Example                                       |
|---------------------------|---------------------------------------|-----------------------------------------------|
| Docstrings                | **English**                           | `"""Load the scenario from disk."""`          |
| Inline comments           | **English**                           | `# Extract the main result blocks`            |
| Log messages (all levels) | **French**                            | `"Démarrage du scraping pour id=%s"`          |
| Exception messages        | **French**                            | `"Provider introuvable : {id}"`               |
| User-facing strings       | **French** — via `shared/i18n_fra.py` only | `ERROR_TEMPLATES["empty_field"]`         |

> **Reminder for AI agents:** log messages are in **French** by default in this project.
> Never write `logger.info("Starting scraping for id=%s", ...)` — always use French.
> The only English text in `.py` files is docstrings and inline comments.

`shared/i18n_fra.py` is the single source of truth for all user-facing French strings.

---

## Code Conventions

### Import Order

Imports must follow **isort** order, enforced via `ruff --select I`:

```python
# 1. Standard library
import logging
from dataclasses import dataclass

# 2. Third-party
from playwright.async_api import Page

# 3. Local application
from models.provider_model import ProviderModel
from shared.i18n_fra import ERROR_TEMPLATES
```

Run `ruff check --select I --fix` before committing.

### General Style
- Strict **PEP 8** compliance.
- **Docstrings** required on all public classes and functions, **Google style**, in **English**.
- **Inline comments** in **English**.
- **Method length**: 25 lines of code maximum per method.
  - Docstrings, blank lines, and pure argument-wrapping lines are excluded from the count.
  - Beyond 25 lines of actual code, split into focused private helpers with intent-revealing names.
- **File length**: 1000 lines maximum — split into focused modules above that.
- **Comments**: one comment per logical block, roughly every 5 lines of code.

```python
# GOOD — decompose by semantic step, not by arbitrary line count
def process_scenario(self, id_scenario: str) -> None:
    scenario = self._fetch_scenario(id_scenario)
    self._validate_scenario(scenario)
    self._apply_defaults(scenario)
```

### Expected Docstring Format (Google Style, English)

A docstring must add information beyond the signature.

```python
# BAD — tautological
def load_config(self) -> dict:
    """Load the config."""
    ...

# GOOD
def fetch_page(url: str, timeout: int = 30) -> str:
    """Load the HTML content of a page via Playwright.

    Args:
        url: The target URL to load.
        timeout: Maximum delay in seconds before giving up.

    Returns:
        The raw HTML content of the page.

    Raises:
        PlaywrightTimeoutError: If the page does not respond within the allotted time.
    """
```

### Type Hints
- **Required** on all function and method signatures.

---

## Interfaces — Protocol Pattern

All inter-layer contracts are defined as `typing.Protocol` in `interfaces/`.
**Never use `ABC` for interfaces** — `Protocol` enables structural subtyping and allows testing without Tkinter.

### Naming convention

- Files: `i_<name>.py` (e.g. `i_scraping_view.py`).
- Classes: `I<Name>` in PascalCase (e.g. `IExecutorView`).

### Definition

```python
# interfaces/i_scenario_service.py
from typing import Protocol

from models.scenario_model import ScenarioModel

class IScenarioService(Protocol):
    def get_scenario(self, id_scenario: str) -> ScenarioModel: ...
    def save_scenario(self, name: str, url: str, active: bool) -> None: ...
```

### Anti-patterns — Interfaces

❌ Never use `ABC`
❌ Never place concrete logic in `interfaces/` (`return []` instead of `...` is a violation)

---

## Dependency Injection & Wiring

**Never instantiate a Service, Repository, ViewModel, or Presenter inside another one.**
All concrete objects are assembled once in `main.py` and injected via `__init__`.

The composition root in `main.py` is also responsible for keeping a reference to every
`Presenter` instance so it is not garbage-collected — losing the reference silently kills
the bindings to the ViewModel.

---

## Shared Application State — `AppStateModel`

Data accessible across multiple modules (currently selected provider, global execution flags) lives
in an `AppStateModel` dataclass in `models/`, instantiated once in `main.py` and injected into the
Services that need it.

```python
# models/app_state_model.py
from dataclasses import dataclass

@dataclass
class AppStateModel:
    """Holds runtime state shared across services.

    Attributes:
        active_scenario_id: ID of the currently selected provider, or None.
        is_scraping: True while a scraping session is running.
    """
    active_scenario_id: str | None = None
    is_scraping: bool = False
```

```python
# main.py — AppStateModel injected into services that need it
state = AppStateModel()
scraping_service = ScrapingService(repository=scraping_repo, state=state)
executor_service = ExecutorService(repository=executor_repo, state=state)
```

**Rules:**
- `AppStateModel` is a plain dataclass — no methods, no business logic.
- Only Services may read or write `AppStateModel` — never Presenters, ViewModels, or Views.
- Never use a module-level global variable as a substitute.

> **AppStateModel vs ViewModel:** `AppStateModel` is **cross-service** domain state.
> `ViewModel` is **per-view** UI state. They never overlap. The Presenter is the only
> component allowed to read `AppStateModel` (via a Service call) and reflect it into the VM.

---

## `TitleModuleEnum` — `shared/enums.py`

`TitleModuleEnum` identifies each sidebar module by a stable internal name.
The enum value is the French display label shown in the sidebar button.

```python
# shared/enums.py
from enum import Enum

class TitleModuleEnum(Enum):
    """Enum for the main view sidebar button labels.

    The values are the actual display labels shown in the sidebar (French).
    The enum name (e.g. E_SCENARIOS) is the stable internal identifier used
    to register lazy-load callbacks via MainView.set_on_show().
    """

    E_LOGS = "LOGS"
    E_PROFILES = "PROFILES"
    E_SCENARIOS = "SCENARIOS"
    E_WORKFLOW = "WORKFLOW"
    E_EXECUTOR = "EXECUTOR"
    E_SCRAPING = "SCRAPING"
    E_FAQ = "FAQ"
    E_DEBUG = "DEBUG"
    E_OPTIONS = "OPTIONS"
```

For lazy tab initialization, register a callback via `MainView.set_on_show()`:
the callback runs once, the first time the user navigates to that tab.

```python
# main.py — register lazy loaders after wiring
main_view.set_on_show(TitleModuleEnum.E_SCENARIOS, scripts_presenter.ensure_scenarios_loaded)
main_view.set_on_show(TitleModuleEnum.E_WORKFLOW,  editor_presenter.ensure_workflows_loaded)
```

---

## Logging

Use the standard `logging` module. **Never use `print()` for runtime output.**

### Setup — one logger per class

```python
import logging

class ScrapingService:
    def __init__(self, ...) -> None:
        self._logger = logging.getLogger(__name__)
```

### Log levels by layer

| Layer        | Levels to use    | Rationale                                                |
|--------------|------------------|----------------------------------------------------------|
| `Repository` | `DEBUG`          | Low-level I/O details, useful for tracing.               |
| `Service`    | `DEBUG`, `INFO`  | Business flow steps.                                     |
| `Presenter`  | `ERROR`          | Unexpected failures caught before being shown to the user. |
| `ViewModel`  | —                | Pure state holder — never logs.                          |
| `View`       | —                | Passive UI — never logs, delegates to the Presenter.     |

```python
# Repository — trace I/O at DEBUG (message in French)
def find_by_id(self, id_scenario: str) -> ScenarioModel | None:
    self._logger.debug("Lecture du scenario id=%s", id_scenario)
    ...

# Service — trace flow at INFO (message in French)
def start_scraping(self, id_scenario: str) -> None:
    self._logger.info("Démarrage du scraping pour scenario id=%s", id_scenario)
    ...

# Presenter — log unexpected errors at ERROR (message in French)
def _on_submit(self) -> None:
    try:
        self._service.start_scraping(self._vm.scenario_id_var.get())
    except AppError as e:
        self._logger.error("Erreur lors du scraping : %s", e, exc_info=True)
        self._vm.error_message_var.set(format_error(e))
```

**Rules:**
- Always use `%s` formatting in log calls — never f-strings.
- Use `exc_info=True` in `logger.error()` calls that catch exceptions.
- Log messages are written in **French**.
- Never log sensitive data (passwords, tokens, personal data).

---

## Error Handling

### Exception hierarchy

All runtime exceptions inherit from a common base defined in `shared/exception_util.py`:

```python
# shared/exception_util.py
class AppError(Exception):
    """Base error for the application."""

class ScrapingError(AppError): ...
class PageLoadError(ScrapingError): ...
class ScenarioError(AppError): ...
class ScenarioNotFoundError(ScenarioError): ...
class RepositoryError(AppError): ...
class DatabaseUnavailableError(RepositoryError): ...
```

Exception messages (the string passed to `raise`) are written in **French**.

**Rules:**
- Never raise `Exception`, `ValueError`, `RuntimeError`, or `FileNotFoundError` directly in business code.
- Always raise the most **specific** exception available.
- Always chain with `raise NewError("...") from original`.

### Who raises, who catches

| Layer        | Raises                                  | Catches                                                                  |
|--------------|-----------------------------------------|--------------------------------------------------------------------------|
| `Repository` | `RepositoryError` subclasses            | Low-level errors (`OSError`, `json.JSONDecodeError`…) — wraps and re-raises |
| `Service`    | Domain exceptions                       | `RepositoryError` if a transformation is needed                          |
| `Presenter`  | —                                       | Domain exceptions → formats and writes the message into a VM Var         |
| `ViewModel`  | —                                       | Nothing — it is pure state.                                              |
| `View`       | —                                       | Nothing — it only renders.                                               |

```python
# Repository — wrap technical errors
def load_config(self) -> dict:
    try:
        with open(self._path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise DatabaseUnavailableError("Impossible de lire la config.") from e

# Service — raise domain errors
def get_scenario(self, id_scenario: str) -> ScenarioModel:
    scenario = self._repository.find_by_id(id_scenario)
    if scenario is None:
        raise ScenarioNotFoundError(f"Scenario introuvable : {id_scenario}")
    return scenario

# Presenter — only layer that catches for the UI; writes into a VM Var
def _on_load(self) -> None:
    try:
        scenario = self._service.get_scenario(self._vm.scenario_id_var.get())
        self._vm.name_var.set(scenario.name)
        self._vm.url_var.set(scenario.url)
        self._vm.error_message_var.set("")
    except ScenarioNotFoundError as e:
        self._vm.error_message_var.set(str(e))
    except AppError as e:
        self._logger.error("Erreur inattendue : %s", e, exc_info=True)
        self._vm.error_message_var.set("Une erreur inattendue est survenue.")
```

### Anti-patterns — Exceptions

❌ Never use a bare `except` or swallow errors silently
❌ Never raise generic exceptions in business code
❌ Never forget `raise … from original` chaining
❌ Never catch exceptions in a layer that is not responsible for them

---

## Error Messages

### Ownership by layer

| What                          | Where                                    |
|-------------------------------|------------------------------------------|
| Raw errors (code + context)   | `models/field_validation_error_model.py` |
| Message templates             | `shared/i18n_fra.py`                     |
| Formatting logic              | `shared/error_formatter.py` — `format_error()` |
| Storage of formatted message  | `ViewModel` (`error_message_var`)        |
| Display                       | `View` — bound to `vm.error_message_var` |

### `FieldValidationErrorModel`

```python
# models/field_validation_error_model.py
from dataclasses import dataclass

@dataclass(frozen=True)
class FieldValidationErrorModel:
    """Represents a business field validation error.

    Attributes:
        code: Key of the template in ERROR_TEMPLATES.
        context: Data used to format the message.
    """
    code: str
    context: dict[str, str | int]
```

### Message templates — `shared/i18n_fra.py`

```python
ERROR_TEMPLATES: dict[str, str] = {
    "invalid_operator": (
        "Étape {step} : l'opérateur doit être l'un de : "
        "equal, not_equal, greater_than, less_than, "
        "greater_or_equal, less_or_equal."
    ),
    "empty_field": "Étape {step} : le champ '{field}' ne peut pas être vide.",
}
```

### `format_error()` helper — `shared/error_formatter.py`

```python
from models.field_validation_error_model import FieldValidationErrorModel
from shared.i18n_fra import ERROR_TEMPLATES

def format_error(error: FieldValidationErrorModel) -> str:
    """Format a FieldValidationErrorModel into a ready-to-display French string.

    Args:
        error: The validation error to format.

    Returns:
        A ready-to-display user message in French.
    """
    template = ERROR_TEMPLATES.get(
        error.code,
        "Erreur inconnue (code : {code})",
    )
    try:
        return template.format(code=error.code, **error.context)
    except KeyError as e:
        return f"Erreur de formatage pour le code '{error.code}' : clé manquante {e}"
```

### Presenter — formats and writes to a VM Var

```python
from shared.error_formatter import format_error

messages = [format_error(e) for e in raw_errors]
self._vm.error_message_var.set("\n".join(messages))
```

### Anti-patterns — Error Messages

❌ Never write a user-facing string inline in a Service, Presenter, or ViewModel
❌ Never call `.format(**e.context)` directly — always go through `format_error()`
❌ Never pass `FieldValidationErrorModel` instances into a VM Var — format first
❌ Never compose or format error messages inside the View

---

## Validators — FluentValidation Pattern

All domain-level field validation is centralised in `__src__/validators/`. **No validation logic
is allowed inline in Presenters, Services, ViewModels, or Views.**

### Location and naming

- Folder: `__src__/validators/`
- Base class: `abstract_validator.py` — `AbstractValidator[T]`
- Concrete validators: `<domain>_validator.py` (e.g. `scraping_validator.py`)
- Class name: `<Domain>Validator` in PascalCase

### Dependency rules

| Layer                 | May import from                                                  |
|-----------------------|------------------------------------------------------------------|
| `AbstractValidator`   | `shared/` only                                                   |
| Concrete Validator    | `models/`, `shared/`, `AbstractValidator`                        |
| `Presenter`           | Concrete validator — runs it on a Model built from VM Vars       |
| `Service`             | Concrete validator — used as a domain validation gate            |

A concrete validator validates a **domain Model** (`AbstractValidator[MyModel]`). The Presenter is
responsible for assembling a Model from the ViewModel's Vars before passing it to the validator.
Validators **must never** import from `View`, `Presenter`, `Repository`, or `ViewModel`.

### Definition pattern

```python
# validators/scraping_validator.py
from models.launcher_model import LauncherModel
from shared.enums import UrlSourceTypeEnum
from shared.i18n_fra import C_EXEC_FOLDER_URL_SOURCE_EMPTY, C_EXEC_NO_EXPORT_FOLDER
from validators.abstract_validator import AbstractValidator

class ScrapingLaunchValidator(AbstractValidator[LauncherModel]):
    """Validates a LauncherModel before triggering a scraping session."""

    def __init__(self) -> None:
        """Define all validation rules for a scraping launch profile."""
        super().__init__()

        self.rule_for(lambda p: p.export_folder, "export_folder").must(
            lambda v: bool(v and v.strip()), C_EXEC_NO_EXPORT_FOLDER,
        )
        self.rule_for(lambda p: p.url_source_value, "url_source_value").must(
            bool, C_EXEC_FOLDER_URL_SOURCE_EMPTY,
        ).when(lambda p: p.url_source_type != UrlSourceTypeEnum.E_MANUAL.value)
```

### Usage in Presenter

```python
from validators.scraping_validator import ScrapingLaunchValidator

def _on_launch(self) -> None:
    # Build a domain model from VM Vars
    model = LauncherModel(
        export_folder=self._vm.export_folder_var.get(),
        url_source_value=self._vm.url_source_value_var.get(),
        url_source_type=self._vm.url_source_type_var.get(),
    )
    result = ScrapingLaunchValidator().validate(model)
    if not result.is_valid:
        self._vm.error_message_var.set(result.first_error or "")
        return
    self._vm.error_message_var.set("")
    self._service.start_scraping(model)
```

### API — `AbstractValidator[T]`

| Method                              | Description                                   |
|-------------------------------------|-----------------------------------------------|
| `rule_for(accessor, field_name="")` | Opens a rule chain; returns `RuleBuilder`.    |
| `validate(instance)`                | Runs all rules; returns `ValidationResult`.   |

### API — `RuleBuilder[T, V]` (chainable)

| Method                       | Description                                          |
|------------------------------|------------------------------------------------------|
| `.not_empty(message)`        | Fails when value is `None`, `""`, or whitespace.     |
| `.not_equal(other, message)` | Fails when `value == other`.                         |
| `.must(predicate, message)`  | Fails when `predicate(value)` returns `False`.       |
| `.when(condition)`           | Guards the **last** rule; condition receives the whole instance. |
| `.with_message(message)`     | Replaces the message on the last rule.               |

### API — `ValidationResult`

| Property      | Type                | Description                                        |
|---------------|---------------------|----------------------------------------------------|
| `is_valid`    | `bool`              | `True` when `errors` is empty.                     |
| `errors`      | `tuple[str, ...]`   | All French error messages, display-ready.          |
| `first_error` | `str \| None`       | First error, or `None` when valid.                 |

Validators run **all rules** (not fail-fast). Use `first_error` when the UI shows one message at a
time; iterate `errors` to list all failures.

### Anti-patterns — Validators

❌ Never write validation predicates inline in a Presenter, Service, or ViewModel
❌ Never import View, Presenter, ViewModel, or Repository from a Validator
❌ Never place business logic inside a Validator beyond predicates and messages
❌ Never use `.when()` before `.must()` — `.when()` guards the rule above it
```python
# BAD
self.rule_for(...).when(condition).must(predicate, msg)
# GOOD
self.rule_for(...).must(predicate, msg).when(condition)
```

---

## Tests

When adding tests:
- Place tests in a `__tests__/` folder at the project root.
- Use **pytest**.
- Mirror the `__src__/` folder structure inside `__tests__/`.
- Every new feature must be accompanied by its tests.
- ViewModel tests instantiate a hidden `tk.Tk()` root and assert on Var values after action calls — no widget needed.
- Run tests with:
```bash
pytest __tests__/ -v
```

---

## Do Not Modify Without Prior Discussion

- The MVP + ViewModel layer structure — never mix responsibilities between layers.
- `config-aspirabot.json` — runtime-generated file, never hardcode it.
- `tmp_*` folders — runtime-generated, never write to them manually.
- `data_*` folders — runtime-generated, never write to them manually.

---

## Anti-patterns — Strictly Forbidden

These patterns violate the MVP + ViewModel architecture and must never appear in the codebase.
If you are an AI agent, treat these as hard constraints — no exception, no workaround.

### ViewModel Violations

❌ Never store a `tk.*Var` as a local variable instead of an instance attribute (silent GC).
❌ Never compute derived state inside the View — use `trace_add` in the VM.
❌ Never call a Service, Repository, or Model from a ViewModel.
❌ Never mutate a Var inside its own `trace_add` callback without a re-entrancy guard.
❌ Never pass raw domain Models into the View — the Presenter maps them onto VM Vars.
❌ Never pass `dict[str, Any]` as UI state — UI state lives in typed Vars on the VM.

### View Violations

❌ Never put `if/else` on domain values in the View — derive in the VM, bind in the View.
❌ Never let the View import a Service, Repository, Presenter, or Model.
❌ Never trigger data loading or dynamic content building inside a View constructor — only widget construction and bindings.
```python
# BAD — the View loads data at construction time
class ScenarioEditView(ttk.Frame):
    def __init__(self, master, vm):
        super().__init__(master)
        self._inline_form = StepInlineFormPanel(self)
        self._inline_form.load(None)  # ← wrong, the Presenter decides when to load

# GOOD — only widget construction and VM bindings
class ScenarioEditView(ttk.Frame):
    def __init__(self, master, vm):
        super().__init__(master)
        self._inline_form = StepInlineFormPanel(self, vm)
        # No load() here — the Presenter triggers loading via a VM Var update
```

### Presenter Violations

❌ Never touch a widget directly from a Presenter — mutate a VM Var instead.
❌ Never import `tkinter` from a Presenter.
❌ Never place business logic inside a Presenter — that belongs in a Service.
❌ Never instantiate a Service or Repository inside a Presenter — inject via `__init__`.

### Service / Repository Violations

❌ Never import a `View`, `ViewModel`, or `Presenter` inside a `Service` or `Repository`.
❌ Never write to persistent storage outside a `Repository`.
❌ Never store shared runtime state in a Presenter, View, ViewModel, or module-level global — use `AppStateModel`.

### Design Violations

❌ Never use `ABC` for an interface — always use `typing.Protocol`.
❌ Never place concrete logic inside `interfaces/`.
❌ Never place business logic inside `shared/`.
❌ Never bypass the Presenter to wire a View to a Service directly.
❌ Never forget to keep a reference to the Presenter at the composition root (silent GC kills bindings).

### Code Quality Violations

❌ Never write a method longer than 25 lines of code — break it down.
❌ Never write a file longer than 1000 lines — split into focused modules.
❌ Never use `print()` — use `self._logger = logging.getLogger(__name__)`.
❌ Never use Python 2.
❌ Never commit runtime-generated files or folders.
```
# Must stay in .gitignore — never create or commit them manually
tmp_app_logs/
data_scraping/
data_scenarios/
config-aspirabot.json
```
❌ Never omit type hints on a function or method signature.
❌ Never omit a docstring on a public class or function.
❌ Never write a tautological docstring.
❌ Never use bare `except` clauses.
