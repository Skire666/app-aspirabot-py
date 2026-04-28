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

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, ClassVar, Optional

from models.step_scrapping_model import StepScrappingModel, StepType

# French display labels for each step type (Combobox values).
STEP_TYPE_LABELS: dict[StepType, str] = {
    StepType.OPEN_URL: "Ouvrir une URL",
    StepType.SLEEP: "Pause fixe",
    StepType.RANDOM_PAUSE: "Pause aléatoire",
    StepType.REFRESH_PAGE: "Rafraîchir la page",
    StepType.DOWNLOAD_IMAGE: "Télécharger une image",
    StepType.WAIT_IMAGE_SIZE: "Attendre une taille d'image",
    StepType.CLICK_ELEMENT: "Cliquer sur un élément",
    StepType.WAIT_ELEMENT: "Attendre un élément",
    StepType.SCROLL_DOWN: "Défiler vers le bas",
}

# Reverse mapping for label → StepType lookup.
_LABEL_TO_TYPE: dict[str, StepType] = {v: k for k, v in STEP_TYPE_LABELS.items()}

_ALL_LABELS: list[str] = list(STEP_TYPE_LABELS.values())

# Allowed constrained values (mirrors service layer constants).
_WAIT_STATES = ["commit", "domcontentloaded", "load", "networkidle"]
_UNITS = ["hour", "minute", "second", "millisecond"]
_DOWNLOAD_MODES = ["largest", "first", "last", "all"]
_CLICK_MODES = ["Normal", "Forced", "JS Direct"]


