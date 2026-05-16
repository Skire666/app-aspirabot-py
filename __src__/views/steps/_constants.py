"""Shared view-layer constants for all step form definitions.

Provides unit mappings, display lists, and the safe-int helper used by
every IStepFormDef implementation.  Centralising these avoids duplication
across the 15 form-def files.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from typing import Any

from shared.constants import (
    C_UNITS_TIME_ALLOWED_FOR_MODEL,
    C_UNITS_TIME_ALLOWED_FOR_VIEW,
)

# ---------------------------------------------------------------------------
# Unit display / model mappings
# ---------------------------------------------------------------------------

# Display strings shown in Comboboxes.
WAIT_UNIT_DISPLAY: list[str] = list(C_UNITS_TIME_ALLOWED_FOR_VIEW)

# Display → internal model value ("sec" → "s").
WAIT_UNIT_VIEW_TO_MODEL: dict[str, str] = dict(zip(WAIT_UNIT_DISPLAY, C_UNITS_TIME_ALLOWED_FOR_MODEL, strict=True))

# Internal model value → display ("s" → "sec").
WAIT_UNIT_MODEL_TO_VIEW: dict[str, str] = dict(zip(C_UNITS_TIME_ALLOWED_FOR_MODEL, WAIT_UNIT_DISPLAY, strict=True))

# ---------------------------------------------------------------------------
# Playwright wait-state values
# ---------------------------------------------------------------------------

C_CHOICES_WAIT_PAGE_STATE: list[str] = ["domcontentloaded", "load", "networkidle"]

# ---------------------------------------------------------------------------
# Download mode values
# ---------------------------------------------------------------------------

DOWNLOAD_MODES: list[str] = ["first", "last", "all"]

# ---------------------------------------------------------------------------
# Click mode values
# ---------------------------------------------------------------------------

CLICK_MODES: list[str] = ["Normal", "Forced", "JS Direct"]

# ---------------------------------------------------------------------------
# JUMP_TO_STEP condition display / model mappings
# ---------------------------------------------------------------------------

CONDITION_DISPLAY: list[str] = ["Si succès", "Si échec", "Toujours"]  # GARDER 'Toujours' à la fin
CONDITION_VALUES: list[str] = ["success", "failure", "always"]
CONDITION_VIEW_TO_MODEL: dict[str, str] = dict(zip(CONDITION_DISPLAY, CONDITION_VALUES, strict=True))
CONDITION_MODEL_TO_VIEW: dict[str, str] = dict(zip(CONDITION_VALUES, CONDITION_DISPLAY, strict=True))

# ---------------------------------------------------------------------------
# EXTRACT_TEXT display / model mappings
# ---------------------------------------------------------------------------

EXTRACT_MODE_DISPLAY: list[str] = [
    "innerText — Texte visible",
    "textContent — Texte brut complet",
    "outerHTML — HTML complet de l'élément",
    "innerHTML — HTML interne",
    "value — Valeur du champ (input/textarea)",
]
EXTRACT_MODE_VALUES: list[str] = ["innerText", "textContent", "outerHTML", "innerHTML", "value"]
EXTRACT_MODE_VIEW_TO_MODEL: dict[str, str] = dict(zip(EXTRACT_MODE_DISPLAY, EXTRACT_MODE_VALUES, strict=True))
EXTRACT_MODE_MODEL_TO_VIEW: dict[str, str] = dict(zip(EXTRACT_MODE_VALUES, EXTRACT_MODE_DISPLAY, strict=True))

EXTRACT_TARGET_DISPLAY: list[str] = [
    "Premier élément uniquement",
    "Dernier élément uniquement",
    "Tous les éléments",
]
EXTRACT_TARGET_VALUES: list[str] = ["first", "last", "all"]
EXTRACT_TARGET_VIEW_TO_MODEL: dict[str, str] = dict(
    zip(EXTRACT_TARGET_DISPLAY, EXTRACT_TARGET_VALUES, strict=True)
)
EXTRACT_TARGET_MODEL_TO_VIEW: dict[str, str] = dict(
    zip(EXTRACT_TARGET_VALUES, EXTRACT_TARGET_DISPLAY, strict=True)
)

# ---------------------------------------------------------------------------
# COUNT_ELEMENT operator display / model mappings
# ---------------------------------------------------------------------------

COUNT_OP_DISPLAY: list[str] = [
    "égal à",
    "différent de",
    "inférieur à",
    "supérieur à",
    "inférieur ou égal à",
    "supérieur ou égal à",
]
COUNT_OP_VALUES: list[str] = [
    "equal",
    "not_equal",
    "less_than",
    "greater_than",
    "less_or_equal",
    "greater_or_equal",
]
COUNT_OP_VIEW_TO_MODEL: dict[str, str] = dict(zip(COUNT_OP_DISPLAY, COUNT_OP_VALUES, strict=True))
COUNT_OP_MODEL_TO_VIEW: dict[str, str] = dict(zip(COUNT_OP_VALUES, COUNT_OP_DISPLAY, strict=True))

COUNT_SUCCESS_IF_DISPLAY: list[str] = ["succès", "échec"]
COUNT_SUCCESS_IF_VALUES: list[str] = ["success", "failure"]
COUNT_SUCCESS_IF_VIEW_TO_MODEL: dict[str, str] = dict(
    zip(COUNT_SUCCESS_IF_DISPLAY, COUNT_SUCCESS_IF_VALUES, strict=True)
)
COUNT_SUCCESS_IF_MODEL_TO_VIEW: dict[str, str] = dict(
    zip(COUNT_SUCCESS_IF_VALUES, COUNT_SUCCESS_IF_DISPLAY, strict=True)
)

# ---------------------------------------------------------------------------
# Shared widget helper
# ---------------------------------------------------------------------------


def safe_int_widget(widgets: dict[str, Any], key: str, default: int) -> int:
    """Reads an integer from a StringVar widget, falling back to ``default``.

    Args:
        widgets: Dict of widget variables populated by ``build_form``.
        key: The parameter key to read.
        default: Value returned when the widget is absent or non-numeric.

    Returns:
        Integer value or ``default``.

    Raises:
        None.
    """
    var = widgets.get(key)
    if var is None:
        return default
    try:
        return int(var.get())
    except ValueError, TypeError:
        return default


# EOF
