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
├── validators/     # Pydantic-based domain validators (launch profile)
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
| `Model`         | `shared/`, `pydantic` (infrastructure only)                  | `View`, `ViewModel`, `Presenter`, `Service`, `Repository` |
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
| `validators/`   | `_validator.py`     | `launch_validator.py`                  |
| `interfaces/`   | `i_*.py`            | `i_scraping_view.py`                   |

The class inside a file is always the PascalCase counterpart of the file name (e.g. `provider_model.py` → `ProviderModel`, `scenario_edit_view_model.py` → `ScenarioEditViewModel`).

> The shared ViewModel infrastructure base lives in `view_models/view_model_base.py` → `ViewModelBase`. It is the one file in `view_models/` not suffixed `_view_model.py`, because it is infrastructure, not a concrete per-view ViewModel.

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

## ViewModel — Presentation State Container

The `ViewModel` (VM) is the **single, typed, observable contract** between a `View` and its
`Presenter`. It is the only owner of UI state. Conceptually it is a *presentation-state DTO that
happens to be observable*: it holds the data the screen needs (as Tkinter Vars), recomputes its own
derived state, dispatches user actions to the Presenter, and exposes a frozen snapshot for reading.

A correct VM is **pure UI plumbing**: no business rule, no service, no widget, no domain Model.
If a VM method contains a domain decision, the decision is misplaced (→ Service). If it touches a
widget, the binding is misplaced (→ View).

### Location and naming

- Folder: `__src__/view_models/`
- File: `<module>_view_model.py` (e.g. `scenario_edit_view_model.py`)
- Class: `<Module>ViewModel` in PascalCase (e.g. `ScenarioEditViewModel`)
- Base class: `view_models/view_model_base.py` → `ViewModelBase` (shared infrastructure)

| Element | Convention | Example |
|---|---|---|
| Any `tk.*Var` | suffix `_var` | `url_var`, `is_busy_var`, `can_submit_var` |
| Capability / boolean Var | `can_<x>_var` / `is_<x>_var` | `can_submit_var`, `is_dirty_var` |
| Action method (called by View) | imperative verb | `submit()`, `cancel()`, `open_selected()` |
| Presenter binding hook | prefix `bind_` | `bind_submit(cb)`, `bind_rows_changed(cb)` |
| Stored Presenter callback | prefix `_on_` | `self._on_submit` |
| Read-only snapshot type | `<Module>ViewState` (frozen) | `ScenarioEditViewState` |
| Collection row type | `<Thing>RowState` (frozen) | `ScenarioRowState` |

---

### Var taxonomy and ownership matrix

Every piece of UI state falls into exactly one category. The **ownership matrix is the core
invariant of the layer** — violating "who writes what" is what makes a VM untestable or loop-prone.

| Var kind | Purpose | Declared by | **Written by** | Read by | Two-way |
|---|---|---|---|---|---|
| **Source** | User input | VM | View (widget) **and** Presenter (on load) | VM recompute, snapshot | yes |
| **Derived** | Computed from sources | VM | **VM recompute ONLY** | View, Presenter (read-only) | no (VM→View) |
| **Status / message** | Busy flag, error text | VM | **Presenter ONLY** | View | no (Presenter→View) |
| **Selection** | Selected id / index | VM | View (widget) **and** Presenter | VM, Presenter | yes |
| **Collection** (non-Var) | List/table rows | VM | Presenter (via `set_rows`) | View (render) | no |

Hard consequences of the matrix:

- The **View never writes a derived or status Var** — it only reads them (via `textvariable=`/trace).
- The **Presenter never writes a derived Var** — derived state is recomputed by the VM, never pushed.
- The **VM never writes a status Var** with business content — it may only reset it (e.g. clear on
  `cancel()`); the meaningful value (error message, busy flag) is always set by the Presenter.

---

### Construction protocol (strict order)

The order in `__init__` is not cosmetic — getting it wrong silently breaks bindings.

1. Call `super().__init__(master)` first (stores `master`, prepares trace/debounce registries).
2. Create **every** Var as `self.<name>_var = tk.…Var(master=master, value=…)`.
   A Var stored in a local variable is garbage-collected after `__init__` and its binding dies.
3. Initialise `self._on_*` callback slots to `None`.
4. Register traces via `self._register_trace(src_var, self._guarded_recompute)` for every Var that
   feeds derived state. Never call `var.trace_add` directly — the base must track the id for disposal.
5. Run `self._guarded_recompute()` **once** to compute initial derived state.

---

### Derived state and the recompute gate

Derived Vars (`can_submit_var`, `is_dirty_var`, …) are recomputed **inside the VM**, never in the
View, and never set by the Presenter. All recomputation flows through a single guarded entry point
provided by `ViewModelBase`, which solves three problems at once:

- **Re-entrancy** — a recompute writes a derived Var, whose own (accidental) trace would re-enter.
- **Suspension** — during a batched multi-Var load, recompute is skipped and run once at the end.
- **Churn** — `_set_if_changed` writes a Var only when the value actually changes (fewer traces).

