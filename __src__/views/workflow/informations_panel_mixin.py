"""Mixin providing the 'Informations' panel for WorkflowView."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from views.components.horizontal_line_frame import HorizontalLineFrame

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class _InformationsPanelMixin:
    """Mixin that builds and exposes the 'Informations' top section.

    Provides editable fields for provider name, file ID, URL, and version.
    Must be combined with ttk.Frame via multiple inheritance in WorkflowView.
    """

    def _build_informations_panel(self, parent: tk.Widget) -> None:
        """Creates the 'Informations' LabelFrame with two form rows inside *parent*.

        Args:
            parent: Container widget using a grid layout (two columns configured
                by the caller).
        """
        info_lf = HorizontalLineFrame(parent, text="Informations")
        info_lf.grid(row=0, column=0, columnspan=2, sticky="nwes", padx=(5, 5))

        # Row 1 — provider name and auto-generated file ID.
        line1 = ttk.Frame(info_lf)
        line1.pack(fill="x", padx=5, pady=(0, 8))
        self._build_name_row(line1)

        # Row 2 — target URL and semantic version.
        line2 = ttk.Frame(info_lf)
        line2.pack(fill="x", padx=5)
        self._build_url_row(line2)

    def _build_name_row(self, parent: tk.Widget) -> None:
        """Builds the Name and File ID widgets inside the first row frame.

        Args:
            parent: The row frame to pack widgets into.
        """
        ttk.Label(parent, text="Nom :", width=7).pack(side="left")

        # Editable name entry expands to fill the remaining horizontal space.
        self._var_name = tk.StringVar()
        self._entry_name = ttk.Entry(parent, textvariable=self._var_name)
        self._entry_name.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ttk.Label(parent, text="ID Fichier :", width=10).pack(side="left", padx=(20, 0))

        # Read-only: file ID is auto-generated and never edited by the user.
        self._var_id_file = tk.StringVar()
        self._entry_id_file = ttk.Entry(parent, textvariable=self._var_id_file, state="readonly", width=15)
        self._entry_id_file.pack(side="left")

    def _build_url_row(self, parent: tk.Widget) -> None:
        """Builds the URL and Version widgets inside the second row frame.

        Args:
            parent: The row frame to pack widgets into.
        """
        ttk.Label(parent, text="URL :", width=7).pack(side="left")

        # Editable URL entry expands to fill the remaining horizontal space.
        self._var_url = tk.StringVar()
        self._entry_url = ttk.Entry(parent, textvariable=self._var_url)
        self._entry_url.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ttk.Label(parent, text="Version :", width=10).pack(side="left", padx=(20, 0))

        # Fixed-width version field (short semantic version string).
        self._var_version = tk.StringVar()
        self._entry_version = ttk.Entry(parent, textvariable=self._var_version, width=15)
        self._entry_version.pack(side="left")

    # ---------------------------------------------------------------
    # Public data interface
    # ---------------------------------------------------------------

    def load_data(self, data: dict[str, Any]) -> None:
        """Populates all form fields from *data*.

        Args:
            data: Dict with keys 'id_file', 'provider_name', 'url', 'version'.
        """
        self._var_id_file.set(data.get("id_file", ""))
        self._var_name.set(data.get("provider_name", ""))
        self._var_url.set(data.get("url", ""))
        self._var_version.set(data.get("version", ""))

    def get_data(self) -> dict[str, Any]:
        """Reads all form fields and returns them as a dictionary.

        Returns:
            Dict with keys 'id_file', 'provider_name', 'url', 'version'.
        """
        return {
            "id_file": self._var_id_file.get(),
            "provider_name": self._var_name.get(),
            "url": self._var_url.get(),
            "version": self._var_version.get(),
        }

    def clear_data(self) -> None:
        """Resets all form fields to empty strings."""
        self._var_id_file.set("")
        self._var_name.set("")
        self._var_url.set("")
        self._var_version.set("")

    @staticmethod
    def ask_overwrite_confirmation() -> bool:
        """Shows a dialog asking whether to overwrite an existing provider file.

        Returns:
            True if the user confirmed the overwrite; False otherwise.
        """
        return messagebox.askyesno(
            "Écraser?",
            "Un fournisseur avec cette ID existe déjà. Voulez-vous l'écraser ?",
        )

    @staticmethod
    def show_error(message: str) -> None:
        """Displays an error popup with the given message.

        Args:
            message: Text to show inside the error dialog.
        """
        messagebox.showerror("Erreur", message)


# EOF