class StepInlineFormPanel(ttk.LabelFrame):
    """Inline form panel for creating or editing a single scraping step.

    Embedded inside WorkflowBuilderView. Hidden by default.
    After confirmation, on_confirm is fired with the built StepScrappingModel.
    After cancellation, on_cancel is fired so the parent can hide the panel.

    Attributes:
        on_confirm: Callback(StepScrappingModel) fired when step is validated.
        on_cancel: Callback fired when the user cancels without changes.
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the panel and builds all sub-regions.

        Args:
            parent: The parent Tkinter widget to embed into.
        """
        super().__init__(parent, text="Brique logique")
        self.on_confirm: Optional[Callable[[StepScrappingModel], None]] = None
        self.on_cancel: Optional[Callable[[], None]] = None
        self.on_type_changed: Optional[Callable[[str], None]] = None
        self._type_var = tk.StringVar()
        self._form_widgets: dict[str, Any] = {}

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

        # --- TOP zone (packed after, top→bottom order) ---
        self._create_type_selector()

        self._form_frame = ttk.Frame(self)
        self._form_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _create_type_selector(self) -> None:
        """Creates the step type selector Combobox at the top."""
        frame = ttk.Frame(self)
        frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        ttk.Label(frame, text="Type d'étape:").pack(side=tk.LEFT, padx=(0, 8))
        cb = ttk.Combobox(
            frame,
            textvariable=self._type_var,
            values=_ALL_LABELS,
            state="readonly",
            width=30,
        )
        cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        cb.bind("<<ComboboxSelected>>", self._on_type_changed)

    def _create_buttons(self) -> None:
        """Creates the Confirm and Cancel buttons at the bottom."""
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        ttk.Button(btn_frame, text="Confirmer", command=self._confirm).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annuler", command=self._cancel).pack(side=tk.RIGHT, padx=5)

    # ---------------------------------------------------------------
    # Public interface
    # ---------------------------------------------------------------

    def load(self, step: Optional[StepScrappingModel] = None) -> None:
        """Prepares the form for a new step or pre-fills it from an existing one.

        Args:
            step: Existing step to pre-fill, or None to show a blank form.
        """
        # Select initial step type and rebuild the form.
        initial_type = step.step_type if step else StepType.OPEN_URL
        label = STEP_TYPE_LABELS[initial_type]
        self._type_var.set(label)
        self._rebuild_form(initial_type)

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

    def _rebuild_form(self, step_type: StepType) -> None:
        """Clears and rebuilds the dynamic form for the given step type."""
        # Destroy previous form widgets.
        for widget in self._form_frame.winfo_children():
            widget.destroy()
        self._form_widgets.clear()
        self._error_label.configure(text="")

        # Dispatch to the matching form builder.
        builders = {
            StepType.OPEN_URL: self._build_form_open_url,
            StepType.SLEEP: self._build_form_sleep,
            StepType.RANDOM_PAUSE: self._build_form_random_pause,
            StepType.REFRESH_PAGE: self._build_form_refresh_page,
            StepType.DOWNLOAD_IMAGE: self._build_form_download_image,
            StepType.WAIT_IMAGE_SIZE: self._build_form_wait_image_size,
            StepType.CLICK_ELEMENT: self._build_form_click_element,
            StepType.WAIT_ELEMENT: self._build_form_wait_element,
            StepType.SCROLL_DOWN: self._build_form_scroll_down,
        }
        builder = builders.get(step_type)
        if builder:
            builder()

    # ---------------------------------------------------------------
    # Per-type form builders
    # ---------------------------------------------------------------

    def _build_form_open_url(self) -> None:
        """Builds the OPEN_URL form (URL field + wait_state combobox)."""
        self._form_frame.columnconfigure(1, weight=1)
        ttk.Label(self._form_frame, text="URL:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        url_var = tk.StringVar(value="https://example.com/")
        ttk.Entry(self._form_frame, textvariable=url_var).grid(
            row=0, column=1, sticky="ew", padx=5, pady=4
        )
        self._form_widgets["url"] = url_var

        # Wait state selector.
        ttk.Label(self._form_frame, text="État d'attente:").grid(
            row=1, column=0, sticky="w", padx=5, pady=4
        )
        ws_var = tk.StringVar(value="domcontentloaded")
        ttk.Combobox(self._form_frame, textvariable=ws_var, values=_WAIT_STATES, state="readonly").grid(
            row=1, column=1, sticky="ew", padx=5, pady=4
        )
        self._form_widgets["wait_state"] = ws_var

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
        unit_var = tk.StringVar(value="second")
        ttk.Combobox(self._form_frame, textvariable=unit_var, values=_UNITS, state="readonly").grid(
            row=1, column=1, sticky="ew", padx=5, pady=4
        )
        self._form_widgets["unit"] = unit_var

    def _build_form_random_pause(self) -> None:
        """Builds the RANDOM_PAUSE form (min, max spinboxes + unit combobox)."""
        self._form_frame.columnconfigure(1, weight=1)
        ttk.Label(self._form_frame, text="Min:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        min_var = tk.StringVar(value="0")
        ttk.Spinbox(self._form_frame, from_=0, to=9999, textvariable=min_var, width=10).grid(
            row=0, column=1, sticky="w", padx=5, pady=4
        )
        self._form_widgets["min"] = min_var

        ttk.Label(self._form_frame, text="Max:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        max_var = tk.StringVar(value="1")
        ttk.Spinbox(self._form_frame, from_=0, to=9999, textvariable=max_var, width=10).grid(
            row=1, column=1, sticky="w", padx=5, pady=4
        )
        self._form_widgets["max"] = max_var

        ttk.Label(self._form_frame, text="Unité:").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        unit_var = tk.StringVar(value="second")
        ttk.Combobox(self._form_frame, textvariable=unit_var, values=_UNITS, state="readonly").grid(
            row=2, column=1, sticky="ew", padx=5, pady=4
        )
        self._form_widgets["unit"] = unit_var

    def _build_form_refresh_page(self) -> None:
        """Builds the REFRESH_PAGE form (clear_cache checkbox)."""
        cache_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self._form_frame, text="Vider le cache", variable=cache_var).grid(
            row=0, column=0, sticky="w", padx=5, pady=4
        )
        self._form_widgets["clear_cache"] = cache_var

    def _build_form_download_image(self) -> None:
        """Builds the DOWNLOAD_IMAGE form (mode + 4 dimension spinboxes)."""
        self._form_frame.columnconfigure(2, weight=1)
        ttk.Label(self._form_frame, text="Mode:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        mode_var = tk.StringVar(value="largest")
        ttk.Combobox(
            self._form_frame, textvariable=mode_var, values=_DOWNLOAD_MODES, state="readonly"
        ).grid(row=0, column=1, columnspan=4, sticky="ew", padx=5, pady=4)
        self._form_widgets["mode"] = mode_var

        # Height and width dimension rows share the same helper.
        self._add_dimension_row(1, "Hauteur (px):", "height_min", "height_max", 0, 99999)
        self._add_dimension_row(2, "Largeur (px):", "width_min", "width_max", 0, 99999)

    def _build_form_wait_image_size(self) -> None:
        """Builds the WAIT_IMAGE_SIZE form (4 dimension spinboxes, no mode)."""
        self._add_dimension_row(0, "Hauteur (px):", "height_min", "height_max", 0, 99999)
        self._add_dimension_row(1, "Largeur (px):", "width_min", "width_max", 0, 99999)

    def _build_form_click_element(self) -> None:
        """Builds the CLICK_ELEMENT form (CSS selector + click_mode combobox)."""
        self._form_frame.columnconfigure(1, weight=1)
        ttk.Label(self._form_frame, text="Sélecteur CSS:").grid(
            row=0, column=0, sticky="w", padx=5, pady=4
        )
        sel_var = tk.StringVar()
        ttk.Entry(self._form_frame, textvariable=sel_var).grid(
            row=0, column=1, sticky="ew", padx=5, pady=4
        )
        self._form_widgets["selector"] = sel_var

        ttk.Label(self._form_frame, text="Mode de clic:").grid(
            row=1, column=0, sticky="w", padx=5, pady=4
        )
        mode_var = tk.StringVar(value="Normal")
        ttk.Combobox(
            self._form_frame, textvariable=mode_var, values=_CLICK_MODES, state="readonly"
        ).grid(row=1, column=1, sticky="ew", padx=5, pady=4)
        self._form_widgets["click_mode"] = mode_var

    def _build_form_wait_element(self) -> None:
        """Builds the WAIT_ELEMENT form (CSS selector entry)."""
        self._form_frame.columnconfigure(1, weight=1)
        ttk.Label(self._form_frame, text="Sélecteur CSS:").grid(
            row=0, column=0, sticky="w", padx=5, pady=4
        )
        sel_var = tk.StringVar()
        ttk.Entry(self._form_frame, textvariable=sel_var).grid(
            row=0, column=1, sticky="ew", padx=5, pady=4
        )
        self._form_widgets["selector"] = sel_var

    def _build_form_scroll_down(self) -> None:
        """Builds the SCROLL_DOWN form (pixel count spinbox)."""
        self._form_frame.columnconfigure(1, weight=1)
        ttk.Label(self._form_frame, text="Pixels:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        px_var = tk.StringVar(value="1000")
        ttk.Spinbox(self._form_frame, from_=0, to=99999, textvariable=px_var, width=10).grid(
            row=0, column=1, sticky="w", padx=5, pady=4
        )
        self._form_widgets["pixels"] = px_var

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

    def _load_step(self, step: StepScrappingModel) -> None:
        """Pre-fills form widgets from an existing step's params.

        Args:
            step: The step whose params will populate the form.
        """
        for key, value in step.params.items():
            if key not in self._form_widgets:
                continue
            widget_var = self._form_widgets[key]
            if isinstance(widget_var, tk.BooleanVar):
                widget_var.set(bool(value))
            else:
                widget_var.set(str(value))

    def _get_params(self, step_type: StepType) -> dict[str, Any]:
        """Reads form widget values and returns the params dict for the step.

        Args:
            step_type: Used to select the correct param reader.

        Returns:
            A dictionary of typed parameter values.
        """
        readers = {
            StepType.OPEN_URL: self._params_open_url,
            StepType.SLEEP: self._params_sleep,
            StepType.RANDOM_PAUSE: self._params_random_pause,
            StepType.REFRESH_PAGE: self._params_refresh_page,
            StepType.DOWNLOAD_IMAGE: self._params_download_image,
            StepType.WAIT_IMAGE_SIZE: self._params_wait_image_size,
            StepType.CLICK_ELEMENT: self._params_click_element,
            StepType.WAIT_ELEMENT: self._params_wait_element,
            StepType.SCROLL_DOWN: self._params_scroll_down,
        }
        reader = readers.get(step_type)
        return reader() if reader else {}

    # ---------------------------------------------------------------
    # Per-type param readers
    # ---------------------------------------------------------------

    def _params_open_url(self) -> dict[str, Any]:
        """Reads OPEN_URL params from form widgets."""
        return {
            "url": self._form_widgets["url"].get().strip(),
            "wait_state": self._form_widgets["wait_state"].get(),
        }

    def _params_sleep(self) -> dict[str, Any]:
        """Reads SLEEP params, coercing duration to float."""
        return {
            "duration": self._safe_float("duration", 0),
            "unit": self._form_widgets["unit"].get(),
        }

    def _params_random_pause(self) -> dict[str, Any]:
        """Reads RANDOM_PAUSE params, coercing min/max to float."""
        return {
            "min": self._safe_float("min", 0),
            "max": self._safe_float("max", 1),
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
        return {
            "height_min": self._safe_int("height_min", 0),
            "height_max": self._safe_int("height_max", 99999),
            "width_min": self._safe_int("width_min", 0),
            "width_max": self._safe_int("width_max", 99999),
        }

    def _params_click_element(self) -> dict[str, Any]:
        """Reads CLICK_ELEMENT params."""
        return {
            "selector": self._form_widgets["selector"].get().strip(),
            "click_mode": self._form_widgets["click_mode"].get(),
        }

    def _params_wait_element(self) -> dict[str, Any]:
        """Reads WAIT_ELEMENT params."""
        return {"selector": self._form_widgets["selector"].get().strip()}

    def _params_scroll_down(self) -> dict[str, Any]:
        """Reads SCROLL_DOWN params, coercing pixels to int."""
        return {"pixels": self._safe_int("pixels", 1000)}

    # ---------------------------------------------------------------
    # Type-safe widget reads
    # ---------------------------------------------------------------

    def _safe_float(self, key: str, default: float) -> float:
        """Reads a float from a StringVar form widget.

        Args:
            key: Form widget key.
            default: Fallback value when conversion fails.

        Returns:
            Float value, or default on failure.
        """
        try:
            return float(self._form_widgets[key].get())
        except (ValueError, KeyError):
            return default

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
            StepType.SLEEP: self._validate_sleep_form,
            StepType.RANDOM_PAUSE: self._validate_random_pause_form,
            StepType.REFRESH_PAGE: lambda: [],
            StepType.DOWNLOAD_IMAGE: self._validate_download_image_form,
            StepType.WAIT_IMAGE_SIZE: self._validate_wait_image_size_form,
            StepType.CLICK_ELEMENT: self._validate_click_element_form,
            StepType.WAIT_ELEMENT: self._validate_wait_element_form,
            StepType.SCROLL_DOWN: lambda: [],
        }
        validator = validators.get(step_type)
        return validator() if validator else []

    def _validate_open_url_form(self) -> list[str]:
        """Validates OPEN_URL fields."""
        errors: list[str] = []
        if not self._form_widgets.get("url", tk.StringVar()).get().strip():
            errors.append("L'URL est obligatoire.")
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
        return self._validate_download_image_form()

    def _validate_click_element_form(self) -> list[str]:
        """Validates CLICK_ELEMENT fields."""
        if not self._form_widgets.get("selector", tk.StringVar()).get().strip():
            return ["Le sélecteur CSS est obligatoire."]
        return []

    def _validate_wait_element_form(self) -> list[str]:
        """Validates WAIT_ELEMENT fields."""
        if not self._form_widgets.get("selector", tk.StringVar()).get().strip():
            return ["Le sélecteur CSS est obligatoire."]
        return []

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
        step = StepScrappingModel(step_type=step_type, params=params)
        if self.on_confirm:
            self.on_confirm(step)

    def _cancel(self) -> None:
        """Fires the on_cancel callback without modifying the step list."""
        if self.on_cancel:
            self.on_cancel()


# ---------------------------------------------------------------------------
# Contextual help content
# ---------------------------------------------------------------------------


class StepHelpTexts:
    """Centralised help strings displayed in the 'Aide à la saisie' panel.

    Update values in BY_LABEL to customise guidance without touching layout
    or logic code.  Keys must match the values in STEP_TYPE_LABELS exactly.

    Attributes:
        FALLBACK: Text shown when no step type is selected.
        BY_LABEL: Mapping from French step-type label to its help string.
    """

    FALLBACK: ClassVar[str] = "Sélectionnez un type de brique pour afficher l'aide."

    BY_LABEL: ClassVar[dict[str, str]] = {
        "Ouvrir une URL": (
            "Navigue vers l'URL indiquée et attend que la page soit dans "
            "l'état choisi.\n\n"
            "• URL : adresse complète incluant https://\n"
            "• État d'attente :\n"
            "  -load : attend l'événement window.load\n"
            "  -domcontentloaded : attend le DOM (plus rapide)\n"
            "  -networkidle : attend la fin des requêtes réseau\n"
            "  -commit : attend la première réponse HTTP"
        ),
        "Pause fixe": (
            "Attend un délai fixe avant de passer à l'étape suivante.\n\n"
            "• Durée : valeur numérique (entier ou décimal)\n"
            "• Unité : millisecond, second, minute ou hour"
        ),
        "Pause aléatoire": (
            "Attend un délai aléatoire compris entre Min et Max.\n"
            "Utile pour simuler un comportement humain.\n\n"
            "• Min : borne inférieure (strictement < Max)\n"
            "• Max : borne supérieure\n"
            "• Unité : millisecond, second, minute ou hour"
        ),
        "Rafraîchir la page": (
            "Recharge la page courante du navigateur.\n\n"
            "• Vider le cache : si coché, force un rechargement complet\n"
            "  sans utiliser le cache du navigateur."
        ),
        "Télécharger une image": (
            "Capture et sauvegarde une image présente sur la page.\n\n"
            "• Mode :\n"
            "  -largest : image la plus grande (surface en pixels)\n"
            "  -first / last : première ou dernière image du DOM\n"
            "  -all : toutes les images de la page\n"
            "• Hauteur / Largeur : filtres optionnels sur les dimensions (px)"
        ),
        "Attendre une taille d'image": (
            "Attend qu'une image atteigne les dimensions minimales indiquées.\n"
            "Utile pour les images chargées en progressive ou lazy-load.\n\n"
            "• Hauteur min / max : intervalle de hauteur attendue (px)\n"
            "• Largeur min / max : intervalle de largeur attendue (px)"
        ),
        "Cliquer sur un élément": (
            "Localise un élément via son sélecteur CSS et le clique.\n\n"
            "• Sélecteur CSS : ex. #submit-btn, .card:first-child\n"
            "• Mode de clic :\n"
            "  -Normal : clic standard Playwright\n"
            "  -Forced : clic même si l'élément est masqué\n"
            "  -JS Direct : exécute element.click() via JavaScript"
        ),
        "Attendre un élément": (
            "Attend qu'un élément CSS soit présent dans le DOM avant de "
            "continuer.\n\n"
            "• Sélecteur CSS : ex. .results-loaded, #content\n"
            "  L'exécution est bloquée jusqu'à ce que l'élément soit visible."
        ),
        "Défiler vers le bas": (
            "Fait défiler la page vers le bas d'un nombre de pixels donné.\n"
            "Utile pour déclencher le chargement en infinite scroll.\n\n"
            "• Pixels : distance de défilement en pixels (ex. 1000)"
        ),
    }


# ---------------------------------------------------------------------------
# Help panel widget
# ---------------------------------------------------------------------------


class StepHelpPanel(ttk.LabelFrame):
    """Read-only help panel showing contextual guidance for the active step type.

    Displayed beside StepInlineFormPanel inside WorkflowBuilderView.
    Call set_help_text() to update the displayed content.
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the panel with a read-only text widget.

        Args:
            parent: The parent Tkinter widget to embed into.
        """
        super().__init__(parent, text="Aide à la saisie")
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Builds the read-only scrollable text area."""
        # Text widget with word-wrap; locked to prevent user edits.
        self._text = tk.Text(
            self,
            wrap=tk.WORD,
            width=1,  # let grid/pack control the width via column weights
            state=tk.DISABLED,
            relief=tk.FLAT,
            cursor="arrow",
            padx=8,
            pady=6,
        )
        self._text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def set_help_text(self, text: str) -> None:
        """Replaces the displayed help content.

        Args:
            text: New help string to display.
        """
        # Re-enable momentarily to allow insertion, then lock again.
        self._text.configure(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.insert("1.0", text)
        self._text.configure(state=tk.DISABLED)
