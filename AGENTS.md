# AGENTS.md — Aspirabot

## Project Description

**Aspirabot** is a Web Scraping tool with a Tkinter-based GUI.
It allows users to create, configure, and execute data extraction or web automation workflows visually.
The browser is simulated via **Playwright** (Chromium) to bypass standard antibot detection.

---

## Architecture

### MVP Layers

The project strictly follows the **Model-View-Presenter** pattern:

```
__src__/
├── models/         # Business entities and data structures (domain)
├── views/          # Tkinter GUI components (no business logic)
├── presenters/     # Orchestration: connects views to services
├── repositories/   # Data read/write layer (files, JSON…)
├── services/       # Business logic and domain rules
└── main.py         # Application entry point
```

**MVP rules — strictly enforced:**
- `views` contain **no business logic** — display and UI events only.
- `services` and `models` form the **domain**: they are independent of the UI and repositories.
- `repositories` are the **only layer** allowed to read/write persistent data.
- `presenters` are the **only layer** allowed to connect views to services.

### Supporting Structure

These folders are **not part of the MVP pattern** but participate in the overall code organization:

```
__src__/
├── interfaces/     # Protocol-based contracts for MVP layers
└── shared/         # Common utilities and base code shared across layers
```

**Rules for supporting folders:**
- `interfaces/` defines `Protocol` contracts implemented by MVP layers — never place concrete logic here.
- `shared/` contains helpers, constants, and base classes usable by any layer — never place business logic here.
- Neither `interfaces/` nor `shared/` belong to any MVP layer — they are cross-cutting concerns.

---

## Dependency Map

**Allowed import direction — strictly one way:**

```
View → Presenter → Service → Repository → Model
```

Each layer may only import from layers **below** it in this chain.
Cross-layer imports in the opposite direction are a hard violation.

| Importing layer | May import from | Must NEVER import from |
|-----------------|-----------------|------------------------|
| `View`          | `interfaces/`, `shared/`               | `Service`, `Repository`, `Model` directly |
| `Presenter`     | `Service`, `interfaces/`, `shared/`    | `Repository` directly |
| `Service`       | `Repository`, `interfaces/`, `Model`, `shared/` | `View`, `Presenter` |
| `Repository`    | `Model`, `shared/`                     | `View`, `Presenter`, `Service` |
| `Model`         | `shared/`                              | Everything else |

> **Rule:** if adding an import would create a cycle or go against the arrow above, the design is wrong — refactor instead.

---

## Service vs Presenter — Decision Rule

A condition or transformation belongs in the **Service** if it is a **domain rule**:
it would still be true if the application had no GUI at all (CLI, API, test runner).

A condition belongs in the **Presenter** if it is a **coordination decision**:
it only exists because the UI needs to decide what to show or what to call next.

| Question to ask | Answer → layer |
|---|---|
| "Would this rule exist in a headless version of the app?" | Yes → **Service** |
| "Does this condition only make sense because of what the View expects?" | Yes → **Presenter** |
| "Am I transforming or validating domain data?" | → **Service** |
| "Am I deciding which view method to call, or in what order?" | → **Presenter** |

```python
# BAD — business rule hidden inside a Presenter
def on_start_clicked(self) -> None:
    url = self._view.get_url()
    if not url.startswith("https://"):   # ← domain rule, belongs in Service
        self._view.show_errors(["URL invalide."])
        return
    self._service.start_scraping(url)

# GOOD — Presenter coordinates only; Service owns the rule
def on_start_clicked(self) -> None:
    url = self._view.get_url()
    try:
        self._service.start_scraping(url)   # raises ScrapingError if URL invalid
    except ScrapingError as e:
        self._view.show_errors([str(e)])

# BAD — Presenter duplicates a rule that already lives (or should live) in the Service
def on_save_clicked(self) -> None:
    if self._view.get_name().strip() == "":   # ← validation = domain rule
        self._view.show_errors(["Le nom est requis."])

# GOOD — Service validates, Presenter only formats and dispatches
def on_save_clicked(self) -> None:
    data = self._view.get_form_data()
    try:
        self._service.save_provider(data)
    except ProviderValidationError as e:
        self._view.show_errors([format_error(e)])
```

