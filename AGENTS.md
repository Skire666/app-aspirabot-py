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
| `./tmp_app_chromium_session/` | Persisted Chromium session |
| `./tmp_user_brokens/` | Broken/errored items |
| `./tmp_user_providers/` | User provider data |
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
- **Comments**: one comment per logical block, approximately every 4 lines of code
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
