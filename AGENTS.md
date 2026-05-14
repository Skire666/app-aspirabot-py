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
- `interfaces/` defines abstract contracts (ABCs) implemented by MVP layers — never place concrete logic here.
- `shared/` contains helpers, constants, and base classes usable by any layer — never place business logic here.
- Neither `interfaces/` nor `shared/` belong to any MVP layer — they are cross-cutting concerns.

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

These resources are created automatically at launch — **do not version them**:

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

---

## Code Conventions

This project enforces a high standard of code quality. All contributions must follow these rules.

### General Style
- Strict **PEP 8** compliance
- **Docstrings** required on all public classes and functions, **Google style**
- **Method length**: 25 lines maximum — if a method exceeds this, break it down
- **Comments**: one comment per logical block, approximately every 5 lines of code
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
class IScrapingService(ABC):
    def run(self, url: str) -> list[dict]:
        return []  # ← must be abstract
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

---

### Code Quality Violations

❌ Never write a method longer than 25 lines — break it down instead

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
main_view.set_on_show(C_TITLE_MODULE_SCRAPING, scraping_presenter.ensure_providers_loaded)
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

## Error Messages

### Ownership by layer

| What | Where |
|------|-------|
| Raw errors (code + context) | `models/` — `ValidationError` dataclass |
| Message templates | `presenters/messages.py` |
| Formatting logic | `presenters/` — converts raw errors into `list[str]` |
| Display | `views/` — receives `list[str]`, renders, nothing else |

### `ValidationError` — `models/`

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ValidationError:
    code: str
    context: dict  # Raw data used for formatting
```

### Message templates — `presenters/messages.py`

All user-facing strings live here. No string is ever written inline in
business logic or view code.

```python
ERROR_TEMPLATES: dict[str, str] = {
    "invalid_operator": (
        "Step {step}: operator must be one of: "
        "equal, not_equal, greater_than, less_than, "
        "greater_or_equal, less_or_equal."
    ),
    "empty_field": "Step {step}: field '{field}' cannot be empty.",
}
```

### Presenter — formats and delegates

```python
from presenters.messages import ERROR_TEMPLATES

messages = [
    ERROR_TEMPLATES[e.code].format(**e.context)
    for e in raw_errors
]
self._view.show_errors(messages)   # or clear_errors()
```

### View — passive display only

```python
def show_errors(self, messages: list[str]) -> None: ...
def clear_errors(self) -> None: ...
```

The View receives ready-to-display strings. It never formats,
conditions, or owns any message text.

### Interface — `interfaces/`

```python
class IErrorDisplayView(Protocol):
    def show_errors(self, messages: list[str]) -> None: ...
    def clear_errors(self) -> None: ...
```

Presenters depend on this protocol, never on the concrete View —
enabling tests without Tkinter.

---

### Anti-patterns — Error Messages

❌ Never write a user-facing string inline in a service or presenter

```python
# BAD — string belongs in presenters/messages.py
errors.append(f"Step {index}: operator must be one of: equal, ...")
```

❌ Never format or build error messages inside the View

```python
# BAD — the View must receive ready-to-display strings
def show_errors(self, raw_errors: list[ValidationError]) -> None:
    for e in raw_errors:
        msg = ERROR_TEMPLATES[e.code].format(**e.context)  # ← Presenter's job
```

❌ Never pass `ValidationError` objects to the View

```python
# BAD — the View must only receive list[str]
self._view.show_errors(raw_errors)  # ← format first in the Presenter
```