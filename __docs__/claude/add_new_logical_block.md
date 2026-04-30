Tu peux me faire un prompt agentique pour une nouvelle brique. Voici ce que j'ai écrit pour l'instant :

Lit le fichier 'AGENTS.m'd et suit les instructions qu'il contient.
On va rajouter une nouvelle brique logique : "COUNT_ELEMENT".

Pour cela, tu vas analyser une brique logique déjà existante : "WAIT_ELEMENT".
Voici les endroits qui la référence :
- models\step_scrapping_[model.py](http://model.py)
- services\scrapping_[service.py](http://service.py)
- services\workflow_[service.py](http://service.py)
- views\step_edit_dialog_[view.py](http://view.py)
- views\workflow_builder_[view.py](http://view.py)

Regarde l'existant et le fonctionnement.
Une fois listé et compris les différents éléments à coder, tu vas établir une liste des modifications à entreprendre pour pouvoir ajouter la nouvelle brique logique "COUNT_ELEMENT".

Cette nouvelle brique logique permet :
- D'attendre X temps (hour, min, sec, millisec) avant de compter les éléments.
- Les éléments à compter sont une évaluation du nombre de "css/selector". Il retourne un nombre >= 0 (soit 'COUNT').
- Il est possible de renseigner si le compteur est en succès/éches en fonction de la condition que l'utilisateur a saisie : Est un [ succès | échec ] si COUNT est [ compris entre | non compris entre | égale à | différent de | supérieur à | inférieur à | supérieur ou égal à | inférieur ou égal à ]
- L'exécution est bloquée jusqu'à ce que l'évaluation soit terminé.


----------------------------------------------------
----------------------------------------------------
Réponse de claude code 4.6 Sonnet - 2026.04.30
----------------------------------------------------
----------------------------------------------------


# Task: Add the `COUNT_ELEMENT` action type to the Workflow Builder

## Read first — mandatory before writing any code

1. Read `AGENTS.md` fully and follow every instruction it contains.
2. Read these files fully before touching anything:
   - `models/step_scrapping_model.py`
   - `services/scrapping_service.py`
   - `services/workflow_service.py`
   - `views/step_edit_dialog_view.py`
   - `views/workflow_builder_view.py`
3. Locate every reference to `WAIT_ELEMENT` across these 5 files. List them before writing a single line of code. `COUNT_ELEMENT` follows the exact same propagation pattern — use `WAIT_ELEMENT` as your implementation blueprint.

Do not create new files. Do not modify any existing action type.

---

## Goal

Add a new `COUNT_ELEMENT` action type that:
- Waits a configurable delay before evaluating
- Counts DOM elements matching a CSS selector
- Evaluates a user-defined condition against the count
- Blocks execution until the evaluation is complete
- Marks the step as **success** or **failure** based on the condition result

---

## Specification

### `params` keys

| Key | Type | Default | Required |
|---|---|---|---|
| `selector` | `str` | `""` | yes |
| `wait_duration` | `int \| float` | `0` | no — 0 means no pre-wait |
| `wait_unit` | `str` | `"second"` | yes if `wait_duration > 0` |
| `success_if` | `str` | `"success"` | yes — `"success"` or `"failure"` |
| `operator` | `str` | `"equal"` | yes — see allowed values below |
| `value_min` | `int` | `0` | yes if operator is `"between"` or `"not_between"` |
| `value_max` | `int` | `0` | yes if operator is `"between"` or `"not_between"` |
| `value` | `int` | `0` | yes for all other operators |

### Allowed values for `operator`

| Internal value | French display label | Requires |
|---|---|---|
| `"between"` | `"compris entre"` | `value_min` and `value_max` |
| `"not_between"` | `"non compris entre"` | `value_min` and `value_max` |
| `"equal"` | `"égale à"` | `value` |
| `"not_equal"` | `"différent de"` | `value` |
| `"greater_than"` | `"supérieur à"` | `value` |
| `"less_than"` | `"inférieur à"` | `value` |
| `"greater_or_equal"` | `"supérieur ou égal à"` | `value` |
| `"less_or_equal"` | `"inférieur ou égal à"` | `value` |

### Condition evaluation logic

```python
def _evaluate(count: int, operator: str, value: int, value_min: int, value_max: int) -> bool:
    match operator:
        case "between":      return value_min <= count <= value_max
        case "not_between":  return not (value_min <= count <= value_max)
        case "equal":        return count == value
        case "not_equal":    return count != value
        case "greater_than": return count > value
        case "less_than":    return count < value
        case "greater_or_equal": return count >= value
        case "less_or_equal":    return count <= value
        case _: return False
```

The step outcome is then resolved as:
```python
condition_met = _evaluate(count, operator, value, value_min, value_max)
step_success = condition_met if success_if == "success" else not condition_met
```

Log both the raw `count` and the final `step_success` result to the execution log.

---

## Changes required — file by file

### 1. `models/step_scrapping_model.py`

Add after the last existing `StepType` member:
```python
COUNT_ELEMENT = "COUNT_ELEMENT"
```

Add to `_DEFAULT_PARAMS`:
```python
StepType.COUNT_ELEMENT.value: {
    "selector": "",
    "wait_duration": 0,
    "wait_unit": "second",
    "success_if": "success",
    "operator": "equal",
    "value_min": 0,
    "value_max": 0,
    "value": 0,
},
```

---

### 2. `services/scrapping_service.py`

Add a `COUNT_ELEMENT` execution block following the same structure as `WAIT_ELEMENT`.

Execution sequence:
1. If `wait_duration > 0`, wait the configured delay (reuse the existing unit-to-ms conversion and '_UNIT_TO_MS' to help)
2. Count elements matching `selector` using the appropriate Playwright call (e.g. `page.locator(selector).count()`).
3. Log: `f"COUNT_ELEMENT : {count} élément(s) trouvé(s) pour '{selector}'"`.
4. Evaluate the condition using the logic above.
5. Log the outcome: `f"COUNT_ELEMENT : {'succès' if step_success else 'échec'} (condition: COUNT {operator} ...)"`.
6. Return or raise according to the existing step success/failure handling pattern found in `WAIT_ELEMENT`.

---

### 3. `services/workflow_service.py`

Add validation for `COUNT_ELEMENT` following the same dispatch pattern as `WAIT_ELEMENT`:

```python
allowed_units = {"hour", "minute", "second", "millisecond"}
allowed_operators = {
    "between", "not_between", "equal", "not_equal",
    "greater_than", "less_than", "greater_or_equal", "less_or_equal"
}
allowed_success_if = {"success", "failure"}

if not params.get("selector", "").strip():
    errors.append("COUNT_ELEMENT : le sélecteur CSS est obligatoire.")
if params.get("wait_duration", 0) < 0:
    errors.append("COUNT_ELEMENT : wait_duration doit être >= 0.")
if params.get("wait_duration", 0) > 0 and params.get("wait_unit") not in allowed_units:
    errors.append(f"COUNT_ELEMENT : wait_unit invalide — {params.get('wait_unit')!r}.")
if params.get("success_if") not in allowed_success_if:
    errors.append(f"COUNT_ELEMENT : success_if invalide — {params.get('success_if')!r}.")
if params.get("operator") not in allowed_operators:
    errors.append(f"COUNT_ELEMENT : operator invalide — {params.get('operator')!r}.")

op = params.get("operator")
if op in {"between", "not_between"}:
    if params.get("value_min", 0) > params.get("value_max", 0):
        errors.append("COUNT_ELEMENT : value_min doit être <= value_max.")
```

---

### 4. `views/step_edit_dialog_view.py`

Add `_build_form_count_element()` following the same structure as `_build_form_wait_element()`.

Register the new type in the type selector Combobox with the French label: `"Compter les éléments"`.

**Form layout — in order:**

**Row 1 — Sélecteur CSS**
- `ttk.Label` + `ttk.Entry`, pre-fills from `params["selector"]`
- Required — inline red error if empty on confirm

**Row 2 — Pré-attente (single horizontal line)**
- `ttk.Label` text `"Attendre"` + `ttk.Spinbox` for `wait_duration` (0–99999) + `ttk.Combobox` (readonly) for `wait_unit` + `ttk.Label` text `"(0 = immédiat)"`
- Unit display/value mapping: `heure`/`"hour"`, `minute`/`"minute"`, `seconde`/`"second"`, `milli-sec`/`"millisecond"`

**Row 3 — Résultat (single horizontal line)**
- `ttk.Label` text `"C'est un"` + `ttk.Combobox` for `success_if` (display: `"succès"` / `"échec"`, values: `"success"` / `"failure"`) + `ttk.Label` text `"si COUNT est"`

**Row 4 — Condition (single horizontal line, dynamic)**
- `ttk.Combobox` (readonly) for `operator` — all 8 French display labels
- When `operator` changes, the value area to the right is rebuilt dynamically:
  - If `"between"` or `"not_between"`: show two `ttk.Spinbox` widgets labeled `"min"` and `"max"`, pre-fill from `value_min` / `value_max`
  - All other operators: show one `ttk.Spinbox` labeled `"valeur"`, pre-fill from `value`

All fields pre-fill correctly when editing an existing `COUNT_ELEMENT` step.
Validation on confirm: `selector` non-empty; if `between`/`not_between`, `value_min <= value_max`.

#### `StepHelpTexts`

Add an entry for `"Compter les éléments"`:
- What the step does (count DOM elements, block until done)
- How the pre-wait works
- How to read the condition: `"C'est un succès si COUNT est supérieur à 3"`
- The difference between `between` (inclusive) and `not_between`
- That the raw count and result are both logged

---

### 5. `views/workflow_builder_view.py`

Add one `if` branch to `_format_step_label()`:

```python
if t == StepType.COUNT_ELEMENT:
    op_labels = {
        "between": "compris entre", "not_between": "non compris entre",
        "equal": "=", "not_equal": "≠",
        "greater_than": ">", "less_than": "<",
        "greater_or_equal": "≥", "less_or_equal": "≤",
    }
    op = op_labels.get(p.get("operator", "equal"), "?")
    selector = p.get("selector", "")
    if p.get("operator") in {"between", "not_between"}:
        val_str = f"{p.get('value_min', 0)} et {p.get('value_max', 0)}"
    else:
        val_str = str(p.get("value", 0))
    return f"Compter — {selector} [{op} {val_str}]"
```

---

## Checklist before finishing

- [ ] All references to `WAIT_ELEMENT` were listed before any code was written
- [ ] `StepType.COUNT_ELEMENT` added — no existing member modified
- [ ] `_DEFAULT_PARAMS` entry present with all 8 keys and correct defaults
- [ ] `scrapping_service.py` — pre-wait applied when `wait_duration > 0`
- [ ] `scrapping_service.py` — element count logged before condition evaluation
- [ ] `scrapping_service.py` — `success_if` correctly inverts the condition result
- [ ] `workflow_service.py` — validates selector, wait, success_if, operator, and value_min <= value_max
- [ ] Inline form has 4 rows in the correct order
- [ ] Operator Combobox dynamically shows 1 or 2 value spinboxes depending on operator
- [ ] All fields pre-fill correctly when editing an existing step
- [ ] `StepHelpTexts` entry added for `"Compter les éléments"`
- [ ] `_format_step_label()` uses symbolic operators (=, ≠, >, ≤…) for compact display
- [ ] No existing action type was modified