# Task: Add 4 new step types to the Workflow Builder

## Read first — mandatory before writing any code

1. Read `AGENTS.md` fully and follow every instruction it contains.
2. Read these files fully before touching anything:
   - `src/models/step_scraping_model.py` — contains `StepType` enum and `_DEFAULT_PARAMS`. **All additions go here.**
   - `src/views/workflow_builder_view.py` — contains `_format_step_label()` and `WorkflowBuilderView`. Extend, do not rewrite.
   - `src/views/step_edit_dialog_view.py` — contains `StepInlineFormPanel`, `StepHelpPanel`, `StepHelpTexts`. Extend, do not rewrite.

Do not create new files. Do not modify any existing step type.

---

## Goal

Add exactly **4 new `StepType` members** and wire them end-to-end through every layer that already handles step types. No architectural changes — only additive modifications following the existing patterns.

The 4 new types are listed below in their natural execution order within a typical scraping workflow:

1. `CLOSE_TABS` — clean up browser state before starting work
2. `EXTRACT_TEXT` — extract content from the page
3. `JUMP_TO_STEP` — conditional flow control
4. `END_PROCESS` — terminate the workflow

---

## New step types — specification (4 total)

### 1. `CLOSE_TABS`

Closes browser tabs, optionally keeping only those whose URL matches a substring filter and respecting a maximum tab count threshold.

`params` keys:

| Key | Type | Default | Required |
|---|---|---|---|
| `url_filter` | `str` | `""` | no — empty string means no filter |
| `max_tabs` | `int` | `0` | yes |

Validation: `max_tabs >= 1`. `url_filter` may be empty.

---

### 2. `EXTRACT_TEXT`

Extracts text or markup from one or more DOM elements matching a CSS selector, and logs the result to the execution log.

`params` keys:

| Key | Type | Default | Required |
|---|---|---|---|
| `selector` | `str` | `""` | yes |
| `extract_mode` | `str` | `"innerText"` | yes |
| `target` | `str` | `"first"` | yes |

**Allowed values for `extract_mode`:**

| Value | Description |
|---|---|
| `"innerText"` | Visible rendered text (respects CSS visibility) |
| `"textContent"` | Raw text content including hidden nodes |
| `"outerHTML"` | Full HTML of the element including its own tag |
| `"innerHTML"` | HTML content inside the element |
| `"value"` | Value attribute — for `<input>` and `<textarea>` elements |

**Allowed values for `target`:**

| Value | Description |
|---|---|
| `"first"` | First element matching the selector |
| `"last"` | Last element matching the selector |
| `"all"` | All elements matching the selector (results joined with newline) |

If the selector matches nothing, log a warning line and continue — do not raise an error.

---

### 3. `JUMP_TO_STEP`

Conditionally jumps to a target step based on whether the previous step succeeded or failed.

`params` keys:

| Key | Type | Default | Required |
|---|---|---|---|
| `condition` | `str` | `"success"` | yes |
| `target_hexastring` | `int` | `0` | yes |

Allowed values for `condition`: `"success"`, `"failure"`, `"always"`.

`target_hexastring` is a **zero-based** index into the current workflow steps list. It must be >= 0. It must not point to itself (no self-loop). The presenter is responsible for passing the current steps list to the inline form so the UI can populate the target selector dynamically.

Validation: `condition` is one of the three allowed values, `target_hexastring >= 0`, `target_hexastring != current_step_index`.

---

### 4. `END_PROCESS`

Signals the end of the scraping run and waits a fixed delay before releasing control.

`params` keys:

| Key | Type | Default | Required |
|---|---|---|---|
| `wait_duration` | `int \| float` | `0` | yes |
| `wait_unit` | `str` | `"second"` | yes |

Allowed values for `wait_unit`: `"minute"`, `"second"`, `"millisecond"` — same set as `SLEEP`.

Validation: `wait_duration >= 1` and `wait_unit` is one of the four allowed values.

---

## Changes required — layer by layer

