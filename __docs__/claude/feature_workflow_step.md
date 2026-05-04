# Task: Build the Workflow Builder feature

## Read first — mandatory before writing any code

1. Read `AGENTS.md` fully and follow every instruction it contains.
2. Read and understand these files before touching anything:
   - `src/models/provider_model.py` — fully implemented, source of truth for provider structure
   - `src/models/step_scraping_model.py` — class is a **placeholder**: defined and referenced but empty body. You will implement it.
   - `src/views/provider_edit_view.py` — existing view; the Workflow Builder will be embedded inside it. Locate the frame named **"Workflow & Instructions"** — this is your insertion point.
3. Inspect `src/interfaces/` — list all existing abstract base classes before creating new ones.
4. Inspect `src/shared/` — identify base classes and utilities to inherit from or reuse.

Do not create anything until steps 1–4 are complete.

---

## Goal

Implement the **Workflow Builder** UI and its full backend stack (service, repository, model).

The UI must be embedded **inside the existing `"Workflow & Instructions"` frame** in `provider_edit_view.py` — not as a new window or a separate top-level. Replace the placeholder content of that frame with the workflow builder widget.

---

## Step 1 — Implement the `StepScraping` model

The class in `src/models/step_scraping_model.py` is empty. Implement it now.

- Inspect `provider_model.py` to understand how `StepScraping` is referenced and what fields are expected.
- Define a `StepType` enum in `step_scraping_model.py` — do not create it elsewhere.
- Use Python dataclass conventions (`@dataclass`, native type hints, no `from __future__ import annotations`).

### Step types and their parameter contracts

Each `StepScraping` instance holds a `step_type: StepType` and a `params: dict` whose keys depend on the type.

| `StepType` | `params` keys | Defaults | Required |
|---|---|---|---|
| `OPEN_URL` | `url: str`, `wait_state: str` | `url="https://example.com/"`, `wait_state="domcontentloaded"` | both |
| `SLEEP` | `duration: int \| float`, `unit: str` | `duration=0` | both |
| `RANDOM_PAUSE` | `min: int \| float`, `max: int \| float`, `unit: str` | `min=0`, `max=1` | all three |
| `REFRESH_PAGE` | `clear_cache: bool` | `clear_cache=False` | always valid |
| `DOWNLOAD_IMAGE` | `mode: str`, `height_min: int`, `height_max: int`, `width_min: int`, `width_max: int` | `mode="largest"`, `0/999999` for dimensions | all five |
| `WAIT_IMAGE_SIZE` | `height_min: int`, `height_max: int`, `width_min: int`, `width_max: int` | `0/999999` | all four |
| `CLICK_ELEMENT` | `selector: str`, `click_mode: str` | `click_mode="Normal"` | both |
| `WAIT_ELEMENT` | `selector: str` | — | required |
| `SCROLL_DOWN` | `pixels: int` | `pixels=1000` | required |

Allowed values for constrained fields:
- `wait_state`: `"commit"`, `"domcontentloaded"`, `"load"`, `"networkidle"`
- `unit` (SLEEP / RANDOM_PAUSE): `"hour"`, `"minute"`, `"second"`, `"millisecond"`
- `mode` (DOWNLOAD_IMAGE): `"largest"`, `"first"`, `"last"`, `"all"`
- `click_mode` (CLICK_ELEMENT): `"Normal"`, `"Forced"`, `"JS Direct"`

---

## Step 2 — Create the Workflow model

File: `src/models/workflow_model.py`

- Represents an ordered list of `StepScraping` attached to a provider.
- No logic, no methods beyond basic dataclass helpers.
- Reuses `StepScraping` — do not redefine step structure here.

---

## Step 3 — Create interfaces

Only create interfaces that do not already exist in `src/interfaces/`.

Files to create if absent:
- `src/interfaces/workflow_repository_interface.py`

# workflow_repository_interface.py
class WorkflowRepositoryInterface(ABC):
    @abstractmethod
    def load(self, provider_id_file: str) -> Workflow: ...
    @abstractmethod
    def save(self, provider_id_file: str, workflow: Workflow) -> None: ...
