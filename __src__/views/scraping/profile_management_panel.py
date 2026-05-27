"""Panel for managing launch profiles attached to a provider."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import contextlib
import tkinter as tk
from collections.abc import Callable
from datetime import datetime
from tkinter import simpledialog, ttk
from typing import Any

from shared.i18n_fra import C_SCRAPING_SAVED_DATE_EMPTY, C_SCRAPING_SAVED_DATE_FMT
from views.components.horizontal_line_frame import HorizontalLineFrame

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _apply_state_recursive(widget: tk.Widget, state: str) -> None:
    """Recursively apply a Tkinter state to a widget and all its children.

    Args:
        widget: Root widget to start from.
        state: ``"normal"`` or ``"disabled"``.
    """
    with contextlib.suppress(tk.TclError):
        widget.configure(state=state)
    for child in widget.winfo_children():
        _apply_state_recursive(child, state)


# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ProfileManagementPanel(ttk.Frame):
    """Listbox-based panel for creating, renaming, and deleting launch profiles.

    The panel starts in disabled state and is enabled by the presenter
    once a provider is loaded.

    Example:
        >>> panel = ProfileManagementPanel(parent)
        >>> panel.set_on_profile_new(lambda name: print(name))
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initialize the panel and build widgets.

        Args:
            parent: The parent Tkinter widget.
        """
        super().__init__(parent)
        self._on_profile_selected_cb: Callable[[str], None] | None = None
        self._on_profile_new_cb: Callable[[str], None] | None = None
        self._on_profile_delete_cb: Callable[[str], None] | None = None
        self._on_profile_rename_cb: Callable[[str, str], None] | None = None
        self._on_profile_save_cb: Callable[[str], None] | None = None

        # Parallel list of profile ids matching the Listbox entries.
        self._profile_ids: list[str] = []
        self._build_widgets()

        # Gray out until a provider is loaded.
        self.set_enabled(False)

    def _build_widgets(self) -> None:
        """Build and pack the Listbox, scrollbar, buttons, and date label."""
        self._frame = HorizontalLineFrame(self, text="Gestion des profils")
        self._frame.pack(side=tk.TOP, fill=tk.X)

        # Listbox row with vertical scrollbar.
        left = ttk.Frame(self._frame)
        left.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5)
        self._build_listbox(left)

        # Action buttons row.
        bottom = ttk.Frame(self._frame)
        bottom.pack(side=tk.TOP, fill=tk.BOTH)
        self._build_buttons(bottom)

    def _build_listbox(self, parent: ttk.Frame) -> None:
        """Build the profile Listbox with a vertical scrollbar.

        Args:
            parent: Container frame for the listbox column.
        """
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL)
        self._lst_profiles = tk.Listbox(
            parent,
            height=3,
            exportselection=False,
            yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=self._lst_profiles.yview)
        self._lst_profiles.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._lst_profiles.bind("<<ListboxSelect>>", self._on_listbox_selected)

    def _build_buttons(self, parent: ttk.Frame) -> None:
        """Build action buttons and the modification-date label.

        Args:
            parent: Container frame for the button row.
        """
        ttk.Button(parent, text="Nouveau", command=self._notify_new, width=15).pack(side=tk.LEFT, padx=5, pady=(5, 0))

        # Rename button — disabled until the user selects a profile.
        self._btn_rename = ttk.Button(parent, text="Renommer", command=self._notify_rename, width=15, state=tk.DISABLED)
        self._btn_rename.pack(side=tk.LEFT, padx=5, pady=(5, 0))

        ttk.Button(parent, text="Supprimer", command=self._notify_delete, width=15).pack(
            side=tk.LEFT, padx=5, pady=(5, 0)
        )

        self._btn_save = ttk.Button(parent, text="Sauvegarder", command=self._notify_save, width=15, state=tk.DISABLED)
        self._btn_save.pack(side=tk.LEFT, padx=5, pady=(5, 0))

        # Date label shows the last modification date of the selected profile.
        self._lbl_modified_date = ttk.Label(parent, text=C_SCRAPING_SAVED_DATE_EMPTY)
        self._lbl_modified_date.pack(side=tk.RIGHT, padx=(10, 5), pady=(5, 0))

    # ------------------------------------------------------------------
    # Callback registration
    # ------------------------------------------------------------------

    def set_on_profile_selected(self, callback: Callable[[str], None]) -> None:
        """Register the callback fired when the user selects a profile.

        Args:
            callback: Callable receiving the selected id_profile.
        """
        self._on_profile_selected_cb = callback

    def set_on_profile_new(self, callback: Callable[[str], None]) -> None:
        """Register the callback fired when the user confirms a new profile name.

        Args:
            callback: Callable receiving the new profile name entered by the user.
        """
        self._on_profile_new_cb = callback

    def set_on_profile_delete(self, callback: Callable[[str], None]) -> None:
        """Register the callback fired when the user deletes a profile.

        Args:
            callback: Callable receiving the id_profile to remove.
        """
        self._on_profile_delete_cb = callback

    def set_on_profile_rename(self, callback: Callable[[str, str], None]) -> None:
        """Register the callback fired when the user renames a profile.

        Args:
            callback: Callable receiving (id_profile, new_name).
        """
        self._on_profile_rename_cb = callback

    def set_on_profile_save(self, callback: Callable[[str], None]) -> None:
        """Register the callback fired when the user saves a profile.

        Args:
            callback: Callable receiving the id_profile to save.
        """
        self._on_profile_save_cb = callback

    # ------------------------------------------------------------------
    # Public data feed
    # ------------------------------------------------------------------

    def render_profiles_list(self, profiles: list[dict[str, Any]]) -> None:
        """Populate the Listbox with the given profile rows.

        Args:
            profiles: List of dicts with keys ``id_profile`` and ``profile_name``.
        """
        self._lst_profiles.delete(0, tk.END)
        self._profile_ids = []

        # Insert each profile name and keep a parallel id list.
        for p in profiles:
            self._lst_profiles.insert(tk.END, p["profile_name"])
            self._profile_ids.append(p["id_profile"])

    def get_selected_id_profile(self) -> str | None:
        """Return the id_profile of the highlighted Listbox entry.

        Returns:
            str | None: The id_profile of the selected entry, or None.
        """
        sel = self._lst_profiles.curselection()
        if not sel:
            return None
        idx = sel[0]
        return self._profile_ids[idx] if idx < len(self._profile_ids) else None

    def set_selected_profile(self, id_profile: str) -> None:
        """Highlight the Listbox entry matching id_profile.

        Args:
            id_profile: The profile identifier to select.
        """
        for idx, pid in enumerate(self._profile_ids):
            if pid == id_profile:
                self._lst_profiles.selection_clear(0, tk.END)
                self._lst_profiles.selection_set(idx)
                self._lst_profiles.see(idx)
                return

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable all widgets in the panel.

        Args:
            enabled: True to make the panel interactive; False to gray it out.
        """
        _apply_state_recursive(self._frame, tk.NORMAL if enabled else tk.DISABLED)

    def set_rename_profile_button_state(self, enabled: bool) -> None:
        """Enable or disable the 'Renommer profil' button.

        Args:
            enabled: True when a profile is selected.
        """
        self._btn_rename.config(state=tk.NORMAL if enabled else tk.DISABLED)

    def set_save_profile_button_state(self, enabled: bool) -> None:
        """Enable or disable the 'Sauvegarder' button.

        Args:
            enabled: True when a profile is selected.
        """
        self._btn_save.config(state=tk.NORMAL if enabled else tk.DISABLED)

    def set_profile_modified_date(self, dt: datetime | None) -> None:
        """Update the last-modification date label.

        Args:
            dt: Datetime object representing the modification date, or None to show a placeholder.
        """
        text = (
            C_SCRAPING_SAVED_DATE_FMT.format(date=dt.strftime("%Y-%m-%d %H:%M:%S"))
            if dt
            else C_SCRAPING_SAVED_DATE_EMPTY
        )
        self._lbl_modified_date.config(text=text)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _on_listbox_selected(self, _event: tk.Event) -> None:
        """Resolve the listbox selection to a id_profile and fire the callback.

        Args:
            _event: Tkinter <<ListboxSelect>> event (unused).
        """
        id_profile = self.get_selected_id_profile()
        if id_profile and self._on_profile_selected_cb:
            self._on_profile_selected_cb(id_profile)

    def _notify_new(self) -> None:
        """Ask the user for a name then fire on_profile_new with it."""
        name = simpledialog.askstring("Nouveau profil", "Nom du profil :", parent=self)
        if name and name.strip() and self._on_profile_new_cb:
            self._on_profile_new_cb(name.strip())

    def _notify_delete(self) -> None:
        """Fire on_profile_delete with the currently selected id_profile."""
        id_profile = self.get_selected_id_profile()
        if id_profile and self._on_profile_delete_cb:
            self._on_profile_delete_cb(id_profile)

    def _notify_rename(self) -> None:
        """Ask the user for a new name then fire on_profile_rename with it."""
        id_profile = self.get_selected_id_profile()
        if not id_profile or not self._on_profile_rename_cb:
            return
        new_name = simpledialog.askstring("Renommer profil", "Nouveau nom du profil :", parent=self)
        if new_name and new_name.strip():
            self._on_profile_rename_cb(id_profile, new_name.strip())

    def _notify_save(self) -> None:
        """Fire on_profile_save with the currently selected id_profile."""
        id_profile = self.get_selected_id_profile()
        if id_profile and self._on_profile_save_cb:
            self._on_profile_save_cb(id_profile)


# EOF
