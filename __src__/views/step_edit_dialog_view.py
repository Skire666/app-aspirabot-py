"""Inline form panel for creating and editing a scraping step.

This ttk.LabelFrame is embedded inside WorkflowBuilderView. It displays
a type selector and a dynamic form area. The form is rebuilt whenever the
step type changes. Confirmation fires on_confirm; cancellation fires on_cancel.

Example:
    >>> panel = StepInlineFormPanel(parent_frame)
    >>> panel.on_confirm = lambda step: print(step)
    >>> panel.on_cancel = lambda: print("cancelled")
    >>> panel.load(existing_step)
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import Any

from models.step_scraping_model import StepScrapingModel, StepType
from shared.constants import C_SIZE_HEXASTRING_WORKFLOW_ITEM_ID
from shared.random_util import generate_rng_hexastring
from views.components.canvas_checkbox import CanvasCheckbox

from __src__.shared.numbers_util import C_CONSTANT_INVALID_INT

# French display labels for each step type (Combobox values).
STEP_TYPE_LABELS: dict[StepType, str] = {
    StepType.OPEN_URL: "Ouvrir une URL",
    StepType.REFRESH_PAGE: "Rafraîchir la page",
    StepType.SLEEP: "Attendre une durée fixe",
    StepType.RANDOM_PAUSE: "Attendre aléatoirement",
    StepType.DOWNLOAD_IMAGE: "Télécharger les images",
    StepType.WAIT_IMAGE_SIZE: "Vérifier une taille d'image",
    StepType.WAIT_ELEMENT: "Vérifier les éléments",
    StepType.COUNT_ELEMENT: "Compter les éléments",
    StepType.CLICK_ELEMENT: "Cliquer sur un élément",
    StepType.SCROLL_DOWN: "Défiler vers le bas",
    StepType.EXTRACT_TEXT: "Extraire contenu textuel",
    StepType.JUMP_TO_STEP: "Si OK/KO, se rendre à ...",
    StepType.CLOSE_TABS: "Fermer des onglets",
    StepType.END_PROCESS: "Fin du processus",
}

# Reverse mapping for label → StepType lookup.
_LABEL_TO_TYPE: dict[str, StepType] = {v: k for k, v in STEP_TYPE_LABELS.items()}

_ALL_LABELS: list[str] = list(STEP_TYPE_LABELS.values())

# Allowed constrained values (mirrors service layer constants).
_WAIT_STATES = ["commit", "domcontentloaded", "load", "networkidle"]
_UNITS = ["heure", "minute", "seconde", "milliseconde"]
_DOWNLOAD_MODES = ["largest", "first", "last", "all"]
_CLICK_MODES = ["Normal", "Forced", "JS Direct"]

# --- EXTRACT_TEXT display/value mappings ---
_EXTRACT_MODE_DISPLAY: list[str] = [
    "innerText — Texte visible",
    "textContent — Texte brut complet",
    "outerHTML — HTML complet de l'élément",
    "innerHTML — HTML interne",
    "value — Valeur du champ (input/textarea)",
]
_EXTRACT_MODE_VALUES: list[str] = ["innerText", "textContent", "outerHTML", "innerHTML", "value"]
_EXTRACT_MODE_MAP: dict[str, str] = dict(zip(_EXTRACT_MODE_DISPLAY, _EXTRACT_MODE_VALUES))
_EXTRACT_MODE_REVERSE: dict[str, str] = dict(zip(_EXTRACT_MODE_VALUES, _EXTRACT_MODE_DISPLAY))

# --- EXTRACT_TEXT target display/value mappings ---
_TARGET_DISPLAY: list[str] = [
    "Premier élément uniquement",
    "Dernier élément uniquement",
    "Tous les éléments",
]
_TARGET_VALUES: list[str] = ["first", "last", "all"]
_TARGET_MAP: dict[str, str] = dict(zip(_TARGET_DISPLAY, _TARGET_VALUES))
_TARGET_REVERSE: dict[str, str] = dict(zip(_TARGET_VALUES, _TARGET_DISPLAY))

# --- JUMP_TO_STEP condition display/value mappings ---
_CONDITION_DISPLAY: list[str] = ["Si succès", "Si échec", "Toujours"]
_CONDITION_VALUES: list[str] = ["success", "failure", "always"]
_CONDITION_MAP: dict[str, str] = dict(zip(_CONDITION_DISPLAY, _CONDITION_VALUES))
_CONDITION_REVERSE: dict[str, str] = dict(zip(_CONDITION_VALUES, _CONDITION_DISPLAY))

# --- END_PROCESS wait_unit display/value mappings ---
_WAIT_UNIT_DISPLAY: list[str] = ["heure", "minute", "seconde", "milliseconde"]
_WAIT_UNIT_VALUES: list[str] = ["h", "m", "s", "ms"]
_WAIT_UNIT_MAP_VIEW_TO_MODEL: dict[str, str] = dict(zip(_WAIT_UNIT_DISPLAY, _WAIT_UNIT_VALUES))
_WAIT_UNIT_MAP_MODEL_TO_VIEW: dict[str, str] = dict(zip(_WAIT_UNIT_VALUES, _WAIT_UNIT_DISPLAY))

# --- COUNT_ELEMENT operator display/value mappings ---
_COUNT_OP_DISPLAY: list[str] = [
    "compris entre",
    "non compris entre",
    "égale à",
    "différent de",
    "supérieur à",
    "inférieur à",
    "supérieur ou égal à",
    "inférieur ou égal à",
]
_COUNT_OP_VALUES: list[str] = [
    "between",
    "not_between",
    "equal",
    "not_equal",
    "greater_than",
    "less_than",
    "greater_or_equal",
    "less_or_equal",
]
_COUNT_OP_MAP: dict[str, str] = dict(zip(_COUNT_OP_DISPLAY, _COUNT_OP_VALUES))
_COUNT_OP_REVERSE: dict[str, str] = dict(zip(_COUNT_OP_VALUES, _COUNT_OP_DISPLAY))

# --- COUNT_ELEMENT success_if display/value mappings ---
_SUCCESS_IF_DISPLAY: list[str] = ["succès", "échec"]
_SUCCESS_IF_VALUES: list[str] = ["success", "failure"]
_SUCCESS_IF_MAP: dict[str, str] = dict(zip(_SUCCESS_IF_DISPLAY, _SUCCESS_IF_VALUES))
_SUCCESS_IF_REVERSE: dict[str, str] = dict(zip(_SUCCESS_IF_VALUES, _SUCCESS_IF_DISPLAY))

# Combined reverse map used by _load_step for display-mapped param keys.
_PARAM_DISPLAY_REVERSE: dict[str, dict[str, str]] = {
    "extract_mode": _EXTRACT_MODE_REVERSE,
    "target": _TARGET_REVERSE,
    "condition": _CONDITION_REVERSE,
    "wait_unit": _WAIT_UNIT_MAP_MODEL_TO_VIEW,
    "timeout_unit": _WAIT_UNIT_MAP_MODEL_TO_VIEW,
}


class StepInlineFormPanel(ttk.LabelFrame):
    """Inline form panel for creating or editing a single scraping step.

    Embedded inside WorkflowBuilderView. Hidden by default.
    After confirmation, on_confirm is fired with the built StepScrapingModel.
    After cancellation, on_cancel is fired so the parent can hide the panel.

    Attributes:
        on_confirm: Callback(StepScrapingModel) fired when step is validated.
        on_cancel: Callback fired when the user cancels without changes.
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the panel and builds all sub-regions.

        Args:
            parent: The parent Tkinter widget to embed into.
        """
        super().__init__(parent, text="Logistique")
        self.on_confirm: Callable[[StepScrapingModel], None] | None = None
        self.on_cancel: Callable[[], None] | None = None
        self.on_type_changed: Callable[[str], None] | None = None
        self._type_var = tk.StringVar()
        self._form_widgets: dict[str, Any] = {}
        self._step_selected: str | None = None
        # Step list for JUMP_TO_STEP target combobox; set via set_available_steps().
        self._available_steps: list[StepScrapingModel] = []
        self._jump_target_displays: list[str] = []
        # Container frame for the COUNT_ELEMENT dynamic value area (rebuilt on operator change).
        self._count_value_area_frame: ttk.Frame | None = None

        # Build all structural regions.
        self._create_widgets()

    # ---------------------------------------------------------------
    # Widget construction
    # ---------------------------------------------------------------

    def _create_widgets(self) -> None:
        """Builds type selector, dynamic form area, error label, and buttons.

        Pack order rule: BOTTOM widgets must be packed before TOP ones so that
        pack reserves their space before the expanding form_frame claims the rest.
        Visual order (top→bottom): type_selector / form_frame / error_label / buttons.
        """
        # --- BOTTOM zone (packed first, innermost = lowest on screen) ---
        self._create_buttons()

        self._error_label = ttk.Label(self, text="", foreground="red")
        self._error_label.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 2))

        # --- TOP zone (packed after, left→right order) ---
        top_area = ttk.Frame(self)
        top_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Right: dynamic form area (type selector is provided externally)
        self._form_frame = ttk.Frame(top_area)
        self._form_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 5), pady=5)

    def _create_type_selector(self) -> None:
        """Deprecated: replaced by left-hand listbox UI."""
        return

    def _create_buttons(self) -> None:
        """Creates the Confirm and Cancel buttons at the bottom."""
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        self._btn_confirm = ttk.Button(btn_frame, text="Confirmer", command=self._confirm)
        self._btn_confirm.pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annuler", command=self._cancel).pack(side=tk.RIGHT, padx=5)

    # ---------------------------------------------------------------
    # Public interface
    # ---------------------------------------------------------------

    def set_available_steps(self, steps: list[StepScrapingModel]) -> None:
        """Stores the workflow step list for JUMP_TO_STEP target population.

        Must be called before load() when the user may select JUMP_TO_STEP.

        Args:
            steps: Current ordered workflow step list.
        """
        self._available_steps = list(steps)

    def load(self, step: StepScrapingModel | None = None) -> None:
        """Prepares the form for a new step or pre-fills it from an existing one.

        Args:
            step: Existing step to pre-fill, or None to show a blank form.
        """
        # Select initial step type and rebuild the form.
        initial_type = step.step_type if step else StepType.OPEN_URL
        label = STEP_TYPE_LABELS[initial_type]
        self._type_var.set(label)
        self._rebuild_form(initial_type)

        # Track editing state and update confirm button label
        self._step_selected = step if step else None
        if hasattr(self, "_btn_confirm") and self._btn_confirm:
            if step is None:
                self._btn_confirm.config(text="Ajouter l'étape")
            else:
                self._btn_confirm.config(text="Mettre à jour")

        # Pre-fill widget values when editing an existing step.
        if step:
            self._load_step(step)

        # Notify the parent so the help panel reflects the current type.
        if self.on_type_changed:
            self.on_type_changed(label)

    # ---------------------------------------------------------------
    # Dynamic form management
    # ---------------------------------------------------------------

    def _on_type_changed(self, event: tk.Event) -> None:
        """Rebuilds the form area when the type selector changes."""
        label = self._type_var.get()
        step_type = _LABEL_TO_TYPE.get(label)
        if step_type is not None:
            self._rebuild_form(step_type)
        # Notify the parent so it can update the help panel.
        if self.on_type_changed and label:
            self.on_type_changed(label)

    # Note: listbox selection handler removed; external combobox is used instead.

    def _rebuild_form(self, step_type: StepType) -> None:
        """Clears and rebuilds the dynamic form for the given step type."""
        # Destroy previous form widgets and reset type-specific state.
        for widget in self._form_frame.winfo_children():
            widget.destroy()
        self._form_widgets.clear()
        self._error_label.configure(text="")
        self._count_value_area_frame = None

        # Dispatch to the matching form builder.
        builders = {
            StepType.OPEN_URL: self._build_form_open_url,
            StepType.REFRESH_PAGE: self._build_form_refresh_page,
            StepType.SLEEP: self._build_form_sleep,
            StepType.RANDOM_PAUSE: self._build_form_random_pause,
            StepType.DOWNLOAD_IMAGE: self._build_form_download_image,
            StepType.WAIT_IMAGE_SIZE: self._build_form_wait_image_size,
            StepType.WAIT_ELEMENT: self._build_form_wait_element,
            StepType.COUNT_ELEMENT: self._build_form_count_element,
            StepType.CLICK_ELEMENT: self._build_form_click_element,
            StepType.SCROLL_DOWN: self._build_form_scroll_down,
            StepType.EXTRACT_TEXT: self._build_form_extract_text,
            StepType.JUMP_TO_STEP: self._build_form_jump_to_step,
            StepType.CLOSE_TABS: self._build_form_close_tabs,
            StepType.END_PROCESS: self._build_form_end_process,
        }
        builder = builders.get(step_type)
        if builder:
            builder()

    # ---------------------------------------------------------------
    # Per-type form builders
    # ---------------------------------------------------------------

    def _build_form_open_url(self) -> None:
        """Builds the OPEN_URL form (URL field + wait_state combobox + timeout row)."""
        self._form_frame.columnconfigure(1, weight=1)
        ttk.Label(self._form_frame, text="URL:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        url_var = tk.StringVar(value="https://example.com/")
        ttk.Entry(self._form_frame, textvariable=url_var).grid(row=0, column=1, sticky="ew", padx=5, pady=4)
        self._form_widgets["url"] = url_var

        # Wait state selector.
        ttk.Label(self._form_frame, text="État d'attente:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        ws_var = tk.StringVar(value="domcontentloaded")
        ttk.Combobox(self._form_frame, textvariable=ws_var, values=_WAIT_STATES, state="readonly").grid(
            row=1, column=1, sticky="ew", padx=5, pady=4
        )
        self._form_widgets["wait_state"] = ws_var

        # Timeout row — single horizontal line: label | spinbox | combobox | hint.
        timeout_frame = ttk.Frame(self._form_frame)
        timeout_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=4)
        ttk.Label(timeout_frame, text="Timeout").pack(side=tk.LEFT, padx=(0, 4))
        td_var = tk.StringVar(value="0")
        ttk.Spinbox(timeout_frame, from_=0, to=99999, textvariable=td_var, width=7).pack(side=tk.LEFT, padx=(0, 4))
        tu_var = tk.StringVar(value=_WAIT_UNIT_DISPLAY[2])
        ttk.Combobox(
            timeout_frame, textvariable=tu_var, values=_WAIT_UNIT_DISPLAY, state="readonly", width=10
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(timeout_frame, text="(0 = désactivé)", foreground="gray").pack(side=tk.LEFT)
        self._form_widgets["timeout_duration"] = td_var
        self._form_widgets["timeout_unit"] = tu_var

    def _build_form_sleep(self) -> None:
        """Builds the SLEEP form (duration spinbox + unit combobox)."""
        self._form_frame.columnconfigure(1, weight=1)
        ttk.Label(self._form_frame, text="Durée:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        dur_var = tk.StringVar(value="0")
        ttk.Spinbox(self._form_frame, from_=0, to=9999, textvariable=dur_var, width=10).grid(
            row=0, column=1, sticky="w", padx=5, pady=4
        )
        self._form_widgets["duration"] = dur_var

        ttk.Label(self._form_frame, text="Unité:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        unit_var = tk.StringVar(value="seconde")
        ttk.Combobox(self._form_frame, textvariable=unit_var, values=_UNITS, state="readonly").grid(
            row=1, column=1, sticky="ew", padx=5, pady=4
        )
        self._form_widgets["unit"] = unit_var

    def _build_form_random_pause(self) -> None:
        """Builds the RANDOM_PAUSE form (min, max spinboxes + unit combobox)."""
        # ligne 1
        line1 = ttk.Frame(self._form_frame)
        line1.pack(fill="x", anchor="w", pady=2)

        ttk.Label(line1, text="Attendre aléatoirement entre : ").pack(side=tk.LEFT, padx=(0, 6))

        min_var = tk.StringVar(value="0")
        ttk.Spinbox(line1, from_=0, to=9999, textvariable=min_var, width=10).pack(side=tk.LEFT, padx=(0, 6))
        self._form_widgets["min"] = min_var

        ttk.Label(line1, text=" et ").pack(side=tk.LEFT, padx=(0, 6))

        max_var = tk.StringVar(value="1")
        ttk.Spinbox(line1, from_=0, to=9999, textvariable=max_var, width=10).pack(side=tk.LEFT, padx=(0, 6))
        self._form_widgets["max"] = max_var

        # ligne 2
        line2 = ttk.Frame(self._form_frame)
        line2.pack(fill="x", anchor="w", pady=2)

        ttk.Label(line2, text="Unité:").pack(side=tk.LEFT, padx=(0, 6))

        unit_var = tk.StringVar(value="seconde")
        ttk.Combobox(line2, textvariable=unit_var, values=_UNITS, state="readonly").pack(side=tk.LEFT, padx=(0, 6))
        self._form_widgets["unit"] = unit_var

    def _build_form_refresh_page(self) -> None:
        """Builds the REFRESH_PAGE form (clear_cache checkbox)."""
        cache_var = tk.BooleanVar(value=False)
        CanvasCheckbox(self._form_frame, text="Vider le cache", variable=cache_var).grid(
            row=0, column=0, sticky="w", padx=5, pady=4
        )
        self._form_widgets["clear_cache"] = cache_var

    def _build_form_download_image(self) -> None:
        """Builds the DOWNLOAD_IMAGE form (mode + 4 dimension spinboxes)."""
        self._form_frame.columnconfigure(2, weight=1)
        ttk.Label(self._form_frame, text="Mode:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        mode_var = tk.StringVar(value="largest")
        ttk.Combobox(self._form_frame, textvariable=mode_var, values=_DOWNLOAD_MODES, state="readonly").grid(
            row=0, column=1, columnspan=4, sticky="ew", padx=5, pady=4
        )
        self._form_widgets["mode"] = mode_var

        # Height and width dimension rows share the same helper.
        self._add_dimension_row(1, "Hauteur (px):", "height_min", "height_max", 0, 99999)
        self._add_dimension_row(2, "Largeur (px):", "width_min", "width_max", 0, 99999)

    def _build_form_wait_image_size(self) -> None:
        """Builds the WAIT_IMAGE_SIZE form (4 dimension spinboxes + timeout row)."""
        self._add_dimension_row(0, "Hauteur (px):", "height_min", "height_max", 0, 99999)
        self._add_dimension_row(1, "Largeur (px):", "width_min", "width_max", 0, 99999)

        # Timeout row — single horizontal line: label | spinbox | combobox | hint.
        timeout_frame = ttk.Frame(self._form_frame)
        timeout_frame.grid(row=2, column=0, columnspan=5, sticky="w", padx=5, pady=4)
        ttk.Label(timeout_frame, text="Timeout").pack(side=tk.LEFT, padx=(0, 4))
        td_var = tk.StringVar(value="0")
        ttk.Spinbox(timeout_frame, from_=0, to=99999, textvariable=td_var, width=7).pack(side=tk.LEFT, padx=(0, 4))
        tu_var = tk.StringVar(value=_WAIT_UNIT_DISPLAY[2])
        ttk.Combobox(
            timeout_frame, textvariable=tu_var, values=_WAIT_UNIT_DISPLAY, state="readonly", width=10
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(timeout_frame, text="(0 = désactivé)", foreground="gray").pack(side=tk.LEFT)
        self._form_widgets["timeout_duration"] = td_var
        self._form_widgets["timeout_unit"] = tu_var

    def _build_form_click_element(self) -> None:
        """Builds the CLICK_ELEMENT form (CSS selector + click_mode combobox)."""
        self._form_frame.columnconfigure(1, weight=1)
        ttk.Label(self._form_frame, text="Sélecteur CSS:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        sel_var = tk.StringVar()
        ttk.Entry(self._form_frame, textvariable=sel_var).grid(row=0, column=1, sticky="ew", padx=5, pady=4)
        self._form_widgets["selector"] = sel_var

        ttk.Label(self._form_frame, text="Mode de clic:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        mode_var = tk.StringVar(value="Normal")
        ttk.Combobox(self._form_frame, textvariable=mode_var, values=_CLICK_MODES, state="readonly").grid(
            row=1, column=1, sticky="ew", padx=5, pady=4
        )
        self._form_widgets["click_mode"] = mode_var

    def _build_form_wait_element(self) -> None:
        """Builds the WAIT_ELEMENT form (CSS selector entry + timeout row)."""
        self._form_frame.columnconfigure(1, weight=1)
        ttk.Label(self._form_frame, text="Sélecteur CSS:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        sel_var = tk.StringVar()
        ttk.Entry(self._form_frame, textvariable=sel_var).grid(row=0, column=1, sticky="ew", padx=5, pady=4)
        self._form_widgets["selector"] = sel_var

        # Timeout row — single horizontal line: label | spinbox | combobox | hint.
        timeout_frame = ttk.Frame(self._form_frame)
        timeout_frame.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=4)
        ttk.Label(timeout_frame, text="Timeout").pack(side=tk.LEFT, padx=(0, 4))
        td_var = tk.StringVar(value="0")
        ttk.Spinbox(timeout_frame, from_=0, to=99999, textvariable=td_var, width=7).pack(side=tk.LEFT, padx=(0, 4))
        tu_var = tk.StringVar(value=_WAIT_UNIT_DISPLAY[2])
        ttk.Combobox(
            timeout_frame, textvariable=tu_var, values=_WAIT_UNIT_DISPLAY, state="readonly", width=10
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(timeout_frame, text="(0 = désactivé)", foreground="gray").pack(side=tk.LEFT)
        self._form_widgets["timeout_duration"] = td_var
        self._form_widgets["timeout_unit"] = tu_var

    def _build_form_count_element(self) -> None:
        """Builds the COUNT_ELEMENT form (selector, pre-wait, condition, operator rows)."""
        self._form_frame.columnconfigure(1, weight=1)

        # Row 0 — pre-wait: label | spinbox | unit combobox | hint.
        wait_frame = ttk.Frame(self._form_frame)
        wait_frame.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=4)
        ttk.Label(wait_frame, text="Attendre ").pack(side=tk.LEFT, padx=(0, 4))
        wd_var = tk.StringVar(value="0")
        ttk.Spinbox(wait_frame, from_=0, to=99999, textvariable=wd_var, width=7).pack(side=tk.LEFT, padx=(0, 4))
        wu_var = tk.StringVar(value=_WAIT_UNIT_DISPLAY[2])
        ttk.Combobox(wait_frame, textvariable=wu_var, values=_WAIT_UNIT_DISPLAY, state="readonly", width=10).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Label(wait_frame, text=" avant de lancer l'évaluation(0 = immédiat)").pack(side=tk.LEFT)
        self._form_widgets["wait_duration"] = wd_var
        self._form_widgets["wait_unit"] = wu_var

        # Row 1 — CSS selector entry.
        ttk.Label(self._form_frame, text="Sélecteur CSS:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        sel_var = tk.StringVar()
        ttk.Entry(self._form_frame, textvariable=sel_var).grid(row=1, column=1, sticky="ew", padx=5, pady=4)
        self._form_widgets["selector"] = sel_var

        # Row 2 — success_if: "C'est un" | combobox | "si COUNT est".
        result_frame = ttk.Frame(self._form_frame)
        result_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=4)
        ttk.Label(result_frame, text="Est un").pack(side=tk.LEFT, padx=(0, 4))
        si_var = tk.StringVar(value=_SUCCESS_IF_DISPLAY[0])
        si_cb = ttk.Combobox(
            result_frame, textvariable=si_var, values=_SUCCESS_IF_DISPLAY, state="readonly", width=8
        )
        si_cb.pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(result_frame, text="si le résultat est ").pack(side=tk.LEFT, padx=(4, 0))
        self._form_widgets["success_if"] = si_var

        # Operator combobox defaults to "égale à".
        op_var = tk.StringVar(value=_COUNT_OP_DISPLAY[2])
        op_cb = ttk.Combobox(
            result_frame, textvariable=op_var, values=_COUNT_OP_DISPLAY, state="readonly", width=18
        )
        op_cb.pack(side=tk.LEFT, padx=(0, 6))
        self._form_widgets["operator"] = op_var

        # Value area: rebuilt dynamically when operator changes.
        self._count_value_area_frame = ttk.Frame(result_frame)
        self._count_value_area_frame.pack(side=tk.LEFT)
        self._rebuild_count_value_area(_COUNT_OP_DISPLAY[2])
        op_cb.bind("<<ComboboxSelected>>", lambda _: self._rebuild_count_value_area(op_var.get()))

    def _rebuild_count_value_area(self, op_display: str) -> None:
        """Rebuilds the value spinbox(es) in the COUNT_ELEMENT value area frame.

        Shows two spinboxes (min/max) for range operators, one spinbox otherwise.

        Args:
            op_display: French display label of the currently selected operator.
        """
        if self._count_value_area_frame is None:
            return

        # Clear previous value widgets and form_widget entries for values.
        for widget in self._count_value_area_frame.winfo_children():
            widget.destroy()
        for key in ("value", "value_min", "value_max"):
            self._form_widgets.pop(key, None)

        op_value = _COUNT_OP_MAP.get(op_display, "equal")

        # Range operators require min and max spinboxes.
        if op_value in {"between", "not_between"}:
            ttk.Label(self._count_value_area_frame, text="min").pack(side=tk.LEFT, padx=(0, 2))
            vmin_var = tk.StringVar(value="0")
            ttk.Spinbox(self._count_value_area_frame, from_=0, to=99999, textvariable=vmin_var, width=7).pack(
                side=tk.LEFT, padx=(0, 6)
            )
            ttk.Label(self._count_value_area_frame, text="max").pack(side=tk.LEFT, padx=(0, 2))
            vmax_var = tk.StringVar(value="0")
            ttk.Spinbox(self._count_value_area_frame, from_=0, to=99999, textvariable=vmax_var, width=7).pack(
                side=tk.LEFT
            )
            self._form_widgets["value_min"] = vmin_var
            self._form_widgets["value_max"] = vmax_var
            return

        # Single-value operators require one spinbox.
        ttk.Label(self._count_value_area_frame, text="valeur").pack(side=tk.LEFT, padx=(0, 2))
        val_var = tk.StringVar(value="0")
        ttk.Spinbox(self._count_value_area_frame, from_=0, to=99999, textvariable=val_var, width=7).pack(
            side=tk.LEFT
        )
        self._form_widgets["value"] = val_var

    def _build_form_scroll_down(self) -> None:
        """Builds the SCROLL_DOWN form (pixel count spinbox)."""
        self._form_frame.columnconfigure(1, weight=1)
        ttk.Label(self._form_frame, text="Pixels:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        px_var = tk.StringVar(value="1000")
        ttk.Spinbox(self._form_frame, from_=0, to=99999, textvariable=px_var, width=10).grid(
            row=0, column=1, sticky="w", padx=5, pady=4
        )
        self._form_widgets["pixels"] = px_var

    def _build_form_close_tabs(self) -> None:
        """Builds the CLOSE_TABS form (url_filter entry + max_tabs spinbox)."""
        self._form_frame.columnconfigure(1, weight=1)

        # Optional URL substring filter field.
        ttk.Label(self._form_frame, text="Filtre URL:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        filter_var = tk.StringVar()
        ttk.Entry(self._form_frame, textvariable=filter_var).grid(row=0, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(self._form_frame, text="Laisser vide pour ne pas filtrer", foreground="gray").grid(
            row=1, column=1, sticky="w", padx=5
        )
        self._form_widgets["url_filter"] = filter_var

        # Maximum tabs to keep open.
        ttk.Label(self._form_frame, text="Max onglets:").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        tabs_var = tk.StringVar(value="0")
        ttk.Spinbox(self._form_frame, from_=0, to=9999, textvariable=tabs_var, width=10).grid(
            row=2, column=1, sticky="w", padx=5, pady=4
        )
        self._form_widgets["max_tabs"] = tabs_var

    def _build_form_extract_text(self) -> None:
        """Builds the EXTRACT_TEXT form (selector, extract_mode, target comboboxes)."""
        self._form_frame.columnconfigure(1, weight=1)

        # CSS selector entry.
        ttk.Label(self._form_frame, text="Sélecteur CSS:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        sel_var = tk.StringVar()
        ttk.Entry(self._form_frame, textvariable=sel_var).grid(row=0, column=1, sticky="ew", padx=5, pady=4)
        self._form_widgets["selector"] = sel_var

        # Extraction mode combobox.
        ttk.Label(self._form_frame, text="Mode d'extraction:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        mode_var = tk.StringVar(value=_EXTRACT_MODE_DISPLAY[0])
        ttk.Combobox(self._form_frame, textvariable=mode_var, values=_EXTRACT_MODE_DISPLAY, state="readonly").grid(
            row=1, column=1, sticky="ew", padx=5, pady=4
        )
        self._form_widgets["extract_mode"] = mode_var

        # Target elements combobox.
        ttk.Label(self._form_frame, text="Éléments ciblés:").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        target_var = tk.StringVar(value=_TARGET_DISPLAY[0])
        ttk.Combobox(self._form_frame, textvariable=target_var, values=_TARGET_DISPLAY, state="readonly").grid(
            row=2, column=1, sticky="ew", padx=5, pady=4
        )
        self._form_widgets["target"] = target_var

    def _build_form_jump_to_step(self) -> None:
        """Builds the JUMP_TO_STEP form (condition + dynamic target step combobox)."""
        self._form_frame.columnconfigure(1, weight=1)

        # Condition selector.
        ttk.Label(self._form_frame, text="Condition:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        cond_var = tk.StringVar(value=_CONDITION_DISPLAY[0])
        ttk.Combobox(self._form_frame, textvariable=cond_var, values=_CONDITION_DISPLAY, state="readonly").grid(
            row=0, column=1, sticky="ew", padx=5, pady=4
        )
        self._form_widgets["condition"] = cond_var

        # Build display strings from the available steps list.
        self._jump_target_displays = [
            f"Étape {i + 1} — {STEP_TYPE_LABELS.get(s.step_type, s.step_type.value)}"
            for i, s in enumerate(self._available_steps)
        ]
        default_target = self._jump_target_displays[0] if self._jump_target_displays else ""
        target_var = tk.StringVar(value=default_target)
        ttk.Label(self._form_frame, text="Étape cible:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        ttk.Combobox(
            self._form_frame,
            textvariable=target_var,
            values=self._jump_target_displays,
            state="readonly",
        ).grid(row=1, column=1, sticky="ew", padx=5, pady=4)
        self._form_widgets["target_index"] = target_var

    def _build_form_end_process(self) -> None:
        """Builds the END_PROCESS form (wait_duration spinbox + wait_unit combobox)."""
        self._form_frame.columnconfigure(1, weight=1)

        # Duration spinbox.
        ttk.Label(self._form_frame, text="Durée d'attente:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        dur_var = tk.StringVar(value="0")
        ttk.Spinbox(self._form_frame, from_=0, to=99999, textvariable=dur_var, width=10).grid(
            row=0, column=1, sticky="w", padx=5, pady=4
        )
        self._form_widgets["wait_duration"] = dur_var

        # Unit combobox — default "seconde" maps to internal "second".
        ttk.Label(self._form_frame, text="Unité:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        unit_var = tk.StringVar(value=_WAIT_UNIT_DISPLAY[2])
        ttk.Combobox(self._form_frame, textvariable=unit_var, values=_WAIT_UNIT_DISPLAY, state="readonly").grid(
            row=1, column=1, sticky="ew", padx=5, pady=4
        )
        self._form_widgets["wait_unit"] = unit_var

    # ---------------------------------------------------------------
    # Shared form helpers
    # ---------------------------------------------------------------

    def _add_dimension_row(
        self,
        row: int,
        label: str,
        min_key: str,
        max_key: str,
        default_min: int,
        default_max: int,
    ) -> None:
        """Adds a labeled Min/Max spinbox pair to the form grid.

        Args:
            row: Grid row index to place the widgets.
            label: Row header text (e.g. "Hauteur (px):").
            min_key: Form widget key for the minimum value.
            max_key: Form widget key for the maximum value.
            default_min: Default value for the minimum spinbox.
            default_max: Default value for the maximum spinbox.
        """
        ttk.Label(self._form_frame, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=4)
        ttk.Label(self._form_frame, text="Min:").grid(row=row, column=1, sticky="w", padx=2)
        min_var = tk.StringVar(value=str(default_min))
        ttk.Spinbox(self._form_frame, from_=0, to=99999, textvariable=min_var, width=8).grid(
            row=row, column=2, padx=5, pady=4
        )

        ttk.Label(self._form_frame, text="Max:").grid(row=row, column=3, sticky="w", padx=2)
        max_var = tk.StringVar(value=str(default_max))
        ttk.Spinbox(self._form_frame, from_=0, to=99999, textvariable=max_var, width=8).grid(
            row=row, column=4, padx=5, pady=4
        )

        self._form_widgets[min_key] = min_var
        self._form_widgets[max_key] = max_var

    # ---------------------------------------------------------------
    # Pre-fill and read-back
    # ---------------------------------------------------------------

    def _load_step(self, step: StepScrapingModel) -> None:
        """Pre-fills form widgets from an existing step's params.

        Applies display reverse-maps for keys whose combobox shows translated
        labels (extract_mode, target, condition, wait_unit). Handles
        target_index via the dynamic jump target display list. COUNT_ELEMENT
        uses a dedicated loader so that operator is applied before value fields.

        Args:
            step: The step whose params will populate the form.
        """
        # COUNT_ELEMENT needs ordered loading: operator must precede value fields.
        if step.step_type == StepType.COUNT_ELEMENT:
            self._load_count_element_step(step.params)
            return

        for key, value in step.params.items():
            if key not in self._form_widgets:
                continue
            widget_var = self._form_widgets[key]

            # JUMP_TO_STEP target_index maps int → display string.
            if key == "target_index":
                idx = int(value) if str(value).lstrip("-").isdigit() else 0
                if 0 <= idx < len(self._jump_target_displays):
                    widget_var.set(self._jump_target_displays[idx])
                continue

            if isinstance(widget_var, tk.BooleanVar):
                widget_var.set(bool(value))
            else:
                # Use display reverse-map when available, fall back to raw string.
                display = _PARAM_DISPLAY_REVERSE.get(key, {}).get(str(value), str(value))
                widget_var.set(display)

    def _load_count_element_step(self, params: dict[str, Any]) -> None:
        """Pre-fills COUNT_ELEMENT form widgets in the required order.

        Operator must be applied before value fields so that _rebuild_count_value_area
        creates the correct spinboxes before their values are written.

        Args:
            params: COUNT_ELEMENT step params dict.
        """
        # Set plain text and unit fields.
        if "selector" in self._form_widgets:
            self._form_widgets["selector"].set(params.get("selector", ""))
        if "wait_duration" in self._form_widgets:
            self._form_widgets["wait_duration"].set(str(params.get("wait_duration", 0)))
        if "wait_unit" in self._form_widgets:
            unit_display = _WAIT_UNIT_MAP_MODEL_TO_VIEW.get(params.get("wait_unit", "s"), "seconde")
            self._form_widgets["wait_unit"].set(unit_display)
        if "success_if" in self._form_widgets:
            si_display = _SUCCESS_IF_REVERSE.get(params.get("success_if", "success"), "succès")
            self._form_widgets["success_if"].set(si_display)

        # Set operator and rebuild the value area before writing value fields.
        op_display = _COUNT_OP_REVERSE.get(params.get("operator", "equal"), "égale à")
        if "operator" in self._form_widgets:
            self._form_widgets["operator"].set(op_display)
        self._rebuild_count_value_area(op_display)

        # Write value fields (widgets now exist after the rebuild above).
        if "value_min" in self._form_widgets:
            self._form_widgets["value_min"].set(str(params.get("value_min", 0)))
        if "value_max" in self._form_widgets:
            self._form_widgets["value_max"].set(str(params.get("value_max", 0)))
        if "value" in self._form_widgets:
            self._form_widgets["value"].set(str(params.get("value", 0)))

    def _get_params(self, step_type: StepType) -> dict[str, Any]:
        """Reads form widget values and returns the params dict for the step.

        Args:
            step_type: Used to select the correct param reader.

        Returns:
            A dictionary of typed parameter values.
        """
        readers = {
            StepType.OPEN_URL: self._params_open_url,
            StepType.REFRESH_PAGE: self._params_refresh_page,
            StepType.SLEEP: self._params_sleep,
            StepType.RANDOM_PAUSE: self._params_random_pause,
            StepType.DOWNLOAD_IMAGE: self._params_download_image,
            StepType.WAIT_IMAGE_SIZE: self._params_wait_image_size,
            StepType.WAIT_ELEMENT: self._params_wait_element,
            StepType.COUNT_ELEMENT: self._params_count_element,
            StepType.CLICK_ELEMENT: self._params_click_element,
            StepType.SCROLL_DOWN: self._params_scroll_down,
            StepType.EXTRACT_TEXT: self._params_extract_text,
            StepType.JUMP_TO_STEP: self._params_jump_to_step,
            StepType.CLOSE_TABS: self._params_close_tabs,
            StepType.END_PROCESS: self._params_end_process,
        }
        reader = readers.get(step_type)
        return reader() if reader else {}

    # ---------------------------------------------------------------
    # Per-type param readers
    # ---------------------------------------------------------------

    def _params_open_url(self) -> dict[str, Any]:
        """Reads OPEN_URL params from form widgets."""
        unit_display = self._form_widgets["timeout_unit"].get()
        return {
            "url": self._form_widgets["url"].get().strip(),
            "wait_state": self._form_widgets["wait_state"].get(),
            "timeout_duration": self._safe_int("timeout_duration", C_CONSTANT_INVALID_INT),
            "timeout_unit": _WAIT_UNIT_MAP_VIEW_TO_MODEL.get(unit_display, "s"),
        }

    def _params_sleep(self) -> dict[str, Any]:
        """Reads SLEEP params, coercing duration to float."""
        return {
            "duration": self._safe_int("duration", 0),
            "unit": self._form_widgets["unit"].get(),
        }

    def _params_random_pause(self) -> dict[str, Any]:
        """Reads RANDOM_PAUSE params, coercing min/max to float."""
        return {
            "min": self._safe_int("min", 0),
            "max": self._safe_int("max", 1),
            "unit": self._form_widgets["unit"].get(),
        }

    def _params_refresh_page(self) -> dict[str, Any]:
        """Reads REFRESH_PAGE params."""
        return {"clear_cache": bool(self._form_widgets["clear_cache"].get())}

    def _params_download_image(self) -> dict[str, Any]:
        """Reads DOWNLOAD_IMAGE params, coercing dimensions to int."""
        return {
            "mode": self._form_widgets["mode"].get(),
            "height_min": self._safe_int("height_min", 0),
            "height_max": self._safe_int("height_max", 99999),
            "width_min": self._safe_int("width_min", 0),
            "width_max": self._safe_int("width_max", 99999),
        }

    def _params_wait_image_size(self) -> dict[str, Any]:
        """Reads WAIT_IMAGE_SIZE params, coercing dimensions to int."""
        unit_display = self._form_widgets["timeout_unit"].get()
        return {
            "height_min": self._safe_int("height_min", 0),
            "height_max": self._safe_int("height_max", 99999),
            "width_min": self._safe_int("width_min", 0),
            "width_max": self._safe_int("width_max", 99999),
            "timeout_duration": self._safe_int("timeout_duration", 0),
            "timeout_unit": _WAIT_UNIT_MAP_VIEW_TO_MODEL.get(unit_display, "s"),
        }

    def _params_click_element(self) -> dict[str, Any]:
        """Reads CLICK_ELEMENT params."""
        return {
            "selector": self._form_widgets["selector"].get().strip(),
            "click_mode": self._form_widgets["click_mode"].get(),
        }

    def _params_wait_element(self) -> dict[str, Any]:
        """Reads WAIT_ELEMENT params."""
        unit_display = self._form_widgets["timeout_unit"].get()
        return {
            "selector": self._form_widgets["selector"].get().strip(),
            "timeout_duration": self._safe_int("timeout_duration", 0),
            "timeout_unit": _WAIT_UNIT_MAP_VIEW_TO_MODEL.get(unit_display, "s"),
        }

    def _params_count_element(self) -> dict[str, Any]:
        """Reads COUNT_ELEMENT params, translating display labels to internal values."""
        unit_display = self._form_widgets["wait_unit"].get()
        si_display = self._form_widgets["success_if"].get()
        op_display = self._form_widgets["operator"].get()
        op_value = _COUNT_OP_MAP.get(op_display, "equal")

        # Build base params shared by all operators.
        params: dict[str, Any] = {
            "selector": self._form_widgets["selector"].get().strip(),
            "wait_duration": self._safe_int("wait_duration", 0),
            "wait_unit": _WAIT_UNIT_MAP_VIEW_TO_MODEL.get(unit_display, "s"),
            "success_if": _SUCCESS_IF_MAP.get(si_display, "success"),
            "operator": op_value,
        }

        # Add range or single-value fields based on the active operator.
        if op_value in {"between", "not_between"}:
            params["value_min"] = self._safe_int("value_min", 0)
            params["value_max"] = self._safe_int("value_max", 0)
            params["value"] = 0
        else:
            params["value_min"] = 0
            params["value_max"] = 0
            params["value"] = self._safe_int("value", 0)
        return params

    def _params_scroll_down(self) -> dict[str, Any]:
        """Reads SCROLL_DOWN params, coercing pixels to int."""
        return {"pixels": self._safe_int("pixels", 1000)}

    def _params_close_tabs(self) -> dict[str, Any]:
        """Reads CLOSE_TABS params."""
        return {
            "url_filter": self._form_widgets["url_filter"].get().strip(),
            "max_tabs": self._safe_int("max_tabs", 0),
        }

    def _params_extract_text(self) -> dict[str, Any]:
        """Reads EXTRACT_TEXT params, translating display labels to internal values."""
        mode_display = self._form_widgets["extract_mode"].get()
        target_display = self._form_widgets["target"].get()
        return {
            "selector": self._form_widgets["selector"].get().strip(),
            "extract_mode": _EXTRACT_MODE_MAP.get(mode_display, "innerText"),
            "target": _TARGET_MAP.get(target_display, "first"),
        }

    def _params_jump_to_step(self) -> dict[str, Any]:
        """Reads JUMP_TO_STEP params, resolving display labels to internal values."""
        condition_display = self._form_widgets["condition"].get()
        condition = _CONDITION_MAP.get(condition_display, "success")

        # Derive zero-based index from the selected display string.
        target_display = self._form_widgets["target_index"].get()
        if target_display in self._jump_target_displays:
            target_idx = self._jump_target_displays.index(target_display)
        else:
            target_idx = 0
        return {"condition": condition, "target_index": target_idx}

    def _params_end_process(self) -> dict[str, Any]:
        """Reads END_PROCESS params, translating display unit label to internal value."""
        unit_display = self._form_widgets["wait_unit"].get()
        return {
            "wait_duration": self._safe_int("wait_duration", 0),
            "wait_unit": _WAIT_UNIT_MAP_VIEW_TO_MODEL.get(unit_display, "s"),
        }

    # ---------------------------------------------------------------
    # Type-safe widget reads
    # ---------------------------------------------------------------

    def _safe_int(self, key: str, default: int) -> int:
        """Reads an int from a StringVar form widget.

        Args:
            key: Form widget key.
            default: Fallback value when conversion fails.

        Returns:
            Integer value, or default on failure.
        """
        try:
            return int(self._form_widgets[key].get())
        except (ValueError, KeyError):
            return default

    # ---------------------------------------------------------------
    # Validation (mirrors service layer rules)
    # ---------------------------------------------------------------

    def _validate_form(self, step_type: StepType) -> list[str]:
        """Validates the current form for the given step type.

        Args:
            step_type: The currently selected step type.

        Returns:
            A list of error messages; empty if valid.
        """
        validators = {
            StepType.OPEN_URL: self._validate_open_url_form,
            StepType.REFRESH_PAGE: list,
            StepType.SLEEP: self._validate_sleep_form,
            StepType.RANDOM_PAUSE: self._validate_random_pause_form,
            StepType.DOWNLOAD_IMAGE: self._validate_download_image_form,
            StepType.WAIT_IMAGE_SIZE: self._validate_wait_image_size_form,
            StepType.WAIT_ELEMENT: self._validate_wait_element_form,
            StepType.COUNT_ELEMENT: self._validate_count_element_form,
            StepType.CLICK_ELEMENT: self._validate_click_element_form,
            StepType.SCROLL_DOWN: list,
            StepType.EXTRACT_TEXT: self._validate_extract_text_form,
            StepType.JUMP_TO_STEP: self._validate_jump_to_step_form,
            StepType.CLOSE_TABS: self._validate_close_tabs_form,
            StepType.END_PROCESS: list,
        }
        validator = validators.get(step_type)
        return validator() if validator else []

    def _validate_open_url_form(self) -> list[str]:
        """Validates OPEN_URL fields."""
        errors: list[str] = []
        if not self._form_widgets.get("url", tk.StringVar()).get().strip():
            errors.append("L'URL est obligatoire.")
        if self._form_widgets.get("timeout_unit", tk.StringVar()).get() not in _WAIT_UNIT_DISPLAY:
            errors.append("Unité de timeout invalide.")
        if self._safe_int("timeout_duration", -1) < 0:
            errors.append("Durée de timeout doit être un nombre positif.")
        return errors

    def _validate_sleep_form(self) -> list[str]:
        """Validates SLEEP fields."""
        try:
            float(self._form_widgets["duration"].get())
            return []
        except (ValueError, KeyError):
            return ["La durée doit être un nombre."]

    def _validate_random_pause_form(self) -> list[str]:
        """Validates RANDOM_PAUSE fields including min < max."""
        errors: list[str] = []
        try:
            min_val = float(self._form_widgets["min"].get())
            max_val = float(self._form_widgets["max"].get())
            if min_val >= max_val:
                errors.append("min doit être strictement inférieur à max.")
        except (ValueError, KeyError):
            errors.append("min et max doivent être des nombres.")
        return errors

    def _validate_download_image_form(self) -> list[str]:
        """Validates DOWNLOAD_IMAGE dimension fields."""
        errors: list[str] = []
        for key in ("height_min", "height_max", "width_min", "width_max"):
            try:
                int(self._form_widgets[key].get())
            except (ValueError, KeyError):
                errors.append(f"{key} doit être un entier.")
        return errors

    def _validate_wait_image_size_form(self) -> list[str]:
        """Validates WAIT_IMAGE_SIZE dimension fields."""
        errors: list[str] = []
        for key in ("height_min", "height_max", "width_min", "width_max"):
            try:
                int(self._form_widgets[key].get())
            except (ValueError, KeyError):
                errors.append(f"{key} doit être un entier.")
        if self._form_widgets.get("timeout_unit", tk.StringVar()).get() not in _WAIT_UNIT_DISPLAY:
            errors.append("Unité de timeout invalide.")
        if self._safe_int("timeout_duration", -1) < 0:
            errors.append("Durée de timeout doit être un nombre positif.")
        return errors

    def _validate_click_element_form(self) -> list[str]:
        """Validates CLICK_ELEMENT fields."""
        if not self._form_widgets.get("selector", tk.StringVar()).get().strip():
            return ["Le sélecteur CSS est obligatoire."]
        return []

    def _validate_wait_element_form(self) -> list[str]:
        """Validates WAIT_ELEMENT fields."""
        errors: list[str] = []
        if not self._form_widgets.get("selector", tk.StringVar()).get().strip():
            errors.append("Le sélecteur CSS est obligatoire.")
        if self._form_widgets.get("timeout_unit", tk.StringVar()).get() not in _WAIT_UNIT_DISPLAY:
            errors.append("Unité de timeout invalide.")
        if self._safe_int("timeout_duration", -1) < 0:
            errors.append("Durée de timeout doit être un nombre positif.")
        return errors

    def _validate_count_element_form(self) -> list[str]:
        """Validates COUNT_ELEMENT fields."""
        errors: list[str] = []

        # Validate wait before
        if self._safe_int("wait_duration", C_CONSTANT_INVALID_INT) == C_CONSTANT_INVALID_INT:
            errors.append("Durée d'attente doit être un nombre positif ou égal à 0.")

        # Selector is mandatory.
        if not self._form_widgets.get("selector", tk.StringVar()).get().strip():
            errors.append("Le sélecteur CSS est obligatoire.")

        # Range operators: value_min must not exceed value_max.
        op_display = self._form_widgets.get("operator", tk.StringVar()).get()
        op_value = _COUNT_OP_MAP.get(op_display, "equal")
        has_ranged_mode = op_value in {"between", "not_between"}

        if has_ranged_mode:
            if self._safe_int("value_min", C_CONSTANT_INVALID_INT) == C_CONSTANT_INVALID_INT:
                errors.append("La valeur minimale doit être un nombre positif ou égal à 0.")
            if self._safe_int("value_max", C_CONSTANT_INVALID_INT) == C_CONSTANT_INVALID_INT:
                errors.append("La valeur maximale doit être un nombre positif ou égal à 0.")
            if self._safe_int("value_min", 0) > self._safe_int("value_max", 0):
                errors.append("La valeur minimale doit être inférieure ou égale à la valeur maximale.")
        elif self._safe_int("value", C_CONSTANT_INVALID_INT) == C_CONSTANT_INVALID_INT:
            errors.append("La valeur doit être un nombre positif ou égal à 0.")

        return errors

    def _validate_close_tabs_form(self) -> list[str]:
        """Validates CLOSE_TABS fields."""
        errors: list[str] = []
        if self._safe_int("max_tabs", -1) < 0:
            errors.append("Max onglets doit être >= 0.")
        return errors

    def _validate_extract_text_form(self) -> list[str]:
        """Validates EXTRACT_TEXT fields."""
        errors: list[str] = []
        if not self._form_widgets.get("selector", tk.StringVar()).get().strip():
            errors.append("Le sélecteur CSS est obligatoire.")
        return errors

    def _validate_jump_to_step_form(self) -> list[str]:
        """Validates JUMP_TO_STEP fields."""
        errors: list[str] = []
        target_display = self._form_widgets.get("target_index", tk.StringVar()).get()
        if target_display not in self._jump_target_displays:
            errors.append("Sélectionnez une étape cible valide.")
        return errors

    # ---------------------------------------------------------------
    # Button handlers
    # ---------------------------------------------------------------

    def _confirm(self) -> None:
        """Validates the form, builds the step, and fires on_confirm."""
        label = self._type_var.get()
        step_type = _LABEL_TO_TYPE.get(label)
        if step_type is None:
            return

        # Show the first error if validation fails, keeping the form open.
        errors = self._validate_form(step_type)
        if errors:
            self._error_label.configure(text=errors[0])
            return

        # Build and broadcast the confirmed step to the presenter.
        self._error_label.configure(text="")
        params = self._get_params(step_type)

        ## TODO PCO je distingue pas les nouveaux des existants
        if self._step_selected:
            step = StepScrapingModel(
                step_type=step_type,
                is_active=self._step_selected.is_active,
                step_id=generate_rng_hexastring(C_SIZE_HEXASTRING_WORKFLOW_ITEM_ID),
                params=params,
            )
        else:
            step = StepScrapingModel(
                step_type=step_type,
                is_active=True,
                step_id=generate_rng_hexastring(C_SIZE_HEXASTRING_WORKFLOW_ITEM_ID),
                params=params,
            )
        if self.on_confirm:
            self.on_confirm(step)

    def _cancel(self) -> None:
        """Fires the on_cancel callback without modifying the step list."""
        if self.on_cancel:
            self.on_cancel()