```

---

## Step 4 — Implement the service

File: `src/services/workflow_service.py`

Business rules to enforce in `validate()`:
- At least 1 step
- First step must be of type `OPEN_URL`
- Every step must satisfy its own param validation contract (see Step 1 table)
- `RANDOM_PAUSE`: `min` must be strictly less than `max`

No Tkinter import. No file access. Fully unit-testable in isolation.

---

## Step 5 — Implement the repository

File: `src/repositories/workflow_repository.py`

- Persistence target: `config-aspirabot.json`
- **Read the existing JSON structure before writing any serialization code.** Do not overwrite or rename existing keys.
- Serialize/deserialize `Workflow` ↔ JSON under a key scoped to the provider (e.g. `providers.<provider_id_file>.workflow`). Adapt to the actual structure found in the file.

---

## Step 6 — Build the embedded UI

### 6a. Step edit dialog — `src/views/step_edit_dialog_view.py`

A `tk.Toplevel` modal. Layout:

1. A `ttk.Combobox` at the top to select the step type (display labels in French, values are `StepType` enum members).
2. A dynamic form area below: when the type changes, the form area is cleared and rebuilt with the fields specific to that type.
3. Confirm / Cancel buttons at the bottom.
4. Pre-fills all fields when editing an existing step.
5. Returns the result via a `.result: StepScraping | None` attribute.

**Dynamic form — one sub-form per step type:**

| Step type | Fields to render |
|---|---|
| `OPEN_URL` | `ttk.Entry` for URL + `ttk.Combobox` for wait state (`commit`, `domcontentloaded`, `load`, `networkidle`) |
| `SLEEP` | `ttk.Spinbox` for duration + `ttk.Combobox` for unit |
| `RANDOM_PAUSE` | Two `ttk.Spinbox` (min / max) + `ttk.Combobox` for unit |
| `REFRESH_PAGE` | Single `ttk.Checkbutton` "Clear cache" |
| `DOWNLOAD_IMAGE` | `ttk.Combobox` for mode + 4 `ttk.Spinbox` for height min/max and width min/max, arranged in a 2×2 grid labeled "Height" / "Width" |
| `WAIT_IMAGE_SIZE` | 4 `ttk.Spinbox` same layout as above, no mode selector |
| `CLICK_ELEMENT` | `ttk.Entry` for CSS selector + `ttk.Combobox` for click mode (`Normal`, `Forced`, `JS Direct`) |
| `WAIT_ELEMENT` | `ttk.Entry` for CSS selector |
| `SCROLL_DOWN` | `ttk.Spinbox` for pixel count |

Validation runs on Confirm click. Show inline error messages (red label below offending field) — do not close the dialog on error. Validation rules mirror the service layer (see Step 4).

### 6b. Workflow builder widget — embedded in `provider_edit_view.py`

Locate the `"Workflow & Instructions"` frame and replace its placeholder content with:

**Step list** (scrollable):
- One `ttk.Frame` card per step
- Each card: step index, a human-readable label derived from the step type and its key param (e.g. "Open URL — https://example.com", "Sleep — 2 seconds", "Click — .btn-submit"), action buttons: ↑ ↓ edit delete
- ↑ disabled on first step, ↓ disabled on last step
- Selected card highlighted with a distinct background color

**Toolbar** (inside the same frame, above the list):
- "Add step" button
- "Run workflow" button (disabled when 0 steps)

**Log area** (below the list, inside the same frame):
- `scrolledtext.ScrolledText`, read-only, shows execution output line by line
- `ttk.Progressbar`, visible only during execution

Do not modify the layout outside the `"Workflow & Instructions"` frame.

---

## Step 7 — Implement the presenter

File: `src/presenters/workflow_builder_presenter.py`

### View ↔ Presenter contract

The View exposes callbacks (Presenter sets them) and render methods (Presenter calls them):

```python
# Callbacks set by the Presenter on the view
view.on_add_step: Callable | None
view.on_edit_step: Callable[[int], None] | None
view.on_delete_step: Callable[[int], None] | None
view.on_move_step: Callable[[int, int], None] | None   # index, direction (-1/+1)
view.on_run_workflow: Callable | None

# Render methods the Presenter calls on the view
view.render_steps(steps: list[StepScraping]) -> None
view.set_run_button_state(enabled: bool) -> None
view.show_toast(message: str, level: str = "info") -> None
view.append_log(line: str) -> None
```

### Execution threading

- Run workflow in a `threading.Thread`
- Use `threading.Event` for cancellation
- Send UI updates back via `view.after()` — never update Tkinter widgets from a background thread directly

---

## Architecture rules — non-negotiable

| Layer | Owns | Must NOT |
|---|---|---|
| `model` | Data structure only | Import Tkinter, call services or repositories |
| `service` | Business rules, validation | Import Tkinter, read/write files |
| `repository` | File I/O, serialization | Contain business logic |
| `view` | Tkinter widgets, layout, callbacks | Contain any logic beyond rendering |
| `presenter` | Wires view ↔ service | Access files directly, instantiate models |

---

## Order of execution — follow exactly

1. Read `AGENTS.md`, then the four source files listed at the top
2. Inspect `src/interfaces/` and `src/shared/`
3. Implement `StepScraping` model
4. Create `Workflow` model
5. Create interfaces (only if missing)
6. Implement `WorkflowService`
7. Read `config-aspirabot.json` structure, then implement `WorkflowRepository`
8. Implement `step_edit_dialog_view.py`
9. Embed the workflow builder UI into the `"Workflow & Instructions"` frame in `provider_edit_view.py`
10. Implement `WorkflowBuilderPresenter`
11. Wire the presenter into the existing presenter that owns `provider_edit_view.py`
12. Launch the application — confirm the frame renders correctly and all interactions work