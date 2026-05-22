"""Tkinter view for managing providers."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk
from typing import Any

from views.components.data_grid import DataGrid
from views.components.folder_link_widget import FolderLinkWidget
from views.components.horizontal_line_frame import HorizontalLineFrame

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Column definitions for the profiles DataGrid.
DATA_GRID_COLUMNS: list[dict[str, Any]] = [
    {"id": "action_launch", "title": "Lancer", "width": 62, "type": "button", "button_text": "Lancer"},
    {"id": "action_edit", "title": "Modif.", "width": 62, "type": "button", "button_text": "Modif."},
    {"id": "action_duplicate", "title": "Dupp.", "width": 62, "type": "button", "button_text": "Dupp."},
    {
        "id": "action_delete",
        "title": "Supp.",
        "width": 62,
        "type": "button",
        "button_text": "Supp.",
    },
    {"id": "provider_name", "title": "Nom", "width": 160, "type": "text"},
    {"id": "provider_desc", "title": "Description", "width": 160, "type": "text"},
    {"id": "version", "title": "Version", "width": 82, "type": "text"},
    {"id": "created_date_provider", "title": "Création", "width": 125, "type": "text", "format": "%d/%m/%Y %H:%M"},
    {"id": "modified_date_provider", "title": "Modification", "width": 125, "type": "text", "format": "%d/%m/%Y %H:%M"},
    {"id": "id_file", "title": "ID Fichier", "width": 100, "type": "text"},
]

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class ProvidersView(ttk.Frame):
    """View component that renders the list of providers."""

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the ProviderView component in Tkinter.

        Args:
            parent: The parent Tkinter widget.
        """
        super().__init__(parent)

        self._on_create_provider: Callable[[], None] | None = None
        self._on_open_folder: Callable[[str], None] | None = None
        self._on_refresh: Callable[[], None] | None = None
        self._on_sort: Callable[[str, bool], None] | None = None
        self._on_edit: Callable[[str], None] | None = None
        self._on_duplicate: Callable[[str], None] | None = None
        self._on_launch: Callable[[str], None] | None = None
        self._on_delete: Callable[[str], None] | None = None
        self._on_validate: Callable[[], None] | None = None

        self._create_actions_widgets()
        self._create_grid_widgets()

    def _create_actions_widgets(self) -> None:
        """Constructs UI elements including top bar and provider list tree."""
        # Top panel
        top_frame = HorizontalLineFrame(self, text="Actions")
        top_frame.pack(side=tk.TOP, fill=tk.X)

        self._btn_create = ttk.Button(top_frame, text="Créer un scénario", command=self._notify_create_provider)
        self._btn_create.pack(side=tk.LEFT, padx=(5, 10))

        self._btn_validate = ttk.Button(top_frame, text="Valider les scénarios", command=self._notify_validate)
        self._btn_validate.pack(side=tk.LEFT, padx=(0, 10))

    def _create_grid_widgets(self) -> None:
        """Constructs UI elements including top bar and provider list tree."""
        # Top panel
        top_frame = HorizontalLineFrame(self, text="Liste des scénarios")
        top_frame.pack(side=tk.TOP, fill=tk.X)

        self._btn_refresh = ttk.Button(top_frame, text="Actualiser", command=self._notify_refresh)
        self._btn_refresh.pack(side=tk.LEFT, padx=(5, 40), pady=(0, 5))

        self._lbl_counter = ttk.Label(top_frame, text="Aucun scénario")
        self._lbl_counter.pack(side=tk.LEFT, padx=(0, 10), pady=(0, 5))

        self._btn_open_folder = FolderLinkWidget(
            top_frame, title="Dossier des scénarios :", path="", callback=self._notify_open_folder
        )
        self._btn_open_folder.pack(side=tk.RIGHT, padx=(10), pady=(0, 5))

        # Main DataGrid for providers
        self.grid = DataGrid(self, columns=DATA_GRID_COLUMNS, on_sort=self._notify_sort, on_action=self._on_action)
        self.grid.set_sort_state("provider_name", True)
        self.grid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    def set_callbacks(
        self,
        on_create: Callable[[], None],
        on_open_folder: Callable[[str], None],
        on_refresh: Callable[[], None],
        on_sort: Callable[[str, bool], None],
        on_edit: Callable[[str], None],
        on_duplicate: Callable[[str], None],
        on_launch: Callable[[str], None],
        on_delete: Callable[[str], None],
        on_validate: Callable[[], None],
    ) -> None:
        """Sets the callbacks for UI interactions.

        Args:
            on_create: Callback for creating a new provider.
            on_open_folder: Callback for opening the providers folder.
            on_refresh: Callback for refreshing the providers list.
            on_sort: Callback for sorting columns.
            on_edit: Callback for executing the edit action.
            on_duplicate: Callback for executing the duplicate action.
            on_launch: Callback for executing the launch action.
            on_delete: Callback for executing the delete action.
            on_validate: Callback for validating provider files.
        """
        self._on_create_provider = on_create
        self._on_open_folder = on_open_folder
        self._on_refresh = on_refresh
        self._on_sort = on_sort
        self._on_edit = on_edit
        self._on_duplicate = on_duplicate
        self._on_launch = on_launch
        self._on_delete = on_delete
        self._on_validate = on_validate

    def _on_action(self, action_id: str, row_id: str) -> None:
        """Handles actions from the DataGrid."""
        guid = row_id
        if action_id == "action_launch" and self._on_launch:
            self._on_launch(guid)
        elif action_id == "action_edit" and self._on_edit:
            self._on_edit(guid)
        elif action_id == "action_duplicate" and self._on_duplicate:
            self._on_duplicate(guid)
        elif action_id == "action_delete" and self._on_delete:
            self._on_delete(guid)

    def _notify_create_provider(self) -> None:
        if self._on_create_provider:
            self._on_create_provider()

    def _notify_open_folder(self, path: str) -> None:
        if self._on_open_folder:
            self._on_open_folder(path)

    def _notify_refresh(self) -> None:
        if self._on_refresh:
            self._on_refresh()

    def _notify_validate(self) -> None:
        if self._on_validate:
            self._on_validate()

    def _notify_sort(self, column: str, ascending: bool) -> None:
        if self._on_sort:
            self._on_sort(column, ascending)

    def set_validation_state(self, is_running: bool, status_text: str = "") -> None:
        """Enables or disables the validation button and updates the status label."""
        if is_running:
            self._btn_validate.config(state=tk.DISABLED)
            self._lbl_counter.config(text=status_text or "Validation en cours...")
            self.update_idletasks()
            return

        self._btn_validate.config(state=tk.NORMAL)

    def render_scenarios(self, folder_path: str, providers_data: list[dict[str, Any]]) -> None:
        """Clears existing UI providers and renders the new list.

        Args:
            folder_path: The path of the providers folder.
            providers_data: A list of dictionaries mapping to the DataGrid columns.
        """
        count = len(providers_data)
        if count == 0:
            self._lbl_counter.config(text="Trouvé : Aucun scénario")
        elif count == 1:
            self._lbl_counter.config(text="Trouvé : 1 scénario")
        else:
            self._lbl_counter.config(text=f"Trouvé : {count} scénarios")

        self._btn_open_folder.set_path(folder_path)
        self.grid.render_data(providers_data)

    @staticmethod
    def show_info(message: str) -> None:
        """Shows an info message box.

        Args:
            message: The message to be displayed.
        """
        messagebox.showinfo("Information", message)

    @staticmethod
    def show_error(message: str) -> None:
        """Shows an error message box.

        Args:
            message: The message to be displayed.
        """
        messagebox.showerror("Erreur", message)

    @staticmethod
    def show_warning(message: str) -> None:
        """Shows a warning message box.

        Args:
            message: The message to be displayed.
        """
        messagebox.showwarning("Avertissement", message)

    @staticmethod
    def show_validation_report(report_data: dict[str, Any]) -> None:
        """Displays a validation summary to the user.

        Args:
            report_data: Flat dict produced by the presenter with keys
                ``total_files``, ``valid_files``, ``invalid_files``, and
                ``issues`` (list of dicts with ``file_name``, ``broken_path``,
                ``reasons``).
        """
        lines = [
            "Validation terminée.",
            f"Total traités : {report_data.get('total_files', 0)}",
            f"Valides : {report_data.get('valid_files', 0)}",
            f"Invalides : {report_data.get('invalid_files', 0)}",
        ]

        # Show per-issue errors when any file was invalid
        if report_data.get("invalid_files", 0) > 0:
            lines.append("")
            lines.append("Erreurs :")
            for issue in report_data.get("issues", []):
                reason_text = "; ".join(issue.get("reasons", []))
                lines.append(f"{reason_text} ({issue.get('file_name', '')}).")
                if issue.get("broken_path"):
                    lines.append(f"Fichier déplacé : {issue['broken_path']}\n")

            messagebox.showerror("Validation des fournisseurs", "\n".join(lines))
            return

        lines.append("")
        lines.append("Aucun fichier fournisseur invalide n'a été détecté.")
        messagebox.showinfo("Validation des fournisseurs", "\n".join(lines))

    @staticmethod
    def ask_duplicate_confirmation() -> bool:
        """Prompts the user for duplication confirmation.

        Returns:
            True if user confirmed the duplication, False otherwise.
        """
        return messagebox.askyesno("Confirmer", "Voulez-vous dupliquer ce fournisseur ?")

    @staticmethod
    def ask_delete_confirmation() -> bool:
        """Prompts the user for deletion confirmation.

        Returns:
            True if user confirmed the deletion, False otherwise.
        """
        return messagebox.askyesno("Confirmer", "Voulez-vous vraiment supprimer ce fournisseur ?")


# EOF