```python
# view_models/view_model_base.py
from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from contextlib import contextmanager
from typing import Iterator

class ViewModelBase:
    """Infrastructure shared by all ViewModels.

    Provides tracked trace registration, a re-entrant/suspendable recompute gate,
    change-guarded Var writes, debounced scheduling, and deterministic disposal.
    Subclasses override ``_recompute_derived`` and never manage trace ids,
    re-entrancy flags, or pending ``after`` calls themselves.
    """

    def __init__(self, master: tk.Misc) -> None:
        # Real Tk root/widget; Vars and after() scheduling are anchored to it.
        self._master = master
        # (var, trace_id) pairs registered through _register_trace, for disposal.
        self._trace_ids: list[tuple[tk.Variable, str]] = []
        # Pending debounced callbacks, keyed by a stable string.
        self._after_ids: dict[str, str] = {}
        # >0 while a batch_update is active: recompute is deferred.
        self._suspend_depth = 0
        # True while inside _recompute_derived: blocks re-entrant recompute.
        self._in_recompute = False

    # ----- Trace registration (always tracked for disposal) -----

    def _register_trace(self, var: tk.Variable, callback: Callable[..., None]) -> None:
        """Add a write-trace on *var* and remember its id for later removal."""
        trace_id = var.trace_add("write", callback)
        self._trace_ids.append((var, trace_id))

    # ----- Guarded Var write -----

    def _set_if_changed(self, var: tk.Variable, value: object) -> None:
        """Write *value* into *var* only when it differs from the current value."""
        if var.get() != value:
            var.set(value)

    # ----- Recompute gate -----

    def _guarded_recompute(self, *_: object) -> None:
        """Single entry point for derived-state recomputation.

        No-op while a batch update is active or while already recomputing.
        """
        if self._suspend_depth > 0 or self._in_recompute:
            return
        self._in_recompute = True
        try:
            self._recompute_derived()
        finally:
            self._in_recompute = False

    def _recompute_derived(self) -> None:
        """Recompute all derived Vars. Overridden by subclasses; no-op by default."""

    @contextmanager
    def batch_update(self) -> Iterator[None]:
        """Suspend recomputation for a block of Var writes; recompute once on exit.

        Used by the Presenter when populating several source Vars at once (e.g. on
        load) so derived state is computed a single time instead of once per write.
        """
        self._suspend_depth += 1
        try:
            yield
        finally:
            self._suspend_depth -= 1
            if self._suspend_depth == 0:
                self._guarded_recompute()

    # ----- Debounced scheduling -----

    def _schedule(self, key: str, delay_ms: int, callback: Callable[[], None]) -> None:
        """Debounce *callback* under *key*: a new call cancels the pending one."""
        pending = self._after_ids.get(key)
        if pending is not None:
            self._master.after_cancel(pending)
        self._after_ids[key] = self._master.after(
            delay_ms, lambda: self._run_scheduled(key, callback)
        )

    def _run_scheduled(self, key: str, callback: Callable[[], None]) -> None:
        """Clear the pending id for *key* then run *callback*."""
        self._after_ids.pop(key, None)
        callback()

    # ----- Disposal -----

    def dispose(self) -> None:
        """Remove every registered trace and cancel every pending after-call.

        Must be called by whoever owns the VM lifecycle when the View is discarded
        (app shutdown, dialog close, tab destroy). Idempotent.
        """
        for var, trace_id in self._trace_ids:
            var.trace_remove("write", trace_id)
        self._trace_ids.clear()
        for after_id in self._after_ids.values():
            self._master.after_cancel(after_id)
        self._after_ids.clear()
```

Rules for derived state:

- Derived recomputation lives **only** in `_recompute_derived`.
- Write derived Vars exclusively through `_set_if_changed`.
- Never set a derived Var from a trace callback without going through `_guarded_recompute`.
- A recompute that is **expensive** (regex over a long field, cross-field validation) must be
  debounced via `self._schedule("recompute_x", 150, self._recompute_derived)` rather than run on
  every keystroke. Keep the actual computation in a directly-callable method so tests bypass the timer.

---

### Action methods and binding hooks

User actions never call the Presenter directly. The View calls a **VM action method**
(`vm.submit()`), which dispatches to a callback the Presenter registered once via `bind_submit`.
This keeps the VM the single contract and keeps the View ignorant of the Presenter.

Fail-fast invariants (a wiring bug must surface at startup, not silently no-op):

- `bind_<x>` **raises** if the hook is already bound (double-wiring is a composition error).
- An action method **raises** if its hook is unbound when triggered (the View should never be able
  to fire an unwired action; by the composition order this cannot happen at runtime).
- Action methods **only dispatch** — no `try/except`, no Var transformation, no service call.

```python
# Excerpt — hook + action pattern (messages in French, per project convention)
def bind_submit(self, callback: Callable[[], None]) -> None:
    """Register the Presenter handler for submit(); rejects double binding."""
    if self._on_submit is not None:
        raise AppError("Le hook 'submit' est déjà lié.")
    self._on_submit = callback

def submit(self) -> None:
    """Dispatch the submit action to the registered Presenter callback."""
    if self._on_submit is None:
        raise AppError("Action 'submit' déclenchée sans handler lié.")
    self._on_submit()
```

Parameterised actions take the argument and forward it to a typed hook
(`Callable[[str], None]`), e.g. `select_row(row_id: str)` → `self._on_select(row_id)`.

---

### Snapshot — the read-side DTO

Reading state Var-by-Var in the Presenter is noisy and easy to get out of sync. The VM exposes a
**frozen snapshot dataclass** of its scalar state. This is the "ViewModel as DTO": *write* through
Vars and actions, *read* through one typed, immutable object.

