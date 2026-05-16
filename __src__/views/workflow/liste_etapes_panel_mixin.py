"""Mixin providing the 'Liste des étapes' panel for WorkflowView."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import tkinter as tk

from views.components.horizontal_line_frame import HorizontalLineFrame
from views.workflow.steps_list_crud_panel import StepsListCrudView

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class _ListeEtapesPanelMixin:
    """Mixin that builds and exposes the 'Liste des étapes' bottom section.

    Wraps a StepsListCrudView inside a HorizontalLineFrame that expands to fill
    all remaining vertical space. Must be packed after the footer frame so that
    Tkinter's side=BOTTOM reservation does not displace this panel.
    """

    def _build_liste_etapes_panel(self, parent: tk.Widget) -> None:
        """Creates the 'Liste des étapes' panel inside *parent*.

        Args:
            parent: Container widget to pack the panel into.
        """
        # HorizontalLineFrame expands to fill all remaining vertical space.
        workflow_lf = HorizontalLineFrame(parent, text="Liste des étapes")
        workflow_lf.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 5), padx=5)

        # Drag-and-drop step list fills the entire frame.
        self._workflow_builder_view = StepsListCrudView(workflow_lf)
        self._workflow_builder_view.pack(fill=tk.BOTH, expand=True)

    @property
    def workflow_builder_view(self) -> StepsListCrudView:
        """Returns the embedded StepsListCrudView widget.

        Returns:
            The drag-and-drop step list instance.
        """
        return self._workflow_builder_view