---

## Python Version

This project targets **Python 3.14**. Do not use syntax or features incompatible with this version.
It is expressly prohibited to use Python 2

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

| Path | Description |
|------|-------------|
| `./tmp_app_logs/` | Temporary execution logs |
| `./data_scraping/` | User provider data |
| `./data_providers/` | Output for scraping |
| `./config-aspirabot.json` | Main application configuration |

---

## Language

This file and all agent instructions are in **English**.

Language rules by content type:

| Content | Language | Example |
|---|---|---|
| Docstrings | **English** | `"""Load the provider from disk."""` |
| Inline comments | **English** | `# Extract the main result blocks` |
| Log messages (all levels) | **French** | `"Démarrage du scraping pour id=%s"` |
| Exception messages | **French** | `"Provider introuvable : {id}"` |
| User-facing strings | **French** — via `shared/i18n_fra.py` only | `ERROR_TEMPLATES["empty_field"]` |

> **Reminder for AI agents:** log messages are in **French** by default in this project.
> Never write `logger.info("Starting scraping for id=%s", ...)` — always use French.
> The only English text in `.py` files is docstrings and inline comments.

`shared/i18n_fra.py` is the single source of truth for all user-facing French strings.

---

## Code Conventions

This project enforces a high standard of code quality. All contributions must follow these rules.

### Import Order

Imports must follow **isort** order, enforced via `ruff --select I`:

```python
# 1. Standard library
import logging
from dataclasses import dataclass

# 2. Third-party
from playwright.async_api import Page

# 3. Local application
from models.provider import Provider
from shared.i18n_fra import ERROR_TEMPLATES
```

Never mix levels. Run `ruff check --select I --fix` before committing.

### General Style
- Strict **PEP 8** compliance
- **Docstrings** required on all public classes and functions, **Google style**, in **English**
- **Inline comments** in **English**
- **Method length**: 25 lines of code maximum per method.
  - Docstrings are excluded from the count.
  - Blank lines are excluded from the count.
  - Lines used solely to wrap arguments or chain calls (no logic) are excluded from the count.
  - If a method exceeds 25 lines of *actual code*, break it into focused private helpers with a name that expresses intent.
- **File length**: 1000 lines maximum — if a file exceeds this, split it into focused modules
- **Comments**: one comment per logical block, approximately every 5 lines of code

```python
# GOOD — argument wrapping lines do not count toward the 25-line limit
result = some_function(
    argument_one,
    argument_two,
    argument_three,
)

# GOOD — decompose by semantic step, not by arbitrary line count
def process_provider(self, provider_id: str) -> None:
    provider = self._fetch_provider(provider_id)
    self._validate_provider(provider)
    self._apply_defaults(provider)
```

### Expected Docstring Format (Google Style, English)

A docstring must add information beyond what the signature already expresses.
A docstring that only restates the method name is a violation of intent.

```python
# BAD — tautological docstring, adds no value
def load_config(self) -> dict:
    """Load the config."""
    ...

# GOOD — explains contract, non-obvious behaviour, and raised exceptions
def fetch_page(url: str, timeout: int = 30) -> str:
    """Load the HTML content of a page via Playwright.

    Args:
        url: The target URL to load.
        timeout: Maximum delay in seconds before giving up.

    Returns:
        The raw HTML content of the page.

    Raises:
        PlaywrightTimeoutError: If the page does not respond within the allotted time.

    Examples:
        >>> fetch_page("https://example.com", 30)
        "<html>...</html>"
    """
```

### Expected Inline Comment Style (English)
```python
def parse_results(raw_html: str) -> list[dict]:
    # Initialize the parser and clean the input
    soup = BeautifulSoup(raw_html, "html.parser")
    soup = _strip_scripts(soup)

    # Extract the main result blocks
    blocks = soup.select(".result-item")
    if not blocks:
        return []

    # Convert each block into a structured dictionary
    results = [_block_to_dict(b) for b in blocks]
    return results
```

### Type Hints
- **Required** on all function and method signatures

---

## Interfaces — Protocol Pattern

All inter-layer contracts are defined as `typing.Protocol` in `interfaces/`.
**Never use `ABC` for interfaces** — `Protocol` enables structural subtyping and allows testing without Tkinter.

