# Aspirabot

> Web scraping tool with a visual Tkinter GUI, powered by Playwright (Chromium).

Aspirabot allows users to create, configure, and execute data extraction or web automation workflows visually, without writing code. It uses a real browser engine to bypass standard antibot detection.

---

## Prerequisites

Before getting started, make sure you have the following installed on your machine:

- **Python 3.14** — [python.org](https://www.python.org/downloads/)
- **Git** — [git-scm.com](https://git-scm.com/)
- **VS Code** (recommended) — [code.visualstudio.com](https://code.visualstudio.com/)
- **Terminal** — PowerShell, Command Prompt, bash, zsh, ...

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd app-aspirabot
```

### 2. Create the virtual environment

/!\ The folder '__src__/' must be visible. /!\

```bash
python -m venv venv
```

### 3. Activate the virtual environment

** On Windows (with PowerShell)**
```powershell
.\venv\Scripts\activate
```

> If PowerShell blocks script execution with a red error message, use `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

** On macOS & Linux**
```bash
source venv/bin/activate
```

> You should see `(venv)` appear at the start of your terminal prompt.

### 4. Install dependencies

```bash
pip install -r './__src__/requirements.txt'
```

### 5. Install Chromium for Playwright

```bash
playwright install chromium
```

### 6. Deploy the project in editable mode

```bash
pip install -e .
```

---

## Run the Application

Make sure the virtual environment is activated, then:

```bash
python __src__/main.py
```

---

## VS Code Setup

### Recommended extensions

Install the following extensions from the VS Code marketplace (`Ctrl+Shift+X`):

| Extension | Publisher | Purpose |
|-----------|-----------|---------|
| **Python** | Microsoft | Python language support |
| **Ruff** | Astral Software | Linter & formatter |
| **Mypy Type Checker** | Microsoft | Static type checking |
| **Pytest** | Little Fox Team | Test runner integration |

### Settings

Open your user settings (`Ctrl+Shift+P` → *Open User Settings JSON*) and add:

```json
"[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.fixAll.ruff": "explicit",
        "source.organizeImports.ruff": "explicit"
    }
}
```

Ruff will now automatically lint and format your code on every save (`Ctrl+S`).

---

## Project Structure

```
app-aspirabot/
├── __src__/
│   ├── interfaces/     # Abstract base classes — contract-based programming
│   ├── models/         # Business entities and data structures (domain)
│   ├── views/          # Tkinter GUI components (no business logic)
│   ├── presenters/     # Orchestration: connects views to services
│   ├── repositories/   # Data read/write layer
│   ├── services/       # Business logic and domain rules
│   ├── shared/         # Contains common utilities and base code
│   └── main.py         # Application entry point
├── __tests__/          # Test files (mirrors __src__/ structure)
├── venv/               # Virtual environment (not versioned)
├── AGENTS.md           # Instructions for AI coding agents
├── pyproject.toml      # Project configuration (Ruff, Mypy, Pytest)
└── README.md           # This file
```

The project follows the **MVP (Model-View-Presenter)** pattern strictly.
See `AGENTS.md` for architecture rules.

---

## Code Quality Tools

The project enforces a high standard of code quality.
All tools are configured in `pyproject.toml`.

### Ruff — linter & formatter

```bash
# Check for issues
ruff check ./__src__/

# Auto-fix what can be fixed
ruff check --fix ./__src__/

# Format code
ruff format ./__src__/
```

### Mypy — static type checking

```bash
pip install mypy
mypy ./__src__/
```

---

### Test — Pytest

```bash
pytest __tests__/ -v
```

---

## Runtime-Generated Files

These are created automatically when the app runs. **Do not version them** (already listed in `.gitignore`):

```
./tmp_app_logs/
./data_scraping/
./data_providers/
./config-aspirabot.json
```

---

## Project Cleanup

Remove compiled Python files (`__pycache__`, `.pyc`, etc.):

```bash
python -m pip install pyclean
python -m pyclean ./ -v
```

---

## Further Reading

- `AGENTS.md` — architecture rules, code conventions, and AI agent instructions
- `pyproject.toml` — full configuration for Ruff, Mypy, and Pytest