- Use the snapshot whenever the Presenter reads **3 or more** Vars together (e.g. before a save).
- The snapshot contains **primitives only** — it must not import or expose a domain Model.
- The snapshot is **read-only**: it never sets anything back.

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class ScenarioEditViewState:
    """Immutable read-only view of the scenario-edit VM scalar state."""
    name: str
    url: str
    is_active: bool
    is_busy: bool
    can_submit: bool
    error_message: str
```

---

### Collections and tables (no `ListVar` in Tkinter)

Tkinter has no observable collection Var, so list/table state is the **one exception** to the
"everything is a Var" rule. The pattern:

1. The VM stores rows as a private list of frozen `<Thing>RowState` (primitives only).
2. The VM exposes a read-only `rows` property and a `bind_rows_changed(callback)` hook.
3. The Presenter maps domain Models → row states and calls `vm.set_rows(...)`, which replaces the
   list and fires `rows_changed`.
4. The View subscribes to `rows_changed` and rebuilds its `ttk.Treeview` from `vm.rows`.
5. Selection is a normal Var (`selected_id_var`), two-way like any source Var.

```python
# view_models/scenario_list_view_model.py
from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

from shared.exception_util import AppError
from view_models.view_model_base import ViewModelBase

@dataclass(frozen=True, slots=True)
class ScenarioRowState:
    """One Treeview row, already formatted for display (primitives only)."""
    id_scenario: str
    name: str
    status_label: str