### 1. `src/models/step_scraping_model.py`

Add the 4 new members to the `StepType` enum after `SCROLL_DOWN`, in execution order:
```python
CLOSE_TABS = "CLOSE_TABS"
EXTRACT_TEXT = "EXTRACT_TEXT"
JUMP_TO_STEP = "JUMP_TO_STEP"
END_PROCESS = "END_PROCESS"
```

Add their entries to `_DEFAULT_PARAMS`:
```python
StepType.CLOSE_TABS.value: {
    "url_filter": "",
    "max_tabs": 1,
},
StepType.EXTRACT_TEXT.value: {
    "selector": "",
    "extract_mode": "innerText",
    "target": "first",
},
StepType.JUMP_TO_STEP.value: {
    "condition": "success",
    "target_hexastring": 0,
},
StepType.END_PROCESS.value: {
    "wait_duration": 1,
    "wait_unit": "second",
},
```

Do not modify any existing entry in `StepType` or `_DEFAULT_PARAMS`.

---

### 2. `src/views/workflow_builder_view.py`

Extend `_format_step_label()` only. Add 4 new `if` branches.

```python
if t == StepType.CLOSE_TABS:
    f = p.get("url_filter", "")
    max_t = p.get("max_tabs", 0)
    filter_str = f" (filtre : {f})" if f else ""
    return f"Fermer onglets — max {max_t}{filter_str}"

if t == StepType.EXTRACT_TEXT:
    mode = p.get("extract_mode", "innerText")
    target = p.get("target", "first")
    selector = p.get("selector", "")
    return f"Extraire texte — {selector} [{mode} / {target}]"

if t == StepType.JUMP_TO_STEP:
    cond = p.get("condition", "success")
    target = p.get("target_hexastring", 0)
    return f"Sauter à l'étape {target + 1} — si {cond}"

if t == StepType.END_PROCESS:
    return f"Fin du processus — attendre {p.get('wait_duration', 0)} {p.get('wait_unit', '')}"
```

Do not modify any other method in this file.

---

### 3. `src/views/step_edit_dialog_view.py`

#### `StepInlineFormPanel` — add 4 new sub-forms

Register the 4 new types in the type selector Combobox (French display labels, in execution order):
`"Fermer les onglets"`, `"Extraire le texte (CSS)"`, `"Sauter à une étape"`, `"Fin du processus"`

**`_build_form_CLOSE_TABS()`**
- `ttk.Entry` for `url_filter` (optional, placeholder: `"Laisser vide pour ne pas filtrer"`)
- `ttk.Spinbox` for `max_tabs` (range 0–999, default 0)

**`_build_form_EXTRACT_TEXT()`**

Fields in order:

1. **Sélecteur CSS** — `ttk.Entry`, pre-fills from `params["selector"]`, required (inline error on confirm if empty)
2. **Mode d'extraction** — `ttk.Combobox` (readonly):

| Display | Internal value |
|---|---|
| `innerText — Texte visible` | `"innerText"` |
| `textContent — Texte brut complet` | `"textContent"` |
| `outerHTML — HTML complet de l'élément` | `"outerHTML"` |
| `innerHTML — HTML interne` | `"innerHTML"` |
| `value — Valeur du champ (input/textarea)` | `"value"` |

3. **Éléments ciblés** — `ttk.Combobox` (readonly):

| Display | Internal value |
|---|---|
| `Premier élément uniquement` | `"first"` |
| `Dernier élément uniquement` | `"last"` |
| `Tous les éléments` | `"all"` |

**`_build_form_JUMP_TO_STEP()`**
- `ttk.Combobox` for `condition` (display: `"Si succès"` / `"Si échec"` / `"Toujours"`; maps to `"success"` / `"failure"` / `"always"`; default `"Si succès"`)
- `ttk.Combobox` for `target_hexastring` populated dynamically from the live step list. **The presenter must call `set_available_steps(steps)` before opening this form.** Display as `"Étape N — <label>"` (1-based), store zero-based index as value.