### Naming convention

- Interface files: `i_<name>.py` (e.g. `i_scraping_view.py`)
- Interface classes: prefix `I` in PascalCase (e.g. `IScrapingView`)

### Definition

```python
# interfaces/i_error_display_view.py
from typing import Protocol

class IErrorDisplayView(Protocol):
    def show_errors(self, messages: list[str]) -> None: ...
    def clear_errors(self) -> None: ...
```

### Usage in Presenter

```python
# presenters/scraping_presenter.py
from views.scraping_view import ScrapingView
from services.scraping_service import ScrapingService

class ScrapingPresenter:
    def __init__(self, view: ScrapingView, service: ScrapingService) -> None:
        self._view = view
        self._service = service
```

### Anti-patterns — Interfaces

❌ Never use `ABC` for view or service contracts
```python
# BAD
from abc import ABC, abstractmethod
class IScrapingView(ABC):
    @abstractmethod
    def show_errors(self, messages: list[str]) -> None: ...
```

❌ Never place concrete logic inside `interfaces/`
```python
# BAD — interfaces define contracts only, no implementation
class IScrapingService(Protocol):
    def run(self, url: str) -> list[dict]:
        return []  # ← must be left as "..."
```

---

## Dependency Injection & Wiring

**Never instantiate a Service or Repository inside another Service, Presenter, or View.**
All concrete objects are assembled once and injected via `__init__`.

---

## Shared Application State

Some data must be accessible across multiple modules (e.g. currently selected provider, global
execution flags). This state must never be stored in a Presenter, a View, or a module-level global.

**Rule:** define an `AppState` dataclass in `models/`, instantiate it once in `main.py`,
and inject it into every Service that needs it.

```python
# models/app_state.py
from dataclasses import dataclass

@dataclass
class AppState:
    """Holds runtime state shared across services.

    Attributes:
        active_provider_id: ID of the currently selected provider, or None.
        is_scraping: True while a scraping session is running.
    """
    active_provider_id: str | None = None
    is_scraping: bool = False
```

```python
# main.py — AppState instantiated once, injected into services that need it
from models.app_state import AppState
state             = AppState()
scraping_service  = ScrapingService(repository=scraping_repo, state=state)
executor_service  = ExecutorService(repository=executor_repo, state=state)
```

