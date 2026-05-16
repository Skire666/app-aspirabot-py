"""Tkinter view for creating and editing a provider."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import Any

from views.workflow.gestion_etapes_panel_mixin import _GestionEtapesPanelMixin
from views.workflow.informations_panel_mixin import _InformationsPanelMixin
from views.workflow.liste_etapes_panel_mixin import _ListeEtapesPanelMixin

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STATUS_COLOR_OK = "#1b5e20"
_STATUS_COLOR_ERROR = "#b00020"

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class WorkflowView(_InformationsPanelMixin, _GestionEtapesPanelMixin, _ListeEtapesPanelMixin, ttk.Frame):
    """View for creating and editing a provider workflow.

    Composed of three panel mixins assembled in display order (top to bottom):
    1. _InformationsPanelMixin  — provider name, URL, version, file ID fields.
    2. _GestionEtapesPanelMixin — step type selector and inline edit form.
    3. _ListeEtapesPanelMixin   — drag-and-drop step list.

    A footer row with a validation status label and Save / Cancel buttons is
    placed between the Gestion and Liste panels, as required by Tkinter's
    side=BOTTOM packing order (footer must be packed before the expanding panel).
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes WorkflowView and creates all sub-panels.

        Args:
            parent: The parent Tkinter widget.
        """
        super().__init__(parent)
        self._on_save: Callable[[dict[str, Any]], None] | None = None
        self._on_cancel: Callable[[], None] | None = None
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Orchestrates the creation of all panels in display order."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Outer container fills the entire frame.
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=0)

        # Panel 1 — Informations (two-column grid layout).
        top_frame = ttk.Frame(main_container)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=1)
        self._build_informations_panel(top_frame)

        # Panel 2 — Gestion des étapes.
        self._build_gestion_etapes_panel(main_container)

        # Footer — packed with side=BOTTOM before Panel 3 so Tkinter reserves
        # its space before the expanding panel claims the remaining height.
        footer_frame = ttk.Frame(main_container)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 5))
        self._build_footer(footer_frame)

        # Panel 3 — Liste des étapes (fills all remaining vertical space).
        self._build_liste_etapes_panel(main_container)

    def _build_footer(self, parent: tk.Widget) -> None:
        """Creates the validation status label and Save / Cancel buttons.

        Args:
            parent: The footer frame to pack widgets into.
        """
        # Status label on the left expands to fill available width.
        self._lbl_workflow_status = ttk.Label(
            parent, text="", anchor="w", foreground=_STATUS_COLOR_OK
        )
        self._lbl_workflow_status.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Action buttons anchored to the right in reverse visual order.
        self._btn_save = ttk.Button(parent, text="Sauvegarder le fournisseur", command=self._notify_save)
        self._btn_save.pack(side=tk.RIGHT, padx=5)

        self._btn_cancel = ttk.Button(parent, text="Annuler", command=self._notify_cancel)
        self._btn_cancel.pack(side=tk.RIGHT, padx=5)

    # ---------------------------------------------------------------
    # Public interface — callbacks and footer status
    # ---------------------------------------------------------------

    def set_callbacks(
        self,
        on_save: Callable[[dict[str, Any]], None],
        on_cancel: Callable[[], None],
    ) -> None:
        """Registers the Save and Cancel callbacks.

        Args:
            on_save: Called with the form data dict when the user saves.
            on_cancel: Called with no arguments when the user cancels.
        """
        self._on_save = on_save
        self._on_cancel = on_cancel

    def set_workflow_validation_message(self, message: str, is_error: bool) -> None:
        """Updates the validation status label near the Save button.

        Args:
            message: Status text to display.
            is_error: True for error styling (red); False for success (green).
        """
        color = _STATUS_COLOR_ERROR if is_error else _STATUS_COLOR_OK
        self._lbl_workflow_status.configure(text=message, foreground=color)

    # ---------------------------------------------------------------
    # Overrides — data methods that also update the footer status label
    # ---------------------------------------------------------------

    def load_data(self, data: dict[str, Any]) -> None:
        """Populates form fields and resets the workflow validation status label.

        Args:
            data: Dict with keys 'id_file', 'provider_name', 'url', 'version'.
        """
        super().load_data(data)
        self.set_workflow_validation_message("Vérification : --", False)

    def clear_data(self) -> None:
        """Clears all form fields and the workflow validation status label."""
        super().clear_data()
        self.set_workflow_validation_message("", False)

    # ---------------------------------------------------------------
    # Internal button handlers
    # ---------------------------------------------------------------

    def _notify_save(self) -> None:
        """Fires the on_save callback with the current form data."""
        if self._on_save:
            self._on_save(self.get_data())

    def _notify_cancel(self) -> None:
        """Resets the step list then fires the on_cancel callback."""
        self._workflow_builder_view.reset()
        if self._on_cancel:
            self._on_cancel()