Add `set_available_steps(steps: list[StepScrapingModel])` to `StepInlineFormPanel` if it does not already exist.

**`_build_form_END_PROCESS()`**
- `ttk.Spinbox` for `wait_duration` (range 0–C_MAXIMUM_SIZE_IMAGE, default 0)
- `ttk.Combobox` for `wait_unit` (values: `minute` / `seconde` / `milli-sec`; maps to `"minute"` / `"second"` / `"millisecond"`)

---

#### `StepHelpTexts` — add 4 new entries to `BY_LABEL`

Add concise French help texts for (in execution order):
- `"Fermer les onglets"` — explain the URL filter (empty = close all) and the max_tabs threshold
- `"Extraire le texte (CSS)"` — cover: CSS selector syntax with short examples (`h1`, `.title`, `#price`); difference between each extract_mode; when to use `value`; effect of target (mention newline join for "all"); silent warning on no match
- `"Sauter à une étape"` — explain the condition/target logic and the self-loop restriction
- `"Fin du processus"` — explain the delay before releasing control

Follow the format and existing entries exactly.

---

### 4. `src/services/workflow_service.py`

In the per-step-type validation dispatch, add cases for the 4 new types in execution order:

```python
# CLOSE_TABS
if params.get("max_tabs", -1) < 0:
    errors.append("CLOSE_TABS : max_tabs doit être >= 0.")

# EXTRACT_TEXT
allowed_modes = {"innerText", "textContent", "outerHTML", "innerHTML", "value"}
allowed_targets = {"first", "last", "all"}
if not params.get("selector", "").strip():
    errors.append("EXTRACT_TEXT : le sélecteur CSS est obligatoire.")
if params.get("extract_mode") not in allowed_modes:
    errors.append(f"EXTRACT_TEXT : mode d'extraction invalide — {params.get('extract_mode')!r}.")
if params.get("target") not in allowed_targets:
    errors.append(f"EXTRACT_TEXT : cible invalide — {params.get('target')!r}.")

# JUMP_TO_STEP
allowed_conditions = {"success", "failure", "always"}
if params.get("condition") not in allowed_conditions:
    errors.append(f"JUMP_TO_STEP : condition invalide — {params.get('condition')!r}.")
if params.get("target_hexastring", -1) < 0:
    errors.append("JUMP_TO_STEP : target_hexastring doit être >= 0.")
if params.get("target_hexastring") == step_index:
    errors.append("JUMP_TO_STEP : une étape ne peut pas pointer vers elle-même.")

# END_PROCESS
allowed_units = {"minute", "second", "millisecond"}
if params.get("wait_duration", -1) < 0:
    errors.append("END_PROCESS : wait_duration doit être >= 0.")
if params.get("wait_unit") not in allowed_units:
    errors.append(f"END_PROCESS : unité de temps invalide — {params.get('wait_unit')!r}.")
```

Return errors in the existing format. Do not change the method signature.

---

## Checklist before finishing

- [ ] `StepType` has exactly 4 new members in execution order, no existing member modified
- [ ] `_DEFAULT_PARAMS` has 4 new entries with the correct defaults
- [ ] `_format_step_label()` handles all 4 new types without hitting the fallback
- [ ] The inline form Combobox lists all 4 new types in French, in execution order
- [ ] Each new sub-form pre-fills correctly when editing an existing step of that type
- [ ] Inline validation shows errors without closing the form
- [ ] `validate()` in the service layer covers all 4 new types
- [ ] `EXTRACT_TEXT` — all 5 extract_mode display labels map to correct internal values
- [ ] `EXTRACT_TEXT` — all 3 target display labels map to correct internal values
- [ ] `JUMP_TO_STEP` — target selector is populated from the live step list via `set_available_steps()`
- [ ] `JUMP_TO_STEP` — self-loop is rejected by both UI and service validation
- [ ] `StepHelpTexts.BY_LABEL` has entries for all 4 new French labels
- [ ] No existing step type behaviour was altered