**Rules:**
- `AppState` is a plain dataclass — no methods, no business logic.
- Only Services may read or write `AppState` — never Presenters or Views directly.
- Never use a module-level global variable as a substitute for `AppState`.

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
    The enum name (e.g. E_SCRIPTS) is the stable internal identifier used
    to register lazy-load callbacks via MainView.set_on_show().
    """

    E_LOGS     = "LOGS"
    E_HISTORY  = "HISTORIC"
    E_SCRIPTS  = "PROVIDER"
    E_EDITOR   = "WORKFLOW"
    E_EXECUTOR = "EXECUTE"
    E_FAQ      = "FAQ"
    E_DEBUG    = "DEBUG"
    E_OPTIONS  = "OPTIONS"
```

For lazy tab initialization, register a callback via `MainView.set_on_show()`:
the callback is invoked once, the first time the user navigates to that tab.

```python
# main.py — register lazy loaders after wiring
main_view.set_on_show(TitleModuleEnum.E_SCRIPTS, scripts_presenter.ensure_providers_loaded)
main_view.set_on_show(TitleModuleEnum.E_EDITOR,  editor_presenter.ensure_workflows_loaded)
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

| Layer | Levels to use | Rationale |
|---|---|---|
| `Repository` | `DEBUG` | Low-level I/O details, useful for tracing |
| `Service` | `DEBUG`, `INFO` | Business flow steps |
| `Presenter` | `ERROR` | Unexpected failures caught before the View |
| `View` | — | Never logs — delegates all errors to the Presenter |

```python
# Repository — trace I/O at DEBUG (message in French)
def find_by_id(self, provider_id: str) -> Provider | None:
    self._logger.debug("Lecture du provider id=%s", provider_id)
    ...

# Service — trace flow at INFO (message in French)
def start_scraping(self, provider_id: str) -> None:
    self._logger.info("Démarrage du scraping pour provider id=%s", provider_id)
    ...

# Presenter — log unexpected errors at ERROR (message in French)
def on_start_clicked(self, provider_id: str) -> None:
    try:
        self._service.start_scraping(provider_id)
    except AppError as e:
        self._logger.error("Erreur lors du scraping : %s", e, exc_info=True)
        self._view.show_errors([format_error(e)])
```

**Rules:**
- Always use `%s` formatting in log calls — never f-strings (`logger.error("msg %s", var)` not `logger.error(f"msg {var}")`).
- Use `exc_info=True` in `logger.error()` calls that catch exceptions, to capture the full stack trace.
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
class ProviderError(AppError): ...
class ProviderNotFoundError(ProviderError): ...
class RepositoryError(AppError): ...
class DatabaseUnavailableError(RepositoryError): ...
```

Exception messages (the string passed to `raise`) are written in **French**.

**Rules:**
- Never raise `Exception`, `ValueError`, `RuntimeError`, or `FileNotFoundError` directly in business code.
- Always raise the most **specific** exception available.
- Always chain with `raise NewError("...") from original` to preserve the traceback.

### Who raises, who catches

| Layer | Raises | Catches |
|---|---|---|
| `Repository` | `RepositoryError` subclasses | Low-level errors (`IOError`, `json.JSONDecodeError`…) — wraps and re-raises |
| `Service` | Domain exceptions (`ProviderNotFoundError`…) | `RepositoryError` if a transformation is needed |
| `Presenter` | — | Domain exceptions → formats into `list[str]` for the View |
| `View` | — | Nothing — the Presenter delivers ready-to-display messages |

```python
# Repository — wrap technical errors (message in French)
def load_config(self) -> dict:
    try:
        with open(self._path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise DatabaseUnavailableError("Impossible de lire la config.") from e

# Service — raise domain errors (message in French)
def get_provider(self, provider_id: str) -> Provider:
    provider = self._repository.find_by_id(provider_id)
    if provider is None:
        raise ProviderNotFoundError(f"Provider introuvable : {provider_id}")
    return provider

# Presenter — only layer that catches for the View
def on_provider_requested(self, provider_id: str) -> None:
    try:
        provider = self._service.get_provider(provider_id)
        self._view.display_provider(provider)
    except ProviderNotFoundError as e:
        self._view.show_errors([str(e)])
    except AppError as e:
        self._logger.error("Erreur inattendue : %s", e, exc_info=True)
        self._view.show_errors(["Une erreur inattendue est survenue."])
```

### Anti-patterns — Exceptions

❌ Never use a bare `except` or swallow errors silently
```python
# BAD
try:
    ...
except:
    pass

# BAD
try:
    ...
except Exception:
    return None
```

❌ Never raise generic exceptions in business code
```python
# BAD
raise ValueError("Provider not found")
raise FileNotFoundError("File not found")

# GOOD
raise ProviderNotFoundError("Provider introuvable : {id}") from None
raise UrlSourceFileNotFoundError(path) from exc
```

❌ Never forget to chain exceptions
```python
# BAD — original traceback is lost
except OSError:
    raise DatabaseUnavailableError("Erreur I/O")

# GOOD
except OSError as e:
    raise DatabaseUnavailableError("Erreur I/O") from e
```

❌ Never catch exceptions in a layer that is not responsible for them
```python
# BAD — a Repository must not catch domain errors from a Service
# BAD — a Service must not catch and swallow RepositoryError without re-raising
```

❌ Never use `try/except` blocks wrapping more than 4–5 lines without justification

---

## Error Messages

### Ownership by layer

| What | Where |
|------|-------|
| Raw errors (code + context) | `models/` — `FieldValidationError` dataclass |
| Message templates | `shared/i18n_fra.py` |
| Formatting logic | `shared/error_formatter.py` — via `format_error()` helper |
| Display | `views/` — receives `list[str]`, renders only |

---

### `FieldValidationError` — `models/`

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class FieldValidationError:
    """Represents a business field validation error.

    Attributes:
        code: Key of the template in ERROR_TEMPLATES.
        context: Data used to format the message.
    """
    code: str
    context: dict[str, str | int]
```

---

### Message templates — `shared/i18n_fra.py`

All user-facing strings live here. **No string is ever written inline** in business logic or view code.

```python
# shared/i18n_fra.py
ERROR_TEMPLATES: dict[str, str] = {
    "invalid_operator": (
        "Étape {step} : l'opérateur doit être l'un de : "
        "equal, not_equal, greater_than, less_than, "
        "greater_or_equal, less_or_equal."
    ),
    "empty_field": "Étape {step} : le champ '{field}' ne peut pas être vide.",
}
```

---

### `format_error()` helper — `shared/error_formatter.py`

This helper is placed in `shared/` because it is a pure formatting utility with no business logic
and no dependency on any MVP layer. Any layer that produces user-facing messages (typically the
Presenter) may import it.

All formatting goes through this single helper. **Never call `.format(**e.context)` directly.**

```python
# shared/error_formatter.py
from models.field_validation_error import FieldValidationError
from shared.i18n_fra import ERROR_TEMPLATES

def format_error(error: FieldValidationError) -> str:
    """Format a FieldValidationError into a human-readable string.

    Args:
        error: The validation error to format.

    Returns:
        A ready-to-display user message in French.
    """
    template = ERROR_TEMPLATES.get(
        error.code,
        "Erreur inconnue (code : {code})"
    )
    try:
        return template.format(code=error.code, **error.context)
    except KeyError as e:
        return f"Erreur de formatage pour le code '{error.code}' : clé manquante {e}"
```

---

### Presenter — formats and delegates

```python
from shared.error_formatter import format_error

messages = [format_error(e) for e in raw_errors]
self._view.show_errors(messages)
```

---

### View — passive display only

```python
def show_errors(self, messages: list[str]) -> None: ...
def clear_errors(self) -> None: ...
```

The View receives ready-to-display strings. It never formats, conditions, or owns any message text.

---

### Interface — `interfaces/i_error_display_view.py`

```python
from typing import Protocol

class IErrorDisplayView(Protocol):
    def show_errors(self, messages: list[str]) -> None: ...
    def clear_errors(self) -> None: ...
```

---

### Anti-patterns — Error Messages

❌ Never write a user-facing string inline in a service or presenter
```python
# BAD
errors.append(f"Étape {index} : l'opérateur doit être...")
# GOOD — use shared/i18n_fra.py + format_error()
```

❌ Never call `.format(**e.context)` directly — always use `format_error()`

❌ Never pass `FieldValidationError` objects to the View
```python
# BAD
self._view.show_errors(raw_errors)  # ← format first in the Presenter
```

❌ Never format or build error messages inside the View
```python
# BAD
def show_errors(self, raw_errors: list[FieldValidationError]) -> None:
    for e in raw_errors:
        msg = ERROR_TEMPLATES[e.code].format(**e.context)  # ← Presenter's job
```

---

## Tests

When adding tests:
- Place tests in a `__tests__/` folder at the project root
- Use **pytest**
- Mirror the `__src__/` folder structure inside `__tests__/`
- Every new feature must be accompanied by its tests
- Run tests with:
```bash
pytest __tests__/ -v
```

---

## Do Not Modify Without Prior Discussion

- The MVP layer structure — never mix responsibilities between layers
- `config-aspirabot.json` — runtime-generated file, never hardcode it
- `tmp_*` folders — runtime-generated, never write to them manually
- `data_*` folders — runtime-generated, never write to them manually

---

## Anti-patterns — Strictly Forbidden

These patterns violate the MVP architecture and must never appear in the codebase.
If you are an AI agent, treat these rules as hard constraints — no exception, no workaround.

---

### Layer Violations

❌ Never import a `View` inside a `Service`, `Model`, or `Repository`
```python
# BAD — a service must never know the UI exists
from views.main_view import MainView
```

❌ Never import a `Repository` inside a `View`
```python
# BAD — a view must never access persistent data directly
from repositories.config_repository import ConfigRepository
```

❌ Never import a `Service` inside a `View`
```python
# BAD — a view must never call business logic directly
from services.scraping_service import ScrapingService
```

❌ Never place business logic inside a `Presenter`
```python
# BAD — a presenter orchestrates, it does not compute
def on_start_clicked(self):
    url = self._view.get_url()
    if not url.startswith("https://"):  # ← business rule, belongs in a service
        ...
```

❌ Never write to persistent storage outside a `Repository`
```python
# BAD — only repositories are allowed to read/write data
with open("config-aspirabot.json", "w") as f:
    json.dump(data, f)
```

---

### Design Violations

❌ Never use `ABC` to define an interface — always use `typing.Protocol`

❌ Never place concrete logic inside `interfaces/`
```python
# BAD — interfaces define contracts only, no implementation
class IScrapingService(Protocol):
    def run(self, url: str) -> list[dict]:
        return []  # ← must be left as "..."
```

❌ Never place business logic inside `shared/`
```python
# BAD — shared/ contains utilities only, not domain rules
def shared_validate_provider(provider: dict) -> bool:
    if provider["type"] == "premium":  # ← domain rule, belongs in a service
        ...
```

❌ Never bypass the `Presenter` to connect a `View` to a `Service` directly
```python
# BAD — views and services must never be directly coupled
view = MainView()
service = ScrapingService()
view.on_start = service.run  # ← the presenter must be the bridge
```

❌ Never store shared runtime state in a Presenter, a View, or a module-level global
```python
# BAD — global state, not injectable, not testable
_current_provider_id: str | None = None

# GOOD — use AppState defined in models/ and injected into services
```

---

### Code Quality Violations

❌ Never write a method longer than 25 lines of code — break it down instead
(Blank lines, docstrings, and argument-wrapping lines are excluded from the count.)

❌ Never write a file longer than 1000 lines — split into focused modules

❌ Never use `print()` — always use `self._logger = logging.getLogger(__name__)`

❌ Never use Python 2. Always use Python 3.13 and more.

❌ Never commit runtime-generated files or folders
```
# These must stay in .gitignore — never create or commit them manually
tmp_app_logs/
data_scraping/
data_providers/
config-aspirabot.json
```

❌ Never omit type hints on a function or method signature
```python
# BAD
def fetch(url, timeout=30):
    ...

# GOOD
def fetch(url: str, timeout: int = 30) -> str:
    ...
```

❌ Never omit a docstring on a public class or function

❌ Never write a tautological docstring
```python
# BAD — restates the method name, adds no value
def load_config(self) -> dict:
    """Load the config."""

# GOOD — explains contract and failure modes
def load_config(self) -> dict:
    """Read and parse the application configuration from disk.

    Returns:
        A dictionary of configuration values ready for use by services.

    Raises:
        DatabaseUnavailableError: If the file is missing or contains invalid JSON.
    """
```

❌ Never use bare `except` clauses
```python
# BAD — swallows all errors silently
try:
    ...
except:
    pass

# GOOD
try:
    ...
except PlaywrightTimeoutError as e:
    logger.error("Délai de chargement dépassé : %s", e)
    raise
```

❌ Never trigger data loading or dynamic content building inside a View constructor

The View constructor must only build the widget structure (frames, labels, entries, buttons).
It must never call `load()`, `initialize()`, or any method that populates or rebuilds dynamic content.
The Presenter is responsible for deciding *when* content is loaded, via an explicit method call.

```python
# BAD — the View self-initializes its dynamic form at construction time
class ProviderEditView(ttk.Frame):
    def _create_gestion_widgets(self):
        self._inline_form = StepInlineFormPanel(self)
        self._inline_form.load(None)  # ← View decides when to load — wrong

# GOOD — the View only builds widget structure; the Presenter triggers loading
class ProviderEditView(ttk.Frame):
    def _create_gestion_widgets(self):
        self._inline_form = StepInlineFormPanel(self)
        # No load() here — the Presenter calls show_inline_form() when needed

class ProviderEditPresenter:
    def create_new(self):
        ...
        self._view.show_inline_form(None)  # ← Presenter decides when to load
```

For lazy tab initialization (content loaded only on first visit), use `MainView.set_on_show()`:
```python
main_view.set_on_show(TitleModuleEnum.E_SCRIPTS, scripts_presenter.ensure_providers_loaded)
```