class ScenarioListViewModel(ViewModelBase):
    """UI state for the scenario list: rows, selection, and row actions."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        # Selection (two-way, like any source Var)
        self.selected_id_var = tk.StringVar(master=master, value="")
        # Derived: an action is available only when a row is selected
        self.can_open_var = tk.BooleanVar(master=master, value=False)
        # Collection state (non-Var) + change notification
        self._rows: tuple[ScenarioRowState, ...] = ()
        self._on_rows_changed: Callable[[], None] | None = None
        self._on_open: Callable[[str], None] | None = None
        # Wire derived state and compute it once
        self._register_trace(self.selected_id_var, self._guarded_recompute)
        self._guarded_recompute()

    @property
    def rows(self) -> tuple[ScenarioRowState, ...]:
        """Read-only current rows, for the View to render."""
        return self._rows

    def set_rows(self, rows: list[ScenarioRowState]) -> None:
        """Replace the row set (called by the Presenter) and notify the View."""
        self._rows = tuple(rows)
        if self._on_rows_changed is not None:
            self._on_rows_changed()

    def _recompute_derived(self) -> None:
        """An action is available only when a row is selected."""
        self._set_if_changed(self.can_open_var, bool(self.selected_id_var.get()))

    def bind_rows_changed(self, callback: Callable[[], None]) -> None:
        """Register the View re-render handler; rejects double binding."""
        if self._on_rows_changed is not None:
            raise AppError("Le hook 'rows_changed' est déjà lié.")
        self._on_rows_changed = callback

    def bind_open(self, callback: Callable[[str], None]) -> None:
        """Register the Presenter handler for open_selected()."""
        if self._on_open is not None:
            raise AppError("Le hook 'open' est déjà lié.")
        self._on_open = callback

    def open_selected(self) -> None:
        """Dispatch the open action for the currently selected row id."""
        if self._on_open is None:
            raise AppError("Action 'open' déclenchée sans handler lié.")
        self._on_open(self.selected_id_var.get())
```

> `ScenarioRowState` is **already formatted** for display (`status_label`, not a raw enum). The
> Model→row mapping and the formatting happen in the Presenter — the VM stores presentation-ready
> primitives, never domain objects.

---

### Canonical pattern — single edit form

```python
# view_models/scenario_edit_view_model.py
from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

from shared.exception_util import AppError
from view_models.view_model_base import ViewModelBase

@dataclass(frozen=True, slots=True)
class ScenarioEditViewState:
    """Immutable read-only view of the scenario-edit VM scalar state."""
    name: str
    url: str
    is_active: bool
    is_busy: bool
    can_submit: bool
    error_message: str

class ScenarioEditViewModel(ViewModelBase):
    """UI state and action hooks for the scenario edit form.

    Source Vars are bound to widgets; derived Vars (can_submit) are recomputed
    automatically and never written by the View or the Presenter.
    """

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        # Source Vars (two-way: widget + Presenter on load)
        self.name_var = tk.StringVar(master=master, value="")
        self.url_var = tk.StringVar(master=master, value="")
        self.is_active_var = tk.BooleanVar(master=master, value=False)
        # Status Vars (written by the Presenter only)
        self.error_message_var = tk.StringVar(master=master, value="")
        self.is_busy_var = tk.BooleanVar(master=master, value=False)
        # Derived Var (written by the VM recompute only)
        self.can_submit_var = tk.BooleanVar(master=master, value=False)
        # Presenter callback slots
        self._on_submit: Callable[[], None] | None = None
        self._on_cancel: Callable[[], None] | None = None
        # Wire recompute on every input that affects can_submit, then compute once
        for var in (self.name_var, self.url_var, self.is_busy_var):
            self._register_trace(var, self._guarded_recompute)
        self._guarded_recompute()

    # ----- Derived state -----

    def _recompute_derived(self) -> None:
        """Recompute can_submit: both fields filled and not currently busy."""
        ready = (
            bool(self.name_var.get().strip())
            and bool(self.url_var.get().strip())
            and not self.is_busy_var.get()
        )
        self._set_if_changed(self.can_submit_var, ready)

    # ----- Snapshot -----

    def snapshot(self) -> ScenarioEditViewState:
        """Return an immutable copy of the current scalar UI state."""
        return ScenarioEditViewState(
            name=self.name_var.get(),
            url=self.url_var.get(),
            is_active=self.is_active_var.get(),
            is_busy=self.is_busy_var.get(),
            can_submit=self.can_submit_var.get(),
            error_message=self.error_message_var.get(),
        )

    # ----- Binding hooks -----

    def bind_submit(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for submit(); rejects double binding."""
        if self._on_submit is not None:
            raise AppError("Le hook 'submit' est déjà lié.")
        self._on_submit = callback

    def bind_cancel(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for cancel(); rejects double binding."""
        if self._on_cancel is not None:
            raise AppError("Le hook 'cancel' est déjà lié.")
        self._on_cancel = callback

    # ----- Action methods (dispatch only) -----

    def submit(self) -> None:
        """Dispatch the submit action to the registered Presenter callback."""
        if self._on_submit is None:
            raise AppError("Action 'submit' déclenchée sans handler lié.")
        self._on_submit()

    def cancel(self) -> None:
        """Dispatch the cancel action to the registered Presenter callback."""
        if self._on_cancel is None:
            raise AppError("Action 'cancel' déclenchée sans handler lié.")
        self._on_cancel()
```

### View — binds, renders, forwards (zero logic)

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

        # Non-Var binding: mirror can_submit_var onto the button's enabled state.
        # The View tracks its own trace id so it can detach it on teardown.
        self._enable_trace = vm.can_submit_var.trace_add("write", self._sync_enabled)
        self._sync_enabled()

    def _sync_enabled(self, *_: object) -> None:
        """Mirror vm.can_submit_var onto the submit button's state."""
        state = "normal" if self._vm.can_submit_var.get() else "disabled"
        self._submit_btn.configure(state=state)

    def teardown(self) -> None:
        """Detach the View-owned trace before the VM is disposed."""
        self._vm.can_submit_var.trace_remove("write", self._enable_trace)
```

### Presenter — maps, batches, reads via snapshot

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
        vm.bind_submit(self._on_submit)
        vm.bind_cancel(self._on_cancel)

    def load_scenario(self, id_scenario: str) -> None:
        """Fetch a scenario and populate the VM Vars in a single recompute."""
        try:
            scenario = self._service.get_scenario(id_scenario)
        except ScenarioNotFoundError as e:
            self._vm.error_message_var.set(str(e))
            return
        # One recompute of can_submit fires when the batch block exits.
        with self._vm.batch_update():
            self._vm.name_var.set(scenario.name)
            self._vm.url_var.set(scenario.url)
            self._vm.is_active_var.set(scenario.active)
            self._vm.error_message_var.set("")

    def _on_submit(self) -> None:
        """Read VM state via snapshot, call the service, reflect status into Vars."""
        self._vm.is_busy_var.set(True)
        self._vm.error_message_var.set("")
        state = self._vm.snapshot()
        try:
            self._service.save_scenario(
                name=state.name, url=state.url, active=state.is_active
            )
        except AppError as e:
            self._logger.error("Erreur lors de l'enregistrement : %s", e, exc_info=True)
            self._vm.error_message_var.set(str(e))
        finally:
            self._vm.is_busy_var.set(False)

    def _on_cancel(self) -> None:
        """Reset the form to a clean state in a single recompute."""
        with self._vm.batch_update():
            self._vm.name_var.set("")
            self._vm.url_var.set("")
            self._vm.is_active_var.set(False)
            self._vm.error_message_var.set("")
```

### Composition root — wiring and disposal

```python
# main.py — assemble VM, View, and Presenter; anchor against GC; dispose on shutdown
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

    # Keep a reference to the Presenter so the GC does not collect it.
    root._presenter = presenter  # noqa: SLF001 — intentional GC anchor

    # Disposal order is always View first, VM second: the View owns traces on VM
    # Vars, so it must detach them before the VM tears the Vars' traces down.
    def _on_close() -> None:
        view.teardown()
        vm.dispose()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    view.pack(fill="both", expand=True)
    root.mainloop()

if __name__ == "__main__":
    main()
```

> Transient dialogs and destroyable lazy tabs follow the same `teardown()` → `dispose()` sequence.

### Testing a ViewModel

VM tests need a hidden Tk root but **no widgets, no `mainloop`**. They assert on Var values and on
dispatch, after calling action methods directly.

```python
# __tests__/view_models/conftest.py
import tkinter as tk
import pytest

@pytest.fixture
def tk_root():
    """Provide a hidden Tk root for Var creation, torn down after the test."""
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()
```

```python
# __tests__/view_models/test_scenario_edit_view_model.py
from view_models.scenario_edit_view_model import ScenarioEditViewModel

def test_can_submit_requires_both_fields(tk_root):
    vm = ScenarioEditViewModel(master=tk_root)
    assert vm.can_submit_var.get() is False
    vm.name_var.set("Demo")
    assert vm.can_submit_var.get() is False  # url still empty
    vm.url_var.set("https://x.test")
    assert vm.can_submit_var.get() is True

def test_busy_blocks_submit(tk_root):
    vm = ScenarioEditViewModel(master=tk_root)
    vm.name_var.set("Demo")
    vm.url_var.set("https://x.test")
    vm.is_busy_var.set(True)
    assert vm.can_submit_var.get() is False

def test_submit_dispatches_to_bound_handler(tk_root):
    vm = ScenarioEditViewModel(master=tk_root)
    calls = []
    vm.bind_submit(lambda: calls.append("submit"))
    vm.submit()
    assert calls == ["submit"]

def test_batch_update_recomputes_once(tk_root):
    vm = ScenarioEditViewModel(master=tk_root)
    computed = []
    vm.can_submit_var.trace_add("write", lambda *_: computed.append(1))
    with vm.batch_update():
        vm.name_var.set("Demo")
        vm.url_var.set("https://x.test")
    assert computed == [1]  # one transition, not two

def test_snapshot_reflects_current_state(tk_root):
    vm = ScenarioEditViewModel(master=tk_root)
    vm.name_var.set("Demo")
    vm.url_var.set("https://x.test")
    snap = vm.snapshot()
    assert (snap.name, snap.url, snap.can_submit) == ("Demo", "https://x.test", True)

def test_dispose_stops_recomputation(tk_root):
    vm = ScenarioEditViewModel(master=tk_root)
    vm.dispose()
    vm.name_var.set("Demo")
    vm.url_var.set("https://x.test")
    assert vm.can_submit_var.get() is False  # traces removed, no recompute
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

# GOOD — derived state belongs in _recompute_derived via the recompute gate
```

❌ Never call a Service or a Repository from the ViewModel
```python
# BAD
class ScenarioEditViewModel:
    def submit(self):
        self._service.save_scenario(...)   # ← VM must not know services exist

# GOOD — VM dispatches to a Presenter-registered callback
def submit(self):
    if self._on_submit is None:
        raise AppError("Action 'submit' déclenchée sans handler lié.")
    self._on_submit()
```

❌ Never set a derived Var without `_set_if_changed` inside the recompute gate
```python
# BAD — write triggers the callback which writes again → infinite loop
def _recompute_derived(self):
    self.derived_var.set(self.source_var.get().upper())

# GOOD — change-guarded write, run inside the base recompute gate
def _recompute_derived(self):
    self._set_if_changed(self.derived_var, self.source_var.get().upper())
```

❌ Never let the Presenter touch a widget directly
```python
# BAD
self._view._submit_btn.configure(state="disabled")

# GOOD — mutate a VM Var; the View's trace reflects it
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
the bindings to the ViewModel. It is equally responsible for the disposal sequence
(View `teardown()` → VM `dispose()`) when a view is discarded.

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
class AspirabotBaseError(Exception):
    """Base error for the application."""

...
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
| `ViewModel`  | Wiring invariants only (`AppError`)     | Nothing — it is pure state.                                              |
| `View`       | —                                       | Nothing — it only renders.                                              |

> The ViewModel raises `AppError` **only** for composition-time wiring invariants
> (double `bind_<x>`, action triggered without a bound handler). It never raises for
> domain or runtime reasons — those are the Service's and Presenter's responsibility.

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
| Message templates             | `shared/i18n_fra.py`                     |
| Storage of formatted message  | `ViewModel` (`error_message_var`)        |
| Display                       | `View` — bound to `vm.error_message_var` |

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
### Presenter — formats and writes to a VM Var

```python
messages = [format_error(e) for e in raw_errors]
self._vm.error_message_var.set("\n".join(messages))
```

### Anti-patterns — Error Messages

❌ Never write a user-facing string inline in a Service, Presenter, or ViewModel
❌ Never call `.format(**e.context)` directly — always go through `format_error()`
❌ Never pass `FieldValidationErrorModel` instances into a VM Var — format first
❌ Never compose or format error messages inside the View

---

## Validators — Pydantic V2

All domain-level validation is handled by **Pydantic V2**. No validation logic is
allowed inline in Presenters, Services, ViewModels, or Views.

Pydantic validation will grow to cover all domain objects. This section is the authoritative
reference for how to write, place, and consume validators in this project regardless of context.

---

### Decision framework — where to place validators

The placement depends on whether the domain object is a Pydantic model or a plain dataclass:

| Object type | Validator placement | Trigger |
|---|---|---|
| `BaseModel` subclass (frozen, value object) | Directly inside the class via `@field_validator` / `@model_validator` | `model_validate(data, context=ctx)` |
| `@dataclass` (mutable, owns business methods) | Standalone `_<Domain>ValidationSchema` in `validators/<domain>_validator.py` | Public `validate_<domain>(obj)` function |

**Rule of thumb:** if the object will ever be mutated after construction, or has factory
classmethods (`get_default`, `import_from_json`, …), keep it as a dataclass and create a
standalone schema. If the object is immutable and purely structural, make it a `BaseModel`.

---

### Pattern A — Validators embedded in the model

Use this pattern when the domain object **is** a Pydantic `BaseModel`.

#### A1 — Always-on structural validation (no context guard)

For constraints that are always true regardless of external state and safe to check at
construction time (e.g., a field that must always be a positive integer):

```python
from pydantic import BaseModel, ConfigDict, field_validator
from shared.i18n_fra import C_SOME_FIELD_INVALID

class MyModel(BaseModel):
    """My domain value object."""

    model_config = ConfigDict(frozen=True)

    count: int

    @field_validator("count")
    @classmethod
    def check_count(cls, v: int) -> int:
        """Reject non-positive counts."""
        if v < 1:
            raise ValueError(C_SOME_FIELD_INVALID)
        return v
```

#### A2 — Context-aware validation (explicit-only, with context guard)

Use this when the rule requires external state (workflow position, database lookup, user
permissions) or when the object is loaded from JSON (potentially stale data) and
construction must never fail:

```python
from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator
from shared.i18n_fra import ERROR_TEMPLATES

class MyParamsModel(BaseModel):
    """Frozen params model with context-aware validators."""

    model_config = ConfigDict(frozen=True)

    pixels: int

    @field_validator("pixels")
    @classmethod
    def check_pixels(cls, v: int, info: ValidationInfo) -> int:
        """Reject pixel counts below 1 — only when context is provided."""
        if not info.context:
            return v  # no validation at construction / JSON deserialization
        if v < 1:
            raise ValueError(ERROR_TEMPLATES["scroll_down_pixels_invalid"].format(...))
        return v
```

The guard `if not info.context: return v` is the key invariant: validators only fire when
the caller explicitly passes a context dict via `model_validate(..., context=ctx)`.

#### A3 — Cross-field / cross-object validator

Use `@model_validator(mode="before")` to check conditions that span multiple fields or
require data not yet assigned to `self`. Receive raw dict input and always guard:

```python
from pydantic import ValidationInfo, model_validator

class MyModel(BaseModel):
    """Model with a cross-field constraint."""

    min_val: int
    max_val: int

    @model_validator(mode="before")
    @classmethod
    def check_range(cls, data: object, info: ValidationInfo) -> object:
        """Reject min_val > max_val."""
        if not isinstance(data, dict) or not info.context:
            return data
        mn, mx = data.get("min_val"), data.get("max_val")
        if isinstance(mn, int) and isinstance(mx, int) and mn > mx:
            raise ValueError(C_RANGE_INVALID)
        return data
```

Use `@model_validator(mode="after")` when the check is easier to express against the
already-constructed model instance (all fields validated and typed):

```python
    @model_validator(mode="after")
    def check_conditional(self) -> "MyModel":
        """Require path only when source type demands it."""
        if self.source_type in _TYPES_REQUIRING_PATH and not self.path:
            raise ValueError(C_PATH_REQUIRED)
        return self
```

`mode="after"` runs only if all field validators passed, so it is appropriate for
constraints that depend on valid field values rather than raw input.

---

### Pattern B — Standalone validation schema (for dataclasses)

Use this pattern when the domain object **is** a `@dataclass`. The schema is a private
Pydantic model that mirrors the fields of the dataclass and is only instantiated transiently.

#### File structure

```
validators/
└── <domain>_validator.py      # one file per validated dataclass (or logical group)
```

#### Internal schema + public API

```python
# validators/profile_validator.py
from __future__ import annotations

from pydantic import BaseModel, ValidationError, field_validator, model_validator
from typing import Self

from models.profile_model import ProfileModel
from shared.i18n_fra import C_EXPORT_FOLDER_REQUIRED, C_THRESHOLD_INVALID

_MAX_THRESHOLD = 9_999_999


class _ProfileValidationSchema(BaseModel):
    """Internal validation schema — never import this class directly."""

    export_folder: str
    threshold: int
    ...

    @field_validator("export_folder")
    @classmethod
    def check_export_folder(cls, v: str) -> str:
        """Reject empty or whitespace-only export paths."""
        if not v or not v.strip():
            raise ValueError(C_EXPORT_FOLDER_REQUIRED)
        return v

    @field_validator("threshold")
    @classmethod
    def check_threshold(cls, v: int) -> int:
        """Reject thresholds outside the accepted range."""
        if not (isinstance(v, int) and 1 <= v <= _MAX_THRESHOLD):
            raise ValueError(C_THRESHOLD_INVALID)
        return v

    @model_validator(mode="after")
    def check_cross_fields(self) -> Self:
        """Cross-field rule on the validated instance."""
        ...
        return self


def _extract_errors(exc: ValidationError) -> list[str]:
    return [
        str(err["ctx"]["error"]) if "ctx" in err and "error" in err["ctx"] else err["msg"]
        for err in exc.errors()
    ]


# ── Public API ──────────────────────────────────────────────────────────────

def validate_profile(profile: ProfileModel) -> list[str]:
    """Validate *profile* and return all French error messages.

    Args:
        profile: The profile to validate.

    Returns:
        Ordered list of error strings; empty when valid.
    """
    try:
        _ProfileValidationSchema(
            export_folder=profile.export_folder or "",
            threshold=profile.threshold,
            ...
        )
        return []
    except ValidationError as exc:
        return _extract_errors(exc)


def validate_profile_first_error(profile: ProfileModel) -> str | None:
    """Return the first error message, or ``None`` when valid.

    Args:
        profile: The profile to validate.

    Returns:
        First French error string, or None when valid.
    """
    errors = validate_profile(profile)
    return errors[0] if errors else None
```

The two public functions (`validate_<domain>` and `validate_<domain>_first_error`) are
the **only** exported symbols. The schema class is always private (underscore prefix).

#### Usage in a Presenter

```python
from validators.profile_validator import validate_profile_first_error

def _validate_before_save(self) -> str | None:
    self._apply_form_to_model()
    return validate_profile_first_error(self._current_profile)
```

---

### Validator type reference

| Decorator | Mode | Receives | Use when |
|---|---|---|---|
| `@field_validator("f")` | — | `v: FieldType, info: ValidationInfo` | Single-field constraint; structural or context-aware |
| `@model_validator` | `"before"` | `data: object, info: ValidationInfo` | Cross-field check on raw dict; condition spans multiple fields; external context needed |
| `@model_validator` | `"after"` | `self: Model` | Cross-field check on the validated instance; condition depends on valid field values |

**Execution order:** `mode="before"` → field validators → `mode="after"`.
Errors from earlier phases prevent later phases from running.

---

### Context pattern (external state injection)

When a validator needs state only available at call time (workflow position, service result,
user session), pass it via the `context` parameter of `model_validate`:

```python
# 1. Define the context shape (document it at the call site or in the class docstring)
ctx: dict[str, object] = {
    "step_index": step_index,      # int — zero-based position in the workflow
    "steps_context": steps_ctx,    # StepsContext — full workflow snapshot
    "step_id": model.step_id,      # str — own step ID for self-reference checks
}

# 2. Trigger validation
try:
    MyParamsModel.model_validate(obj.to_dict(), context=ctx)
except ValidationError as exc:
    errors = _extract_errors(exc)
```

Inside the validator, always guard against absent context before using it:

```python
@field_validator("target")
@classmethod
def check_target(cls, v: str, info: ValidationInfo) -> str:
    """Validate target — requires workflow context."""
    if not info.context:          # absent → skip (construction / deserialization)
        return v
    steps_ctx = info.context.get("steps_context")
    if steps_ctx is not None and steps_ctx.find_by_id(v) is None:
        raise ValueError(C_TARGET_NOT_FOUND)
    return v
```

---

### Error message extraction

Pydantic wraps every `raise ValueError(msg)` into `"Value error, <msg>"` in `err["msg"]`.
Always extract the original message via `err["ctx"]["error"]`:

```python
def _extract_errors(exc: ValidationError) -> list[str]:
    """Extract French error strings from a Pydantic ValidationError."""
    return [
        str(err["ctx"]["error"]) if "ctx" in err and "error" in err["ctx"] else err["msg"]
        for err in exc.errors()
    ]
```

This helper must be defined locally in every `validators/<domain>_validator.py` and in
every service/base that wraps a `model_validate` call.

---

### Error messages — always from `shared/i18n_fra.py`

Every `raise ValueError(...)` inside a validator must reference a constant from
`shared/i18n_fra.py`. User-facing strings are never written inline:

```python
# BAD — string inline in the validator
raise ValueError("Le champ est requis.")

# GOOD — constant from i18n
from shared.i18n_fra import C_FIELD_REQUIRED
raise ValueError(C_FIELD_REQUIRED)

# GOOD — template with context
from shared.i18n_fra import ERROR_TEMPLATES
raise ValueError(ERROR_TEMPLATES["my_error_key"].format(step=step_label(info.context)))
```

---

### Real-time UI validation (is_dirty pattern)

Because context-aware validators only activate via `model_validate(..., context=ctx)`,
they are safe to call at any frequency. A typical Presenter wires validation to the
`is_dirty` flag:

```python
# Presenter — re-validate on every form change
def _on_form_changed(self) -> None:
    self._is_dirty = True
    self._refresh_validation_message()

def _refresh_validation_message(self) -> None:
    error = validate_profile_first_error(self._build_model_from_form())
    self._view.set_verification_message(error or "")
```

For objects using the context pattern, build the context dict from available state:

```python
def _refresh_step_validation(self, step_index: int) -> None:
    ctx = {"step_index": step_index, "steps_context": self._steps_context, "step_id": self._current_id}
    try:
        type(self._current_params).model_validate(self._current_params.to_dict(), context=ctx)
        self._view.set_error("")
    except ValidationError as exc:
        self._view.set_error(_extract_errors(exc)[0])
```

---

### File and naming conventions

| Artifact | Location | Naming rule |
|---|---|---|
| Embedded validator method | Inside the `BaseModel` subclass | `check_<field_or_rule>` |
| Standalone schema (internal) | `validators/<domain>_validator.py` | `_<Domain>ValidationSchema` (private) |
| Public validation functions | `validators/<domain>_validator.py` | `validate_<domain>`, `validate_<domain>_first_error` |
| Error extraction helper | Local to each validator file or base class | `_extract_errors(exc)` |

---

### Dependency rules

| Layer | May import from |
|---|---|
| `BaseModel` subclass (in `models/`) | `pydantic`, `shared/` |
| Standalone validator schema (in `validators/`) | `pydantic`, `models/`, `shared/` |
| `Presenter` | `validators/` (public functions only) |
| `Service` | `validators/` (public functions only) |

Validators must **never** import from `View`, `Presenter`, `ViewModel`, or `Repository`.

---

### Anti-patterns — Validators

❌ Never use `AbstractValidator`, `RuleBuilder`, or `ValidationResult` — these no longer exist
❌ Never write validation predicates inline in a Presenter, Service, or ViewModel
❌ Never expose a `_<Domain>ValidationSchema` class — only the public `validate_*` functions
❌ Never omit the `if not info.context: return v` guard in a context-aware `@field_validator`
   (missing guard runs validation at JSON deserialization time, breaking loading of old data)
❌ Never use `err["msg"]` directly when extracting Pydantic errors — always use `_extract_errors()`
   to strip the `"Value error, "` prefix
❌ Never write user-facing strings inline in a validator — always use `shared/i18n_fra.py` constants
❌ Never override `validate_model()` in a concrete executor — it is generic in `StepExecutorBase`
❌ Never call `model_validate(data)` without a context dict when context-aware validators are defined
```python
# BAD — context missing, all context-aware validators silently skip
MyParams.model_validate(data)

# GOOD — provide the context that validators depend on
MyParams.model_validate(data, context={"step_index": idx, "steps_context": ctx, "step_id": sid})
```
❌ Never place `@model_validator(mode="after")` when the rule depends on raw input data — use `"before"` instead
❌ Never import `View`, `Presenter`, `ViewModel`, or `Repository` from a validator file

---

## Tests

When adding tests:
- Place tests in a `__tests__/` folder at the project root.
- Use **pytest**.
- Mirror the `__src__/` folder structure inside `__tests__/`
  (e.g. `view_models/scenario_edit_view_model.py`
  → `__tests__/view_models/test_scenario_edit_view_model.py`).
- Every new feature must be accompanied by its tests.
- Run tests with:
```bash
pytest __tests__/ -v
```

### Testing ViewModels

The ViewModel is the most testable layer and must be covered **without any widget,
display, or `mainloop`**. A test only needs a hidden `tk.Tk()` root to anchor the Vars,
provided once via a shared fixture:

```python
# __tests__/view_models/conftest.py
import tkinter as tk
import pytest

@pytest.fixture
def tk_root():
    """Provide a hidden Tk root for Var creation, torn down after the test."""
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()
```

Drive the VM by setting **source** Vars and calling **action methods** directly, then
assert on Var values and on dispatch. No Presenter, no Service, no real callback — use a
plain lambda or a small fake as the bound handler.

Every ViewModel test suite must cover, at minimum:

- **Derived state transitions** — each derived Var (`can_submit_var`, `is_dirty_var`, …)
  flips correctly as its source Vars change, including the initial value at construction.
- **Status inputs to derived state** — e.g. setting `is_busy_var` disables `can_submit_var`.
- **Action dispatch** — `vm.submit()` calls the handler registered via `bind_submit`;
  a parameterised action forwards the right argument.
- **Hook fail-fast** — binding a hook twice raises, and triggering an unbound action raises.
- **Batch updates** — a `with vm.batch_update(): …` block recomputes derived state exactly
  once (assert via a trace counter on the derived Var), with the correct final value.
- **Snapshot** — `vm.snapshot()` returns a frozen DTO matching current Var values.
- **Collections** — `set_rows([...])` fires the `rows_changed` hook and exposes the rows
  as an immutable tuple via the `rows` property; selection drives the related derived Var.
- **Disposal** — after `vm.dispose()`, writing a source Var no longer recomputes derived
  state (traces removed) and no pending `after` call remains.

For a **debounced** recompute, call the underlying compute method directly to assert the
result; test the scheduling separately in a dedicated timing test by pumping the loop with
`tk_root.update()` after the debounce delay. Never rely on wall-clock sleeps for logic.

The canonical fixture and a full set of example tests live in the **ViewModel** section.

### Testing Presenters

Presenters are tested with a **real ViewModel** (hidden root) and a **fake Service** that
records calls or raises domain exceptions. Assert on the VM Vars the Presenter is allowed
to mutate (status/source) — never on widgets, which do not exist in the test.

- A successful service call leaves `error_message_var` empty and `is_busy_var` False.
- A raised domain exception (e.g. `ScenarioNotFoundError`) is reflected into
  `error_message_var`; an unexpected `AppError` is logged and surfaces a generic message.
- `load_scenario(...)` populates the source Vars through a single recompute (`batch_update`).

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

❌ Never store a `tk.*Var` as a local variable instead of `self.<name>_var` (silent GC).
❌ Never extend a ViewModel without inheriting `ViewModelBase` and calling `super().__init__(master)` first.
❌ Never compute derived state anywhere but `_recompute_derived` — not in the View, not in the Presenter.
❌ Never write a **derived** Var from the View or the Presenter — derived Vars are VM output only.
❌ Never write a **status** Var (error / busy) from the VM with business content — the Presenter owns it.
❌ Never call `var.trace_add` directly — register through `self._register_trace` so it can be disposed.
❌ Never mutate a Var inside its own recompute without `_set_if_changed` and the recompute gate (loop).
❌ Never set several source Vars one-by-one from the Presenter on load — wrap them in `with vm.batch_update():`.
❌ Never run an expensive recompute on every keystroke — debounce it via `self._schedule(...)`.
❌ Never put logic in an action method (`try/except`, transformation, service call) — it only dispatches.
❌ Never let a `bind_<x>` silently overwrite an existing hook, or let an unbound action no-op — fail fast.
❌ Never call a Service, Repository, or Model from a ViewModel.
❌ Never import a Service, Repository, Model, Presenter, or View into a ViewModel (only `tkinter`, `shared/`).
❌ Never store or expose a domain Model inside the VM, a `RowState`, or a snapshot — primitives only.
❌ Never pass `dict[str, Any]` as UI state — state is typed Vars; the read DTO is a frozen dataclass.
❌ Never return a mutable list from a collection accessor — expose an immutable tuple via a read-only property.
❌ Never skip `dispose()` wiring at the composition root — leaked traces fire on dead state after teardown.
❌ Never build or load data in a ViewModel at construction — the Presenter decides when to load.

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
❌ Never leave a View-owned trace attached when the View is destroyed — detach it in `teardown()` before the VM is disposed.

### Presenter Violations

❌ Never touch a widget directly from a Presenter — mutate a VM Var instead.
❌ Never import `tkinter` from a Presenter.
❌ Never place business logic inside a Presenter — that belongs in a Service.
❌ Never instantiate a Service or Repository inside a Presenter — inject via `__init__`.
❌ Never push derived state into the VM — set only source/status Vars; derived Vars recompute themselves.

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
