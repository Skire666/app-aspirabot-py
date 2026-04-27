"""Provider step editor dialog utilities.

This module contains the UI helper responsible for rendering and validating
step-edit dialogs used by the provider editor view.

The class is intentionally isolated from the presenter to keep MVP boundaries
clear and make validation helpers easier to unit test.

Example:
    from views.provider_steps_dialog import ProviderStepDialog

    dialog = ProviderStepDialog(parent=view, type_to_label=TYPE_TO_LABEL)
    submitted, value = dialog.open_step_dialog("wait_seconds", {"amount": 3, "unit": "seconds"})
    if submitted:
        print(value)
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable, Optional, cast


StepSubmitCallback = Callable[[], None]
StepBuilder = Callable[[Any, ttk.Frame, tk.Toplevel, dict[str, Any]], StepSubmitCallback]


class ProviderStepsCreatorView:
    """Dialog factory and validator for provider workflow step values.

    Args:
        parent: Parent Tk widget used to host modal dialogs.
        type_to_label: Mapping from internal step type to dialog title.

    Raises:
        None.

    Example:
        dialog = ProviderStepsCreatorView(parent=root, type_to_label={"open_url": "Open URL"})
        ok, value = dialog.open_step_dialog("open_url", "https://example.com")
        if ok:
            print(value)
    """

    def __init__(self, parent: tk.Widget, type_to_label: dict[str, str]) -> None:
        """Initializes the dialog helper with immutable UI mappings.

        Args:
            parent: Parent Tk widget.
            type_to_label: Mapping from step type to user-facing label.

        Returns:
            None.

        Raises:
            None.
        """
        self._parent = parent
        # Copy to avoid accidental external mutation.
        self._type_to_label = dict(type_to_label)

    def _show_invalid_type_error(self) -> None:
        """Displays a standardized invalid-type message.

        Returns:
            None.

        Raises:
            None.
        """
        # Keep user feedback consistent for unsupported step types.
        messagebox.showerror("Erreur", "Type d'étape invalide.")

    def open_step_dialog(self, step_type: str, initial_value: Any = None) -> tuple[bool, Any]:
        """Opens a modal step dialog and returns normalized user input.

        Args:
            step_type: Internal step type key (for example ``"open_url"``).
            initial_value: Existing step value used to prefill fields.

        Returns:
            A tuple ``(submitted, value)`` where:
            - ``submitted`` indicates whether the user validated the form.
            - ``value`` is the normalized value for the selected step type.

        Raises:
            tk.TclError: If Tkinter cannot create or render dialog widgets.

        Example:
            submitted, value = dialog.open_step_dialog("click_element", {"selector": ".btn"})
            if submitted:
                process(value)
        """
        # Reject unknown types early and avoid dialog creation.
        if step_type not in self._type_to_label:
            self._show_invalid_type_error()
            return False, None

        # Create dialog shell and shared result container.
        dialog, content = self._create_dialog(step_type)
        result: dict[str, Any] = {"value": None, "submitted": False}
        submit = self._build_step_form(step_type, initial_value, content, dialog, result)

        # Defensive fallback if dispatch mapping is inconsistent.
        if submit is None:
            self._show_invalid_type_error()
            dialog.destroy()
            return False, None

        # Render footer actions and block until dialog closes.
        self._create_footer(content, dialog, submit)
        self._parent.wait_window(dialog)

        # Return explicit cancellation contract for caller code.
        if not bool(result["submitted"]):
            return False, None
        return True, result["value"]

    def _create_dialog(self, step_type: str) -> tuple[tk.Toplevel, ttk.Frame]:
        """Creates modal dialog container and content frame.

        Args:
            step_type: Internal step type key used to set dialog title.

        Returns:
            A tuple ``(dialog, content_frame)``.

        Raises:
            tk.TclError: If dialog widgets cannot be created.
        """
        # Build a modal top-level attached to the parent window.
        dialog = tk.Toplevel(self._parent)
        dialog.title(self._type_to_label[step_type])
        dialog.transient(self._parent.winfo_toplevel())
        dialog.grab_set()
        dialog.resizable(False, False)

        # Use one inner frame to host all dynamic controls.
        content = ttk.Frame(dialog, padding=12)
        content.pack(fill=tk.BOTH, expand=True)
        return dialog, content

    def _build_step_form(
        self,
        step_type: str,
        initial_value: Any,
        content: ttk.Frame,
        dialog: tk.Toplevel,
        result: dict[str, Any],
    ) -> Optional[StepSubmitCallback]:
        """Dispatches form construction based on step type.

        Args:
            step_type: Internal step type key.
            initial_value: Prefill value for edit mode.
            content: Target frame for widgets.
            dialog: Owning modal dialog.
            result: Mutable output container populated on submit.

        Returns:
            A submit callback for the generated form, or ``None`` if unknown.

        Raises:
            None.
        """
        # Map each step type to a dedicated builder method.
        builders: dict[str, StepBuilder] = {
            "open_url": self._build_open_url,
            "wait_seconds": self._build_wait_seconds,
            "refresh_page": self._build_refresh_page,
            "download_image": self._build_download_image,
            "check_if_image_here": self._build_check_if_image_here,
            "click_element": self._build_click_element,
        }

        # Resolve and run the builder if available.
        builder = builders.get(step_type)
        if builder is None:
            return None
        return builder(initial_value, content, dialog, result)

    def _create_footer(
        self,
        content: ttk.Frame,
        dialog: tk.Toplevel,
        submit: StepSubmitCallback,
    ) -> None:
        """Creates dialog footer buttons and close protocol binding.

        Args:
            content: Dialog content frame.
            dialog: Modal dialog instance.
            submit: Callback triggered by the validate button.

        Returns:
            None.

        Raises:
            tk.TclError: If footer widgets cannot be created.
        """
        # Ensure second column expands for form alignment.
        content.columnconfigure(1, weight=1)
        content.rowconfigure(98, weight=1)

        # Create footer button row below form controls.
        buttons = ttk.Frame(content)
        buttons.grid(row=99, column=0, columnspan=2, sticky="sew")

        # Keep action order consistent across all step dialogs.
        ttk.Button(buttons, text="Annuler", command=dialog.destroy).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(buttons, text="Valider", command=submit).pack(side=tk.RIGHT)
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

    def _build_open_url(
        self,
        initial_value: Any,
        content: ttk.Frame,
        dialog: tk.Toplevel,
        result: dict[str, Any],
    ) -> StepSubmitCallback:
        """Builds the form and submit handler for the ``open_url`` step.

        Args:
            initial_value: Existing URL value when editing.
            content: Target frame for widgets.
            dialog: Owning modal dialog.
            result: Mutable output container.

        Returns:
            A submit callback that validates and stores a URL string.

        Raises:
            None.
        """
        # Create single URL field prefilled from existing data.
        ttk.Label(content, text="URL:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        url_var = tk.StringVar(value=str(initial_value) if initial_value is not None else "")
        url_entry = ttk.Entry(content, textvariable=url_var, width=50)
        url_entry.grid(row=0, column=1, sticky="ew", pady=(0, 8))
        url_entry.focus_set()

        def submit() -> None:
            """Validates URL input and finalizes dialog result."""
            # Normalize user input before validation.
            value = url_var.get().strip()
            if not value:
                self._show_dialog_error(dialog, "La valeur URL est obligatoire.")
                return

            # Persist normalized payload and close the dialog.
            result["value"] = value
            result["submitted"] = True
            dialog.destroy()

        return submit

    def _build_wait_seconds(
        self,
        initial_value: Any,
        content: ttk.Frame,
        dialog: tk.Toplevel,
        result: dict[str, Any],
    ) -> StepSubmitCallback:
        """Builds the form and submit handler for ``wait_seconds``.

        Args:
            initial_value: Existing wait configuration.
            content: Target frame for widgets.
            dialog: Owning modal dialog.
            result: Mutable output container.

        Returns:
            A submit callback returning ``{"amount": int, "unit": str}``.

        Raises:
            None.
        """
        # Render duration amount input.
        ttk.Label(content, text="Durée:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        amount, unit_token = self._get_wait_initials(initial_value)
        wait_var = tk.StringVar(value=amount)
        ttk.Entry(content, textvariable=wait_var, width=20).grid(row=0, column=1, sticky="w", pady=(0, 8))

        # Render unit selector based on display-to-token mapping.
        ttk.Label(content, text="Unité:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        unit_map = self._get_wait_units_map()
        reverse_map = {value: key for key, value in unit_map.items()}
        wait_unit_var = tk.StringVar(value=reverse_map.get(unit_token, "seconde"))
        ttk.Combobox(content, textvariable=wait_unit_var, values=list(unit_map.keys()), state="readonly", width=18).grid(
            row=1,
            column=1,
            sticky="w",
            pady=(0, 8),
        )

        # Return dedicated callback so this method stays focused.
        return self._make_wait_seconds_submit(wait_var, wait_unit_var, unit_map, dialog, result)

    def _make_wait_seconds_submit(
        self,
        wait_var: tk.StringVar,
        wait_unit_var: tk.StringVar,
        unit_map: dict[str, str],
        dialog: tk.Toplevel,
        result: dict[str, Any],
    ) -> StepSubmitCallback:
        """Creates submit callback for ``wait_seconds`` validation.

        Args:
            wait_var: Variable containing duration amount.
            wait_unit_var: Variable containing unit display label.
            unit_map: Mapping from UI labels to backend tokens.
            dialog: Owning modal dialog.
            result: Mutable output container.

        Returns:
            A callback validating positive integer duration.

        Raises:
            None.
        """

        def submit() -> None:
            """Validates wait values, writes result, and closes dialog."""
            # Read and normalize the amount entered by user.
            raw = wait_var.get().strip()
            if not raw:
                self._show_dialog_error(dialog, "La durée est obligatoire.")
                return
            if not raw.isdigit() or int(raw) <= 0:
                self._show_dialog_error(dialog, "La durée doit être un entier positif.")
                return

            # Convert display unit to token expected by downstream logic.
            result["value"] = {
                "amount": int(raw),
                "unit": unit_map.get(wait_unit_var.get(), "seconds"),
            }
            result["submitted"] = True
            dialog.destroy()

        return submit

    def _build_refresh_page(
        self,
        initial_value: Any,
        content: ttk.Frame,
        dialog: tk.Toplevel,
        result: dict[str, Any],
    ) -> StepSubmitCallback:
        """Builds the form and submit handler for ``refresh_page``.

        Args:
            initial_value: Existing boolean for cache clearing.
            content: Target frame for widgets.
            dialog: Owning modal dialog.
            result: Mutable output container.

        Returns:
            A submit callback returning a boolean value.

        Raises:
            None.
        """
        # Render explanatory text and a single checkbox option.
        ttk.Label(content, text="Cette étape rafraîchira la page active.").grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 8),
        )
        clear_cache_var = tk.BooleanVar(value=bool(initial_value))
        ttk.Checkbutton(
            content,
            text="Vider le cache avant rafraîchissement",
            variable=clear_cache_var,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))

        def submit() -> None:
            """Stores checkbox value and closes dialog."""
            # Return boolean payload directly.
            result["value"] = clear_cache_var.get()
            result["submitted"] = True
            dialog.destroy()

        return submit

    def _build_download_image(
        self,
        initial_value: Any,
        content: ttk.Frame,
        dialog: tk.Toplevel,
        result: dict[str, Any],
    ) -> StepSubmitCallback:
        """Builds the form and submit handler for ``download_image``.

        Args:
            initial_value: Existing image download settings.
            content: Target frame for widgets.
            dialog: Owning modal dialog.
            result: Mutable output container.

        Returns:
            A submit callback returning a download configuration dict.

        Raises:
            None.
        """
        # Render controls and collect bound Tk variables.
        mode_var, min_w, min_h, max_w, max_h = self._build_download_controls(initial_value, content)

        # Delegate submit callback creation to keep this method small.
        return self._make_download_submit(mode_var, min_w, min_h, max_w, max_h, dialog, result)

    def _make_download_submit(
        self,
        mode_var: tk.StringVar,
        min_w: tk.StringVar,
        min_h: tk.StringVar,
        max_w: tk.StringVar,
        max_h: tk.StringVar,
        dialog: tk.Toplevel,
        result: dict[str, Any],
    ) -> StepSubmitCallback:
        """Creates submit callback for ``download_image`` validation.

        Args:
            mode_var: Variable containing selected mode token.
            min_w: Variable containing minimum width.
            min_h: Variable containing minimum height.
            max_w: Variable containing maximum width.
            max_h: Variable containing maximum height.
            dialog: Owning modal dialog.
            result: Mutable output container.

        Returns:
            A callback validating dimensions and returning a dict payload.

        Raises:
            None.
        """

        def submit() -> None:
            """Validates dimensions and stores normalized download settings."""
            # Parse and validate all four dimension fields in one helper call.
            min_width, min_height, max_width, max_height = self._parse_download_dimensions(
                min_w,
                min_h,
                max_w,
                max_h,
                dialog,
            )
            if min_width is None or min_height is None or max_width is None or max_height is None:
                return

            # Build final payload with explicit semantic keys.
            result["value"] = self._build_download_value(
                mode_var.get(),
                min_width,
                min_height,
                max_width,
                max_height,
            )
            result["submitted"] = True
            dialog.destroy()

        return submit

    def _parse_download_dimensions(
        self,
        min_w: tk.StringVar,
        min_h: tk.StringVar,
        max_w: tk.StringVar,
        max_h: tk.StringVar,
        dialog: tk.Toplevel,
    ) -> tuple[Optional[int], Optional[int], Optional[int], Optional[int]]:
        """Parses and validates all image dimensions from bound variables.

        Args:
            min_w: Variable containing minimum width text.
            min_h: Variable containing minimum height text.
            max_w: Variable containing maximum width text.
            max_h: Variable containing maximum height text.
            dialog: Owning modal dialog for scoped error messages.

        Returns:
            A tuple ``(min_width, min_height, max_width, max_height)``.
            Any element may be ``None`` when validation fails.

        Raises:
            None.
        """
        # Validate minimum width.
        min_width, error = self._parse_non_negative_int(min_w.get(), "La largeur minimale")
        if error:
            self._show_dialog_error(dialog, error)
            return None, None, None, None

        # Validate minimum height.
        min_height, error = self._parse_non_negative_int(min_h.get(), "La hauteur minimale")
        if error:
            self._show_dialog_error(dialog, error)
            return None, None, None, None

        # Validate maximum width.
        max_width, error = self._parse_non_negative_int(max_w.get(), "La largeur maximale")
        if error:
            self._show_dialog_error(dialog, error)
            return None, None, None, None

        # Validate maximum height.
        max_height, error = self._parse_non_negative_int(max_h.get(), "La hauteur maximale")
        if error:
            self._show_dialog_error(dialog, error)
            return None, None, None, None

        return min_width, min_height, max_width, max_height

    def _build_check_if_image_here(
        self,
        initial_value: Any,
        content: ttk.Frame,
        dialog: tk.Toplevel,
        result: dict[str, Any],
    ) -> StepSubmitCallback:
        """Builds the form and submit handler for ``check_if_image_here``.

        Args:
            initial_value: Existing coordinate boundaries.
            content: Target frame for widgets.
            dialog: Owning modal dialog.
            result: Mutable output container.

        Returns:
            A submit callback returning coordinate boundary dict.

        Raises:
            None.
        """
        # Render four boundary inputs and return their variables.
        w1_var, w2_var, h1_var, h2_var = self._build_check_image_controls(initial_value, content)

        # Delegate callback building to keep this method concise.
        return self._make_check_image_submit(w1_var, w2_var, h1_var, h2_var, dialog, result)

    def _make_check_image_submit(
        self,
        w1_var: tk.StringVar,
        w2_var: tk.StringVar,
        h1_var: tk.StringVar,
        h2_var: tk.StringVar,
        dialog: tk.Toplevel,
        result: dict[str, Any],
    ) -> StepSubmitCallback:
        """Creates submit callback for ``check_if_image_here`` validation.

        Args:
            w1_var: Variable containing width lower bound.
            w2_var: Variable containing width upper bound.
            h1_var: Variable containing height lower bound.
            h2_var: Variable containing height upper bound.
            dialog: Owning modal dialog.
            result: Mutable output container.

        Returns:
            A callback validating integer bounds and ordering.

        Raises:
            None.
        """

        def submit() -> None:
            """Validates boundaries and stores normalized range payload."""
            # Parse all boundaries using shared integer parsing helper.
            bounds = self._parse_check_image_bounds(w1_var, w2_var, h1_var, h2_var, dialog)
            if bounds is None:
                return

            # Enforce strict min/max ordering for both axes.
            w1, w2, h1, h2 = bounds
            if w1 >= w2 or h1 >= h2:
                self._show_dialog_error(
                    dialog,
                    "Les bornes min doivent être strictement inférieures aux bornes max.",
                )
                return

            # Persist result payload and close dialog.
            result["value"] = {"w1": w1, "w2": w2, "h1": h1, "h2": h2}
            result["submitted"] = True
            dialog.destroy()

        return submit

    def _parse_check_image_bounds(
        self,
        w1_var: tk.StringVar,
        w2_var: tk.StringVar,
        h1_var: tk.StringVar,
        h2_var: tk.StringVar,
        dialog: tk.Toplevel,
    ) -> Optional[tuple[int, int, int, int]]:
        """Parses integer bounds used by ``check_if_image_here``.

        Args:
            w1_var: Variable for width lower bound.
            w2_var: Variable for width upper bound.
            h1_var: Variable for height lower bound.
            h2_var: Variable for height upper bound.
            dialog: Owning modal dialog for scoped error messages.

        Returns:
            ``(w1, w2, h1, h2)`` when parsing succeeds; otherwise ``None``.

        Raises:
            None.
        """
        # Parse W1 and short-circuit on first error.
        w1, error = self._parse_int(w1_var.get(), "W1")
        if error:
            self._show_dialog_error(dialog, error)
            return None

        # Parse W2 and short-circuit on first error.
        w2, error = self._parse_int(w2_var.get(), "W2")
        if error:
            self._show_dialog_error(dialog, error)
            return None

        # Parse H1 and short-circuit on first error.
        h1, error = self._parse_int(h1_var.get(), "H1")
        if error:
            self._show_dialog_error(dialog, error)
            return None

        # Parse H2 and return strongly-typed tuple.
        h2, error = self._parse_int(h2_var.get(), "H2")
        if error:
            self._show_dialog_error(dialog, error)
            return None

        if w1 is None or w2 is None or h1 is None or h2 is None:
            return None
        return w1, w2, h1, h2

    def _build_click_element(
        self,
        initial_value: Any,
        content: ttk.Frame,
        dialog: tk.Toplevel,
        result: dict[str, Any],
    ) -> StepSubmitCallback:
        """Builds the form and submit handler for ``click_element``.

        Args:
            initial_value: Existing click configuration.
            content: Target frame for widgets.
            dialog: Owning modal dialog.
            result: Mutable output container.

        Returns:
            A submit callback returning click mode configuration.

        Raises:
            None.
        """
        # Render selector and mode toggles.
        selector_var, normal_var, forced_var, js_var, verify_var = self._build_click_controls(initial_value, content)

        def submit() -> None:
            """Validates click options and returns normalized configuration."""
            # Ensure selector is provided.
            selector = selector_var.get().strip()
            if not selector:
                self._show_dialog_error(dialog, "Le sélecteur CSS est obligatoire.")
                return

            # Ensure at least one click mode is enabled.
            normal = normal_var.get()
            forced = forced_var.get()
            js_direct = js_var.get()
            if not (normal or forced or js_direct):
                self._show_dialog_error(
                    dialog,
                    "Sélectionnez au moins un mode de clic (Normal, Forced ou JS Direct).",
                )
                return

            # Persist normalized click payload.
            result["value"] = self._build_click_value(selector, normal, forced, js_direct, verify_var.get())
            result["submitted"] = True
            dialog.destroy()

        return submit

    def _get_wait_units_map(self) -> dict[str, str]:
        """Returns display-to-token mapping for wait units.

        Returns:
            Mapping from localized labels to internal tokens.

        Raises:
            None.
        """
        # Centralize unit mapping to keep consistency across builders.
        return {
            "heure": "hours",
            "minute": "minutes",
            "seconde": "seconds",
            "milli-sec": "milliseconds",
        }

    def _get_wait_initials(self, initial_value: Any) -> tuple[str, str]:
        """Extracts normalized initial values for ``wait_seconds`` controls.

        Args:
            initial_value: Existing wait value from model or view item.

        Returns:
            Tuple ``(amount, unit_token)`` as strings.

        Raises:
            None.
        """
        # Handle dict payload used by current persisted schema.
        if isinstance(initial_value, dict):
            initial_config = cast(dict[str, Any], initial_value)
            return str(initial_config.get("amount", "")), str(initial_config.get("unit", "seconds"))

        # Handle legacy scalar value fallback.
        if initial_value is not None:
            return str(initial_value), "seconds"
        return "", "seconds"

    def _build_download_controls(
        self,
        initial_value: Any,
        content: ttk.Frame,
    ) -> tuple[tk.StringVar, tk.StringVar, tk.StringVar, tk.StringVar, tk.StringVar]:
        """Renders controls for ``download_image`` and returns bound vars.

        Args:
            initial_value: Existing download configuration.
            content: Target frame for widgets.

        Returns:
            Tuple ``(mode, min_w, min_h, max_w, max_h)`` as Tk variables.

        Raises:
            tk.TclError: If any widget creation fails.
        """
        # Load prefilled values before rendering widgets.
        mode, min_w, min_h, max_w, max_h = self._get_download_initials(initial_value)
        ttk.Label(content, text="Mode de téléchargement:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))

        # Create all bound variables used by this form section.
        mode_var = tk.StringVar(value=mode if mode in {"largest", "first", "all"} else "largest")
        min_width_var = tk.StringVar(value=min_w)
        min_height_var = tk.StringVar(value=min_h)
        max_width_var = tk.StringVar(value=max_w)
        max_height_var = tk.StringVar(value=max_h)

        # Render radio buttons for image selection mode.
        ttk.Radiobutton(content, text="La plus grande image", variable=mode_var, value="largest").grid(row=0, column=1, sticky="w", pady=(0, 4))
        ttk.Radiobutton(content, text="La première image", variable=mode_var, value="first").grid(row=1, column=1, sticky="w", pady=(0, 4))
        ttk.Radiobutton(content, text="Toutes les images", variable=mode_var, value="all").grid(row=2, column=1, sticky="w", pady=(0, 8))
        self._grid_dimension_fields(content, min_width_var, min_height_var, max_width_var, max_height_var)

        return mode_var, min_width_var, min_height_var, max_width_var, max_height_var

    def _get_download_initials(self, initial_value: Any) -> tuple[str, str, str, str, str]:
        """Extracts initial values for ``download_image`` controls.

        Args:
            initial_value: Existing download payload.

        Returns:
            Tuple ``(mode, min_w, min_h, max_w, max_h)`` as strings.

        Raises:
            None.
        """
        # Return defaults when no dict payload is available.
        if not isinstance(initial_value, dict):
            return "largest", "0", "0", "0", "0"

        # Normalize persisted values to strings for Tk variables.
        initial_config = cast(dict[str, Any], initial_value)
        return (
            str(initial_config.get("mode", "largest")),
            str(initial_config.get("min_width", 0)),
            str(initial_config.get("min_height", 0)),
            str(initial_config.get("max_width", 0)),
            str(initial_config.get("max_height", 0)),
        )

    def _grid_dimension_fields(
        self,
        content: ttk.Frame,
        min_width_var: tk.StringVar,
        min_height_var: tk.StringVar,
        max_width_var: tk.StringVar,
        max_height_var: tk.StringVar,
    ) -> None:
        """Renders width/height min/max fields for image filtering.

        Args:
            content: Target frame for widgets.
            min_width_var: Variable bound to minimum width entry.
            min_height_var: Variable bound to minimum height entry.
            max_width_var: Variable bound to maximum width entry.
            max_height_var: Variable bound to maximum height entry.

        Returns:
            None.

        Raises:
            tk.TclError: If entry widgets cannot be created.
        """
        # Render width and height bounds in a compact vertical layout.
        ttk.Label(content, text="Largeur min (W):").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(content, textvariable=min_width_var, width=16).grid(row=3, column=1, sticky="w", pady=(0, 8))
        ttk.Label(content, text="Hauteur min (H):").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(content, textvariable=min_height_var, width=16).grid(row=4, column=1, sticky="w", pady=(0, 8))
        ttk.Label(content, text="Largeur max (W):").grid(row=5, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(content, textvariable=max_width_var, width=16).grid(row=5, column=1, sticky="w", pady=(0, 8))
        ttk.Label(content, text="Hauteur max (H):").grid(row=6, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(content, textvariable=max_height_var, width=16).grid(row=6, column=1, sticky="w", pady=(0, 8))

    def _build_download_value(
        self,
        mode: str,
        min_width: int,
        min_height: int,
        max_width: int,
        max_height: int,
    ) -> dict[str, Any]:
        """Builds normalized payload for ``download_image``.

        Args:
            mode: Selected image download mode.
            min_width: Minimum allowed image width.
            min_height: Minimum allowed image height.
            max_width: Maximum allowed image width.
            max_height: Maximum allowed image height.

        Returns:
            Dictionary payload expected by step creation logic.

        Raises:
            None.
        """
        # Keep payload shape explicit for readability and compatibility.
        return {
            "mode": mode,
            "min_width": min_width,
            "min_height": min_height,
            "max_width": max_width,
            "max_height": max_height,
        }

    def _build_check_image_controls(
        self,
        initial_value: Any,
        content: ttk.Frame,
    ) -> tuple[tk.StringVar, tk.StringVar, tk.StringVar, tk.StringVar]:
        """Renders controls for ``check_if_image_here`` boundaries.

        Args:
            initial_value: Existing boundary configuration.
            content: Target frame for widgets.

        Returns:
            Tuple of Tk variables ``(w1, w2, h1, h2)``.

        Raises:
            tk.TclError: If any widget creation fails.
        """
        # Prefill boundary values from existing payload.
        init_w1, init_w2, init_h1, init_h2 = self._get_check_image_initials(initial_value)
        ttk.Label(content, text="W1:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Label(content, text="W2:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Label(content, text="H1:").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Label(content, text="H2:").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(0, 8))

        # Bind entries to dedicated variables.
        w1_var = tk.StringVar(value=init_w1)
        w2_var = tk.StringVar(value=init_w2)
        h1_var = tk.StringVar(value=init_h1)
        h2_var = tk.StringVar(value=init_h2)
        ttk.Entry(content, textvariable=w1_var, width=16).grid(row=0, column=1, sticky="w", pady=(0, 8))
        ttk.Entry(content, textvariable=w2_var, width=16).grid(row=1, column=1, sticky="w", pady=(0, 8))
        ttk.Entry(content, textvariable=h1_var, width=16).grid(row=2, column=1, sticky="w", pady=(0, 8))
        ttk.Entry(content, textvariable=h2_var, width=16).grid(row=3, column=1, sticky="w", pady=(0, 8))

        # Add rule reminder to reduce user input errors.
        ttk.Label(content, text="Condition: W1 < X < W2 et H1 < Y < H2").grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 8),
        )
        return w1_var, w2_var, h1_var, h2_var

    def _get_check_image_initials(self, initial_value: Any) -> tuple[str, str, str, str]:
        """Extracts initial values for ``check_if_image_here`` controls.

        Args:
            initial_value: Existing boundary payload.

        Returns:
            Tuple ``(w1, w2, h1, h2)`` as strings.

        Raises:
            None.
        """
        # Return default boundaries when payload is missing.
        if not isinstance(initial_value, dict):
            return "0", "0", "0", "0"

        # Convert persisted numbers to strings for Tk variables.
        initial_config = cast(dict[str, Any], initial_value)
        return (
            str(initial_config.get("w1", 0)),
            str(initial_config.get("w2", 0)),
            str(initial_config.get("h1", 0)),
            str(initial_config.get("h2", 0)),
        )

    def _build_click_controls(
        self,
        initial_value: Any,
        content: ttk.Frame,
    ) -> tuple[tk.StringVar, tk.BooleanVar, tk.BooleanVar, tk.BooleanVar, tk.BooleanVar]:
        """Renders controls for ``click_element`` step configuration.

        Args:
            initial_value: Existing click configuration.
            content: Target frame for widgets.

        Returns:
            Tuple ``(selector, normal, forced, js_direct, verify_present)``.

        Raises:
            tk.TclError: If any widget creation fails.
        """
        # Load defaults for selector and click modes.
        selector, normal, forced, js_direct, verify = self._get_click_initials(initial_value)
        ttk.Label(content, text="Sélecteur CSS:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))

        # Bind selector entry and focus it for better UX.
        selector_var = tk.StringVar(value=selector)
        selector_entry = ttk.Entry(content, textvariable=selector_var, width=50)
        selector_entry.grid(row=0, column=1, sticky="ew", pady=(0, 8))
        selector_entry.focus_set()

        # Bind each mode checkbox to a dedicated variable.
        normal_var = tk.BooleanVar(value=normal)
        forced_var = tk.BooleanVar(value=forced)
        js_direct_var = tk.BooleanVar(value=js_direct)
        verify_var = tk.BooleanVar(value=verify)
        ttk.Checkbutton(content, text="Normal", variable=normal_var).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Checkbutton(content, text="Forced", variable=forced_var).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Checkbutton(content, text="JS Direct", variable=js_direct_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Checkbutton(content, text="Vérifier présent du bouton", variable=verify_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 8))

        return selector_var, normal_var, forced_var, js_direct_var, verify_var

    def _get_click_initials(self, initial_value: Any) -> tuple[str, bool, bool, bool, bool]:
        """Extracts initial values for ``click_element`` controls.

        Args:
            initial_value: Existing click payload.

        Returns:
            Tuple ``(selector, normal, forced, js_direct, verify_present)``.

        Raises:
            None.
        """
        # Use full dict payload when available.
        if isinstance(initial_value, dict):
            initial_config = cast(dict[str, Any], initial_value)
            return (
                str(initial_config.get("selector", "")),
                bool(initial_config.get("normal", True)),
                bool(initial_config.get("forced", False)),
                bool(initial_config.get("js_direct", False)),
                bool(initial_config.get("verify_present", False)),
            )

        # Handle legacy plain-selector value format.
        if initial_value is not None:
            return str(initial_value), True, False, False, False
        return "", True, False, False, False

    def _build_click_value(
        self,
        selector: str,
        normal: bool,
        forced: bool,
        js_direct: bool,
        verify_present: bool,
    ) -> dict[str, Any]:
        """Builds normalized payload for ``click_element``.

        Args:
            selector: CSS selector to click.
            normal: Enable standard click strategy.
            forced: Enable forced click strategy.
            js_direct: Enable JavaScript-direct click strategy.
            verify_present: Enable selector-presence check before clicking.

        Returns:
            Dictionary payload expected by step creation logic.

        Raises:
            None.
        """
        # Return explicit and stable schema for click behavior.
        return {
            "selector": selector,
            "normal": normal,
            "forced": forced,
            "js_direct": js_direct,
            "verify_present": verify_present,
        }

    @staticmethod
    def _parse_non_negative_int(raw: str, label: str) -> tuple[Optional[int], Optional[str]]:
        """Parses and validates a non-negative integer value.

        Args:
            raw: Raw text input to parse.
            label: Human-readable field label used in error messages.

        Returns:
            Tuple ``(value, error_message)`` where exactly one element is ``None``.

        Raises:
            None.

        Example:
            value, error = ProviderStepDialog._parse_non_negative_int("12", "Width")
            assert value == 12 and error is None
        """
        # Normalize surrounding spaces before checks.
        value = raw.strip()
        if not value:
            return None, f"{label} est obligatoire."
        if not value.isdigit():
            return None, f"{label} doit être un entier >= 0."

        # Convert validated string to integer.
        return int(value), None

    @staticmethod
    def _parse_int(raw: str, label: str) -> tuple[Optional[int], Optional[str]]:
        """Parses and validates a signed integer value.

        Args:
            raw: Raw text input to parse.
            label: Human-readable field label used in error messages.

        Returns:
            Tuple ``(value, error_message)`` where exactly one element is ``None``.

        Raises:
            None.

        Example:
            value, error = ProviderStepDialog._parse_int("-3", "Offset")
            assert value == -3 and error is None
        """
        # Normalize surrounding spaces before checks.
        value = raw.strip()
        if not value:
            return None, f"{label} est obligatoire."
        if value.startswith("-") and not value[1:].isdigit():
            return None, f"{label} doit être un entier."
        if not value.startswith("-") and not value.isdigit():
            return None, f"{label} doit être un entier."

        # Convert validated string to integer.
        return int(value), None

    @staticmethod
    def _show_dialog_error(dialog: tk.Toplevel, message: str) -> None:
        """Shows an error message associated with a specific dialog.

        Args:
            dialog: Parent dialog used as owner for the popup.
            message: Error message shown to the user.

        Returns:
            None.

        Raises:
            None.
        """
        # Keep error popups attached to the active dialog.
        messagebox.showerror("Erreur", message, parent=dialog)
