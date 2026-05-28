"""Tkinter view for the executor panel.

Displays scenario selection, profile management, launch profile configuration,
and the launch trigger. Contains no business logic — all orchestration is
delegated to ExecutorPresenter via registered callbacks.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import contextlib
import tkinter as tk
from collections.abc import Callable
from datetime import datetime
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any

from models.launcher_model import LaunchModel
from models.scenario_model import ScenarioModel
from models.step_scraping_model import StepScrapingModel
from shared.enums import UrlSortOrderEnum, UrlSourceTypeEnum
from shared.i18n_fra import C_EXEC_SAVED_DATE_EMPTY, C_EXEC_SAVED_DATE_FMT, C_EXEC_USED_DATE_EMPTY, C_EXEC_USED_DATE_FMT
from views.components.column_combobox import ColumnCombobox
from views.components.horizontal_line_frame import HorizontalLineFrame

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_DATE_FMT = "%d/%m/%Y %H:%M"
_MAX_THRESHOLD = 9_999_999


# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class ExecutorView(ttk.Frame):
    """Panel that lets the user configure and launch a scraping session.

    Sections:
        1. Scenario selection (ColumnCombobox + Refresh + Edit buttons).
        2. Available profiles (Listbox + CRUD buttons + saved-date label).
        3. Launch profile configuration (export folder, URL source, thresholds).
        4. Launch trigger (verification label + launch button).

    All user actions are forwarded to the presenter via registered callbacks.
    The view is purely passive: it renders data supplied by the presenter.
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Build widget structure without loading any data.

        Args:
            config_model: Application configuration (unused here, kept for
                consistency with other views that may use it).
            parent: Parent Tkinter container.
        """
        super().__init__(parent)

        # Callbacks registered by the presenter.
        self._on_scenario_changed: Callable[[str], None] | None = None
        self._on_refresh_scenarios: Callable[[], None] | None = None
        self._on_edit_scenario: Callable[[str], None] | None = None
        self._on_profile_selected: Callable[[str], None] | None = None
        self._on_new_profile: Callable[[], None] | None = None
        self._on_rename_profile: Callable[[], None] | None = None
        self._on_delete_profile: Callable[[], None] | None = None
        self._on_save_profile: Callable[[], None] | None = None
        self._on_form_changed: Callable[[], None] | None = None
        self._on_launch: Callable[[], None] | None = None
        self._on_open_export_folder: Callable[[], None] | None = None

        # Cooldown guard for refresh button.
        self._refresh_cooldown: bool = False

        self._create_widgets()

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------

    def _create_widgets(self) -> None:
        """Build all four sections in order."""
        outer = ttk.Frame(self)
        outer.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._create_scenario_section(outer)
        self._create_profiles_section(outer)
        self._create_profile_config_section(outer)
        self._create_launch_section(outer)

    def _create_scenario_section(self, parent: tk.Widget) -> None:
        """Build the scenario selection section."""
        frame = HorizontalLineFrame(parent, text="Liste des scénarios")
        frame.pack(fill=tk.X, pady=(0, 4))

        self._combo_scenarios = ColumnCombobox(frame, width=60)
        self._combo_scenarios.add_column("scenario_name", lambda m: m.scenario_name, width=220)
        self._combo_scenarios.add_column("scenario_desc", lambda m: m.scenario_desc, width=260)
        self._combo_scenarios.add_column("id_file", lambda m: m.id_file, width=90)
        self._combo_scenarios.set_display_column("scenario_name")
        self._combo_scenarios.bind("<<ComboboxSelected>>", self._on_combo_scenario_changed)
        self._combo_scenarios.pack(side=tk.LEFT, padx=(5, 8), pady=(0, 6))

        self._btn_edit = ttk.Button(frame, text="Modifier", command=self._notify_edit_scenario)
        self._btn_edit.pack(side=tk.RIGHT, padx=(4, 5), pady=(0, 6))

        self._btn_refresh = ttk.Button(frame, text="Rafraîchir", command=self._notify_refresh_with_cooldown)
        self._btn_refresh.pack(side=tk.RIGHT, padx=(0, 4), pady=(0, 6))

    def _create_profiles_section(self, parent: tk.Widget) -> None:
        """Build the available-profiles section."""
        frame = HorizontalLineFrame(parent, text="Profils disponibles")
        frame.pack(fill=tk.X, pady=(0, 4))

        self._listbox_profiles = tk.Listbox(frame, height=5, selectmode=tk.SINGLE, exportselection=False)
        self._listbox_profiles.pack(fill=tk.X, padx=5, pady=(0, 4))
        self._listbox_profiles.bind("<<ListboxSelect>>", self._on_listbox_profile_selected)

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, padx=5, pady=(0, 6))

        self._btn_new = ttk.Button(btn_row, text="Nouveau", command=self._notify_new_profile)
        self._btn_new.pack(side=tk.LEFT, padx=(0, 4))

        self._btn_rename = ttk.Button(btn_row, text="Renommer", command=self._notify_rename_profile)
        self._btn_rename.pack(side=tk.LEFT, padx=(0, 4))

        self._btn_delete = ttk.Button(btn_row, text="Supprimer", command=self._notify_delete_profile)
        self._btn_delete.pack(side=tk.LEFT, padx=(0, 4))

        self._btn_save = ttk.Button(btn_row, text="Sauvegarder", command=self._notify_save_profile)
        self._btn_save.pack(side=tk.LEFT, padx=(0, 8))

        self._lbl_saved = ttk.Label(btn_row, text=C_EXEC_SAVED_DATE_EMPTY)
        self._lbl_saved.pack(side=tk.LEFT)

        self.set_profile_buttons_state(selected=False, dirty=False)
        self.set_profiles_list_enabled(False)

    def _create_profile_config_section(self, parent: tk.Widget) -> None:
        """Build the launch-profile configuration section."""
        self._frame_profile_cfg = HorizontalLineFrame(parent, text="Profil de lancement")
        self._frame_profile_cfg.pack(fill=tk.X, pady=(0, 4))
        grid = ttk.Frame(self._frame_profile_cfg)
        grid.pack(fill=tk.X, padx=5, pady=(0, 6))
        self._cfg_grid = grid
        self._create_cfg_row0(grid)
        self._create_cfg_row1(grid)
        self._create_cfg_row2(grid)
        self._create_cfg_row3(grid)
        self._create_cfg_row4(grid)
        self._create_cfg_row5(grid)
        self._create_cfg_row6(grid)

    def _create_cfg_row0(self, grid: tk.Widget) -> None:
        """Row 0 — usage statistics (last used date, launch count)."""
        ttk.Label(grid, text="Dernière utilisation :").grid(row=0, column=0, sticky=tk.W, padx=(0, 4), pady=2)
        self._lbl_used_date = ttk.Label(grid, text=C_EXEC_USED_DATE_EMPTY)
        self._lbl_used_date.grid(row=0, column=1, sticky=tk.W, padx=(0, 20), pady=2)
        ttk.Label(grid, text="Lancements :").grid(row=0, column=2, sticky=tk.W, padx=(0, 4), pady=2)
        self._lbl_launch_count = ttk.Label(grid, text="0")
        self._lbl_launch_count.grid(row=0, column=3, sticky=tk.W, pady=2)

    def _create_cfg_row1(self, grid: tk.Widget) -> None:
        """Row 1 — export folder path, browse button, open-folder button."""
        ttk.Label(grid, text="Dossier d'export :").grid(row=1, column=0, sticky=tk.W, padx=(0, 4), pady=2)
        self._var_export_folder = tk.StringVar()
        self._var_export_folder.trace_add("write", lambda *_: self._notify_form_changed())
        entry = ttk.Entry(grid, textvariable=self._var_export_folder, width=50)
        entry.grid(row=1, column=1, columnspan=2, sticky=tk.EW, padx=(0, 4), pady=2)
        btn_browse = ttk.Button(grid, text="Parcourir", command=self._browse_export_folder)
        btn_browse.grid(row=1, column=3, padx=(0, 4), pady=2)
        btn_open = ttk.Button(grid, text="Ouvrir dossier", command=self._notify_open_export_folder)
        btn_open.grid(row=1, column=4, pady=2)

    def _create_cfg_row2(self, grid: tk.Widget) -> None:
        """Row 2 — URL source type combobox."""
        ttk.Label(grid, text="Source d'URL :").grid(row=2, column=0, sticky=tk.W, padx=(0, 4), pady=2)
        source_choices = [
            ("Liste manuelle", UrlSourceTypeEnum.E_MANUAL.value),
            ("Dossier avec URL", UrlSourceTypeEnum.E_FOLDER.value),
            ("Dossier avec JSON", UrlSourceTypeEnum.E_JSON.value),
        ]
        self._source_choices = source_choices
        display_values = [label for label, _ in source_choices]
        self._combo_source = ttk.Combobox(grid, values=display_values, state="readonly", width=22)
        self._combo_source.grid(row=2, column=1, sticky=tk.W, pady=2)
        self._combo_source.bind("<<ComboboxSelected>>", self._on_source_type_changed)

        # Path entry for folder/json sources.
        self._var_source_path = tk.StringVar()
        self._var_source_path.trace_add("write", lambda *_: self._notify_form_changed())
        self._entry_source_path = ttk.Entry(grid, textvariable=self._var_source_path, width=40)
        self._entry_source_path.grid(row=2, column=2, columnspan=2, sticky=tk.EW, padx=(8, 4), pady=2)
        self._btn_browse_source = ttk.Button(grid, text="Parcourir", command=self._browse_source_folder)
        self._btn_browse_source.grid(row=2, column=4, pady=2)

    def _create_cfg_row3(self, grid: tk.Widget) -> None:
        """Row 3 — URL preview (10 lines, scrollable, editable in manual mode)."""
        ttk.Label(grid, text="Aperçu URLs :").grid(row=3, column=0, sticky=tk.NW, padx=(0, 4), pady=2)
        preview_frame = ttk.Frame(grid)
        preview_frame.grid(row=3, column=1, columnspan=4, sticky=tk.EW, pady=2)
        self._txt_url_preview = tk.Text(preview_frame, height=7, width=70, wrap=tk.NONE)
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self._txt_url_preview.yview)
        self._txt_url_preview.configure(yscrollcommand=scrollbar.set)
        self._txt_url_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._txt_url_preview.bind("<<Modified>>", self._on_url_text_modified)

    def _create_cfg_row4(self, grid: tk.Widget) -> None:
        """Row 4 — sort-order radio buttons (active for folder/json only)."""
        ttk.Label(grid, text="Ordre de lecture :").grid(row=4, column=0, sticky=tk.W, padx=(0, 4), pady=2)
        self._var_sort_order = tk.StringVar(value=UrlSortOrderEnum.E_MTIME_ASC.value)
        rb_frame = ttk.Frame(grid)
        rb_frame.grid(row=4, column=1, columnspan=3, sticky=tk.W, pady=2)
        self._rb_recent = ttk.Radiobutton(
            rb_frame,
            text="Lire récemment modifié",
            variable=self._var_sort_order,
            value=UrlSortOrderEnum.E_MTIME_DESC.value,
            command=self._notify_form_changed,
        )
        self._rb_recent.pack(side=tk.LEFT, padx=(0, 12))
        self._rb_oldest = ttk.Radiobutton(
            rb_frame,
            text="Lire les plus anciens",
            variable=self._var_sort_order,
            value=UrlSortOrderEnum.E_MTIME_ASC.value,
            command=self._notify_form_changed,
        )
        self._rb_oldest.pack(side=tk.LEFT)
        # Disabled by default — enabled only for folder/json.
        self._rb_recent.state(["disabled"])
        self._rb_oldest.state(["disabled"])

    def _create_cfg_row5(self, grid: tk.Widget) -> None:
        """Row 5 — global error threshold."""
        lbl = ttk.Label(grid, text="Erreurs globales max. avant mise en pause d'urgence :")
        lbl.grid(row=5, column=0, columnspan=2, sticky=tk.W, padx=(0, 4), pady=2)
        self._var_global_threshold = tk.StringVar()
        self._var_global_threshold.trace_add("write", lambda *_: self._notify_form_changed())
        entry = ttk.Entry(grid, textvariable=self._var_global_threshold, width=12)
        entry.grid(row=5, column=2, sticky=tk.W, pady=2)

    def _create_cfg_row6(self, grid: tk.Widget) -> None:
        """Row 6 — per-step error threshold with step selector."""
        ttk.Label(grid, text="Mise en pause d'urgence sur :").grid(row=6, column=0, sticky=tk.W, padx=(0, 4), pady=2)
        self._combo_steps = ttk.Combobox(grid, state="readonly", width=38)
        self._combo_steps.grid(row=6, column=1, columnspan=2, sticky=tk.EW, padx=(0, 4), pady=2)
        self._combo_steps.bind("<<ComboboxSelected>>", lambda _: self._notify_form_changed())
        self._var_step_threshold = tk.StringVar()
        self._var_step_threshold.trace_add("write", lambda *_: self._notify_form_changed())
        ttk.Entry(grid, textvariable=self._var_step_threshold, width=12).grid(
            row=6, column=3, sticky=tk.W, padx=(0, 4), pady=2
        )
        ttk.Label(grid, text="erreurs").grid(row=6, column=4, sticky=tk.W, pady=2)

    def _create_launch_section(self, parent: tk.Widget) -> None:
        """Build the launch-trigger section."""
        frame = HorizontalLineFrame(parent, text="Lancer le scraping")
        frame.pack(fill=tk.X, pady=(0, 4))

        row = ttk.Frame(frame)
        row.pack(fill=tk.X, padx=5, pady=(0, 6))

        ttk.Label(row, text="Vérification :").pack(side=tk.LEFT, padx=(0, 6))
        self._lbl_verification = ttk.Label(row, text="", foreground="red")
        self._lbl_verification.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._btn_launch = ttk.Button(row, text="Lancer le scraping", command=self._notify_launch)
        self._btn_launch.pack(side=tk.RIGHT, padx=(8, 0))

    # ------------------------------------------------------------------
    # Public API — data setters
    # ------------------------------------------------------------------

    def set_scenarios(self, scenarios: list[ScenarioModel]) -> None:
        """Populate the scenario combobox.

        Args:
            scenarios: Full list of available scenario models.
        """
        self._combo_scenarios.clear()
        self._combo_scenarios.add_items(scenarios)

    def select_scenario_by_id(self, id_scenario: str) -> None:
        """Pre-select a scenario in the combobox by its id_file.

        Args:
            id_scenario: The scenario ID to select.
        """
        for idx in range(self._combo_scenarios.size()):
            obj = self._combo_scenarios.get_object_at(idx)
            if obj and getattr(obj, "id_file", None) == id_scenario:
                self._combo_scenarios.current(idx)
                return

    def get_selected_scenario(self) -> ScenarioModel | None:
        """Return the currently selected scenario model, or None.

        Returns:
            The bound ``ScenarioModel`` or ``None`` when nothing is selected.
        """
        return self._combo_scenarios.get_selected_object()

    def set_profiles(self, profiles: list[LaunchModel]) -> None:
        """Populate the profile listbox.

        Args:
            profiles: Ordered list of launch profiles to display.
        """
        self._listbox_profiles.delete(0, tk.END)
        self._profile_models: list[LaunchModel] = list(profiles)
        for p in profiles:
            self._listbox_profiles.insert(tk.END, p.profile_name)

    def select_profile_by_id(self, id_profile: str) -> None:
        """Select a profile in the listbox by ID.

        Args:
            id_profile: The profile ID to select.
        """
        for idx, p in enumerate(getattr(self, "_profile_models", [])):
            if p.id_profile == id_profile:
                self._listbox_profiles.selection_clear(0, tk.END)
                self._listbox_profiles.selection_set(idx)
                self._listbox_profiles.see(idx)
                return

    def get_selected_profile(self) -> LaunchModel | None:
        """Return the currently selected profile model, or None.

        Returns:
            The selected ``LaunchModel`` instance, or ``None``.
        """
        sel = self._listbox_profiles.curselection()
        if not sel:
            return None
        models = getattr(self, "_profile_models", [])
        idx = sel[0]
        return models[idx] if idx < len(models) else None

    def set_profiles_list_enabled(self, enabled: bool) -> None:
        """Gray out or restore the profiles listbox and the Nouveau button.

        Args:
            enabled: When False, the listbox and Nouveau button are disabled.
        """
        state = tk.NORMAL if enabled else tk.DISABLED
        self._listbox_profiles.configure(state=state)
        self._btn_new.configure(state=state)

    def set_profile_section_enabled(self, enabled: bool) -> None:
        """Gray out or restore the entire profile-config section.

        Args:
            enabled: When False, the section is visually disabled.
        """
        state = tk.NORMAL if enabled else tk.DISABLED
        for child in self._cfg_grid.winfo_children():
            with contextlib.suppress(tk.TclError):
                child.configure(state=state)

    def set_profile_form(self, model: LaunchModel, steps: list[StepScrapingModel]) -> None:
        """Populate all form fields from a LaunchModel and its scenario steps.

        Args:
            model: The launch profile to render.
            steps: The steps of the selected scenario (for the step combobox).
        """
        self._set_usage_stats(model)
        self._var_export_folder.set(model.export_folder or "")
        self._set_url_source_fields(model)
        self._var_global_threshold.set(str(model.emergency_stop_threshold))
        self._set_steps_combobox(steps, model.emergency_stop_step_id)
        self._var_step_threshold.set(str(model.emergency_stop_step_threshold))

    def _set_usage_stats(self, model: LaunchModel) -> None:
        """Update usage-statistics labels from a model.

        Args:
            model: The launch model containing usage data.
        """
        if model.used_date_profile:
            date_str = model.used_date_profile.strftime(_DATE_FMT)
            self._lbl_used_date.config(text=C_EXEC_USED_DATE_FMT.format(date=date_str))
        else:
            self._lbl_used_date.config(text=C_EXEC_USED_DATE_EMPTY)
        self._lbl_launch_count.config(text=str(model.launch_count))

    def _set_url_source_fields(self, model: LaunchModel) -> None:
        """Populate URL-source-related widgets from the model.

        Args:
            model: The launch model containing URL-source configuration.
        """
        # Select matching combobox entry; default to "Liste manuelle" when unknown.
        for idx, (_, val) in enumerate(self._source_choices):
            if val == model.url_source_type:
                self._combo_source.current(idx)
                break
        else:
            self._combo_source.current(0)

        # Populate path/URL value.
        if model.url_source_type == UrlSourceTypeEnum.E_MANUAL.value:
            urls = model.url_source_value if isinstance(model.url_source_value, list) else []
            self._set_url_preview_text("\n".join(urls), editable=True)
        else:
            path = model.url_source_value if isinstance(model.url_source_value, str) else ""
            self._var_source_path.set(path or "")
            self._set_url_preview_text("", editable=False)

        # Sort-order radio buttons.
        self._var_sort_order.set(model.url_sort_order or UrlSortOrderEnum.E_MTIME_ASC.value)
        self._update_source_type_ui(model.url_source_type)

    def _set_steps_combobox(self, steps: list[StepScrapingModel], selected_id: str) -> None:
        """Populate the per-step combobox with scenario steps.

        Args:
            steps: All steps of the current scenario.
            selected_id: The step_id to pre-select.
        """
        self._step_models: list[StepScrapingModel] = list(steps)
        labels = [f"{i + 1}. {s.step_type.value} — {s.step_id}" for i, s in enumerate(steps)]
        self._combo_steps["values"] = labels
        for idx, s in enumerate(steps):
            if s.step_id == selected_id:
                self._combo_steps.current(idx)
                return
        self._combo_steps.set("")

    def get_profile_form_data(self) -> dict[str, Any]:
        """Read all profile-configuration widgets into a plain dictionary.

        Returns:
            A dict suitable for updating a ``LaunchModel``.
        """
        source_type = self._get_selected_source_type()
        url_value = self._get_url_source_value(source_type)
        step_id = self._get_selected_step_id()
        return {
            "export_folder": self._var_export_folder.get().strip(),
            "url_source_type": source_type,
            "url_source_value": url_value,
            "url_sort_order": self._var_sort_order.get(),
            "emergency_stop_threshold": self._var_global_threshold.get().strip(),
            "emergency_stop_step_id": step_id,
            "emergency_stop_step_threshold": self._var_step_threshold.get().strip(),
        }

    def _get_selected_source_type(self) -> str:
        """Return the raw source-type value of the selected combobox entry."""
        idx = self._combo_source.current()
        if idx < 0 or idx >= len(self._source_choices):
            return ""
        return self._source_choices[idx][1]

    def _get_url_source_value(self, source_type: str) -> list[str] | str | None:
        """Return the URL source value matching the current source type.

        Args:
            source_type: The selected URL source type string.

        Returns:
            A list of URLs for manual mode, or a path string for others.
        """
        if source_type == UrlSourceTypeEnum.E_MANUAL.value:
            raw = self._txt_url_preview.get("1.0", tk.END).strip()
            return [u.strip() for u in raw.splitlines() if u.strip()]
        return self._var_source_path.get().strip() or None

    def _get_selected_step_id(self) -> str:
        """Return the step_id of the entry selected in the step combobox."""
        idx = self._combo_steps.current()
        models = getattr(self, "_step_models", [])
        if 0 <= idx < len(models):
            return models[idx].step_id
        return ""

    def set_url_preview(self, urls: list[str]) -> None:
        """Update the read-only URL preview widget.

        Args:
            urls: Preview URLs to display (up to 10 shown by the provider).
        """
        self._set_url_preview_text("\n".join(urls), editable=False)

    def _set_url_preview_text(self, text: str, *, editable: bool) -> None:
        """Replace the content of the URL text widget.

        Args:
            text: The text to write into the widget.
            editable: When True the widget accepts typing; otherwise read-only.
        """
        self._txt_url_preview.configure(state=tk.NORMAL)
        self._txt_url_preview.delete("1.0", tk.END)
        self._txt_url_preview.insert("1.0", text)
        self._txt_url_preview.edit_modified(False)
        if not editable:
            self._txt_url_preview.configure(state=tk.DISABLED)

    def set_saved_date(self, dt: datetime | None) -> None:
        """Update the "Sauvegardé le" label.

        Args:
            dt: The save timestamp, or None when unsaved.
        """
        if dt:
            self._lbl_saved.config(text=C_EXEC_SAVED_DATE_FMT.format(date=dt.strftime(_DATE_FMT)))
        else:
            self._lbl_saved.config(text=C_EXEC_SAVED_DATE_EMPTY)

    def set_verification_message(self, msg: str) -> None:
        """Display or clear the validation-error message.

        Args:
            msg: The message to show (empty string to clear).
        """
        self._lbl_verification.config(text=msg)

    def set_profile_buttons_state(self, *, selected: bool, dirty: bool) -> None:
        """Enable or disable profile-management buttons based on state.

        Args:
            selected: Whether a profile is currently selected.
            dirty: Whether unsaved changes exist.
        """
        sel_state = tk.NORMAL if selected else tk.DISABLED
        self._btn_rename.configure(state=sel_state)
        self._btn_delete.configure(state=sel_state)
        self._btn_save.configure(state=tk.NORMAL if dirty else tk.DISABLED)

    def set_scenario_edit_button_state(self, enabled: bool) -> None:
        """Enable or disable the 'Modifier' button.

        Args:
            enabled: When False, the button is grayed out.
        """
        self._btn_edit.configure(state=tk.NORMAL if enabled else tk.DISABLED)

    # ------------------------------------------------------------------
    # Public API — callback registration
    # ------------------------------------------------------------------

    def set_on_scenario_changed(self, cb: Callable[[str], None]) -> None:
        """Register callback invoked when the user selects a different scenario.

        Args:
            cb: Called with the selected scenario id_file.
        """
        self._on_scenario_changed = cb

    def set_on_refresh_scenarios(self, cb: Callable[[], None]) -> None:
        """Register callback invoked when the user clicks Rafraîchir.

        Args:
            cb: Zero-argument callable.
        """
        self._on_refresh_scenarios = cb

    def set_on_edit_scenario(self, cb: Callable[[str], None]) -> None:
        """Register callback invoked when the user clicks Modifier.

        Args:
            cb: Called with the selected scenario id_file.
        """
        self._on_edit_scenario = cb

    def set_on_profile_selected(self, cb: Callable[[str], None]) -> None:
        """Register callback invoked when the user clicks a profile in the listbox.

        Args:
            cb: Called with the selected profile id_profile.
        """
        self._on_profile_selected = cb

    def set_on_new_profile(self, cb: Callable[[], None]) -> None:
        """Register callback for the Nouveau profile button."""
        self._on_new_profile = cb

    def set_on_rename_profile(self, cb: Callable[[], None]) -> None:
        """Register callback for the Renommer button."""
        self._on_rename_profile = cb

    def set_on_delete_profile(self, cb: Callable[[], None]) -> None:
        """Register callback for the Supprimer button."""
        self._on_delete_profile = cb

    def set_on_save_profile(self, cb: Callable[[], None]) -> None:
        """Register callback for the Sauvegarder button."""
        self._on_save_profile = cb

    def set_on_form_changed(self, cb: Callable[[], None]) -> None:
        """Register callback invoked when any form field changes (dirty flag).

        Args:
            cb: Zero-argument callable.
        """
        self._on_form_changed = cb

    def set_on_launch(self, cb: Callable[[], None]) -> None:
        """Register callback for the Lancer le scraping button."""
        self._on_launch = cb

    def set_on_open_export_folder(self, cb: Callable[[], None]) -> None:
        """Register callback for the Ouvrir dossier button."""
        self._on_open_export_folder = cb

    def ask_new_profile_name(self) -> str | None:
        """Show a dialog asking for the name of the new profile.

        Returns:
            The user-entered string, or None if the dialog was cancelled.
        """
        return simpledialog.askstring("Nouveau profil", "Nom du profil :", initialvalue="", parent=self)

    def ask_rename(self, current_name: str) -> str | None:
        """Show a dialog asking for a new profile name.

        Args:
            current_name: The current profile name to pre-fill.

        Returns:
            The user-entered string, or None if the dialog was cancelled.
        """
        return simpledialog.askstring("Renommer le profil", "Nouveau nom :", initialvalue=current_name, parent=self)

    def ask_delete_confirm(self, profile_name: str) -> bool:
        """Show a confirmation dialog before deleting a profile.

        Args:
            profile_name: The name of the profile to be deleted.

        Returns:
            True when the user confirms, False when cancelled.
        """
        return messagebox.askyesno(
            "Supprimer le profil",
            f"Supprimer le profil « {profile_name} » ?\nCette action est irréversible.",
            parent=self,
        )

    # ------------------------------------------------------------------
    # Private event handlers
    # ------------------------------------------------------------------

    def _on_combo_scenario_changed(self, _event: tk.Event) -> None:
        obj = self._combo_scenarios.get_selected_object()
        if obj and self._on_scenario_changed:
            self._on_scenario_changed(obj.id_file)

    def _notify_refresh_with_cooldown(self) -> None:
        if self._refresh_cooldown:
            return
        self._refresh_cooldown = True
        self.after(1000, self._reset_refresh_cooldown)
        if self._on_refresh_scenarios:
            self._on_refresh_scenarios()

    def _reset_refresh_cooldown(self) -> None:
        self._refresh_cooldown = False

    def _notify_edit_scenario(self) -> None:
        obj = self._combo_scenarios.get_selected_object()
        if obj and self._on_edit_scenario:
            self._on_edit_scenario(obj.id_file)

    def _on_listbox_profile_selected(self, _event: tk.Event) -> None:
        model = self.get_selected_profile()
        if model and self._on_profile_selected:
            self._on_profile_selected(model.id_profile)

    def _notify_new_profile(self) -> None:
        if self._on_new_profile:
            self._on_new_profile()

    def _notify_rename_profile(self) -> None:
        if self._on_rename_profile:
            self._on_rename_profile()

    def _notify_delete_profile(self) -> None:
        if self._on_delete_profile:
            self._on_delete_profile()

    def _notify_save_profile(self) -> None:
        if self._on_save_profile:
            self._on_save_profile()

    def _notify_form_changed(self) -> None:
        if self._on_form_changed:
            self._on_form_changed()

    def _notify_launch(self) -> None:
        if self._on_launch:
            self._on_launch()

    def _on_source_type_changed(self, _event: tk.Event) -> None:
        source_type = self._get_selected_source_type()
        self._update_source_type_ui(source_type)
        self._notify_form_changed()

    def _update_source_type_ui(self, source_type: str) -> None:
        """Adapt widgets visibility based on the selected URL source type.

        Args:
            source_type: The raw source-type string.
        """
        is_manual = source_type == UrlSourceTypeEnum.E_MANUAL.value
        is_folder_or_json = source_type in {UrlSourceTypeEnum.E_FOLDER.value, UrlSourceTypeEnum.E_JSON.value}
        path_state = tk.NORMAL if is_folder_or_json else tk.DISABLED
        self._entry_source_path.configure(state=path_state)
        self._btn_browse_source.configure(state=path_state)

        rb_state = ["!disabled"] if is_folder_or_json else ["disabled"]
        self._rb_recent.state(rb_state)
        self._rb_oldest.state(rb_state)

        preview_state = tk.NORMAL if is_manual else tk.DISABLED
        self._txt_url_preview.configure(state=preview_state)

    def _on_url_text_modified(self, _event: tk.Event) -> None:
        if self._txt_url_preview.edit_modified():
            self._txt_url_preview.edit_modified(False)
            self._notify_form_changed()

    def _browse_export_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choisir le dossier d'export", parent=self)
        if folder:
            self._var_export_folder.set(folder)

    def _notify_open_export_folder(self) -> None:
        if self._on_open_export_folder:
            self._on_open_export_folder()

    def _browse_source_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choisir le dossier source d'URL", parent=self)
        if folder:
            self._var_source_path.set(folder)

    # ------------------------------------------------------------------
    # Open-folder passthrough
    # ------------------------------------------------------------------

    def show_error(self, title: str, message: str) -> None:
        """Display a modal error dialog.

        Args:
            title: Dialog window title.
            message: Error message to display.
        """
        messagebox.showerror(title, message, parent=self)


# EOF
