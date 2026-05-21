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
├── interfaces/     # Abstract base classes — contract-based programming
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
|-----------------|---|---|
| `View`          | `interfaces/`, `shared/`            | `Service`, `Repository`, `Model` directly |
| `Presenter`     | `Service`, `interfaces/`, `shared/` | `Repository` directly |
| `Service`       | `Repository` (via interface), `Model`, `shared/` | `View`, `Presenter` |
| `Repository`    | `Model`, `shared/`                  | `View`, `Presenter`, `Service` |
| `Model`         | `shared/`                           | Everything else |

> **Rule:** if adding an import would create a cycle or go against the arrow above, the design is wrong — refactor instead.

---

## Python Version

This project targets **Python 3.14**. Do not use syntax or features incompatible with this version.

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
All code conventions (docstrings, inline comments) are written in **English**.
The i18n module (`shared/i18n_fra.py`) is the single source of truth for all French strings.

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

### General Style
- Strict **PEP 8** compliance
- **Docstrings** required on all public classes and functions, **Google style**
- **Method length**: 25 lines maximum — if a method exceeds this, break it down
- **Comments**: one comment per logical block, approximately every 5 lines of code
- **File length**: 1000 lines maximum — if a file exceeds this, split it into focused modules
- **Language**: English only

### Expected Docstring Format (Google Style)
```python
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

### Expected Inline Comment Style
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
from interfaces.i_scraping_view import IScrapingView
from services.scraping_service import ScrapingService

class ScrapingPresenter:
    def __init__(self, view: IScrapingView, service: ScrapingService) -> None:
        self._view = view
        self._service = service
```

Presenters always depend on the `I*` Protocol, **never on the concrete View class**.
This decouples the Presenter from Tkinter entirely and makes it fully testable.

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
All concrete objects are assembled once, in `main.py`, and injected via `__init__`.

```python
# main.py — the ONLY place where concrete classes are instantiated
import tkinter as tk
from repositories.config_repository import ConfigRepository
from services.scraping_service import ScrapingService
from views.main_view import MainView
from presenters.main_presenter import MainPresenter

root = tk.Tk()

config_repo     = ConfigRepository(path=CONFIG_PATH)
scraping_service = ScrapingService(config_repository=config_repo)
main_view       = MainView(root)
main_presenter  = MainPresenter(view=main_view, scraping_service=scraping_service)

root.mainloop()
```

**Rules:**
- Every dependency is passed via `__init__` — no `import` of a concrete class inside a collaborator.
- When the AI adds a new class, it must also update `main.py` with the new wiring.
- No global singletons, no module-level instantiation outside `main.py`.

---

## Logging

Use the standard `logging` module. **Never use `print()` for runtime output.**

### Setup — one logger per module

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
# Repository — trace I/O at DEBUG
def find_by_id(self, provider_id: str) -> Provider | None:
    self._logger.debug("Lecture du provider id=%s", provider_id)
    ...

# Service — trace flow at INFO
def start_scraping(self, provider_id: str) -> None:
    self._logger.info("Démarrage du scraping pour provider id=%s", provider_id)
    ...

# Presenter — log unexpected errors at ERROR
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
- Never log sensitive data (passwords, tokens, personal data).

---

## Error Handling

### Exception hierarchy

All runtime exceptions inherit from a common base defined in `shared/exception_util.py`:

```python
# shared/exception_util.py
class AppError(Exception):
    """Erreur de base de l'application."""

class ScrapingError(AppError): ...
class PageLoadError(ScrapingError): ...
class ProviderError(AppError): ...
class ProviderNotFoundError(ProviderError): ...
class RepositoryError(AppError): ...
class DatabaseUnavailableError(RepositoryError): ...
```

**Rules:**
- Never raise `Exception`, `ValueError`, or `RuntimeError` directly in business code.
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
# Repository — wrap technical errors
def load_config(self) -> dict:
    try:
        with open(self._path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise DatabaseUnavailableError("Impossible de lire la config.") from e

# Service — raise domain errors
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

# GOOD
raise ProviderNotFoundError("Provider introuvable : {id}") from None
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

❌ Never place concrete logic inside `interfaces/`
```python
# BAD — interfaces define contracts only, no implementation
class IScrapingService(Protocol):
    def run(self, url: str) -> list[dict]:
        return []  # ← must be abstract
```

❌ Never use `ABC` to define an interface — always use `typing.Protocol`


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

---

### Code Quality Violations

❌ Never write a method longer than 25 lines — break it down instead

❌ Never write a file longer than 1000 lines — split into focused modules

❌ Never use `print()` — always use `self._logger = logging.getLogger(__name__)`

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
    logger.error("Page load timed out: %s", e)
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
main_view.set_on_show(TitleModuleEnum.C_TITLE_MODULE_SCRAPING, scraping_presenter.ensure_providers_loaded)
```

---

❌ Never commit runtime-generated files or folders
```
# BAD — these must stay in .gitignore
tmp_app_logs/
data_scraping/
data_providers/
config-aspirabot.json
```

---

## Error Messages

### Ownership by layer

| What | Where |
|------|-------|
| Raw errors (code + context) | `models/` — `FieldValidationError` dataclass |
| Message templates | `shared/i18n_fra.py` |
| Formatting logic | `presenters/` — via `format_error()` helper |
| Display | `views/` — receives `list[str]`, renders only |

### `FieldValidationError` — `models/`

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class FieldValidationError:
    """Erreur de validation d'un champ métier.

    Attributes:
        code: Clé du template dans ERROR_TEMPLATES.
        context: Données utilisées pour formater le message.
    """
    code: str
    context: dict[str, str | int]
```

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

### `format_error()` helper — `presenters/`

All formatting goes through this single helper. Never call `.format(**e.context)` directly.

```python
# presenters/error_formatter.py
from models.field_validation_error import FieldValidationError
from shared.i18n_fra import ERROR_TEMPLATES

def format_error(error: FieldValidationError) -> str:
    """Formate une FieldValidationError en message lisible.

    Args:
        error: L'erreur de validation à formater.

    Returns:
        Le message utilisateur prêt à afficher.
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

### View — passive display only

```python
def show_errors(self, messages: list[str]) -> None: ...
def clear_errors(self) -> None: ...
```

The View receives ready-to-display strings. It never formats, conditions, or owns any message text.


### Presenter — formats and delegates

```python
from presenters.error_formatter import format_error

messages = [format_error(e) for e in raw_errors]
self._view.show_errors(messages)
```
### Interface — `interfaces/`

```python
# interfaces/i_error_display_view.py
from typing import Protocol

class IErrorDisplayView(Protocol):
    def show_errors(self, messages: list[str]) -> None: ...
    def clear_errors(self) -> None: ...
```

Presenters depend on this protocol, never on the concrete View —
enabling tests without Tkinter.
### Anti-patterns — Error Messages

❌ Never write a user-facing string inline in a service or presenter

```python
# BAD — string belongs in presenters/messages.py
# BAD
errors.append(f"Étape {index} : l'opérateur doit être...")
```

❌ Never format or build error messages inside the View
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