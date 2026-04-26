"""Tkinter view for creating and editing a provider."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Dict, Any, Optional, cast

class ProviderEditView(ttk.Frame):
    """View component that renders the provider modification form."""

    _ADD_OPTIONS: dict[str, str] = {
        "Ouvrir une URL": "open_url",
        "Attendre X secondes": "wait_seconds",
        "Rafraichir page": "refresh_page",
        "Télécharger une image": "download_image",
        "Vérifier image par taille": "check_if_image_here",
        "Cliquer sur un élément": "click_element",
    }

    _TYPE_TO_LABEL: dict[str, str] = {
        "open_url": "Ouvrir une URL",
        "wait_seconds": "Attendre X secondes",
        "refresh_page": "Rafraichir page",
        "download_image": "Télécharger une image",
        "check_if_image_here": "Vérifier image par taille",
        "click_element": "Cliquer sur un élément",
    }

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the ProviderEditView component in Tkinter.

        Args:
            parent: The parent Tkinter widget.
        """
        super().__init__(parent)

        self._on_save: Optional[Callable[[Dict[str, Any]], None]] = None
        self._on_cancel: Optional[Callable[[], None]] = None
        self._on_add_step: Optional[Callable[[str, Any], None]] = None
        self._on_edit_step: Optional[Callable[[int, str, Any], None]] = None
        self._on_delete_step: Optional[Callable[[int], None]] = None
        self._on_move_up: Optional[Callable[[int], None]] = None
        self._on_move_down: Optional[Callable[[int], None]] = None
        self._on_clear_all: Optional[Callable[[], None]] = None

        self._workflow_items: list[Dict[str, Any]] = []
        self._instruction_form_vars: dict[str, Any] = {}

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Constructs UI elements based on the 4 zones specification."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top Section (Informations + Metadonnees)
        top_frame = ttk.Frame(main_container)
        top_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=1)

        # 1. Informations (Top-left)
        info_lf = ttk.LabelFrame(top_frame, text="Informations")
        info_lf.grid(row=0, column=0, sticky="nwes", padx=(0, 5))
        
        ttk.Label(info_lf, text="Nom:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self._var_name = tk.StringVar()
        self._entry_name = ttk.Entry(info_lf, textvariable=self._var_name)
        self._entry_name.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(info_lf, text="URL:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self._var_url = tk.StringVar()
        self._entry_url = ttk.Entry(info_lf, textvariable=self._var_url)
        self._entry_url.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        self._var_browser = tk.BooleanVar()
        self._chk_browser = ttk.Checkbutton(info_lf, text="Browser affiché", variable=self._var_browser)
        self._chk_browser.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        self._var_obfuscated = tk.BooleanVar()
        self._chk_obfuscated = ttk.Checkbutton(info_lf, text="Automatisation obfusqué", variable=self._var_obfuscated)
        self._chk_obfuscated.grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        info_lf.columnconfigure(1, weight=1) # pour avoir toute la larguer

        # 2. Métadonnées (Top-right)
        meta_lf = ttk.LabelFrame(top_frame, text="Métadonnées")
        meta_lf.grid(row=0, column=1, sticky="nwes", padx=(5, 0))

        ttk.Label(meta_lf, text="Guid:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self._var_guid = tk.StringVar()
        self._entry_guid = ttk.Entry(meta_lf, textvariable=self._var_guid, state="readonly")
        self._entry_guid.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(meta_lf, text="Version:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self._var_version = tk.StringVar()
        self._entry_version = ttk.Entry(meta_lf, textvariable=self._var_version)
        self._entry_version.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(meta_lf, text="Créé le:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self._var_created = tk.StringVar()
        self._entry_created = ttk.Entry(meta_lf, textvariable=self._var_created, state="readonly")
        self._entry_created.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(meta_lf, text="Modifié le:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self._var_modified = tk.StringVar()
        self._entry_modified = ttk.Entry(meta_lf, textvariable=self._var_modified, state="readonly")
        self._entry_modified.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        meta_lf.columnconfigure(1, weight=1)

        # 3. Workflow + Instruction (50/50)
        workflow_instruction_frame = ttk.Frame(main_container)
        workflow_instruction_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        workflow_instruction_frame.columnconfigure(0, weight=1, uniform="workflow_instruction")
        workflow_instruction_frame.columnconfigure(1, weight=1, uniform="workflow_instruction")
        workflow_instruction_frame.rowconfigure(0, weight=1)

        workflow_lf = ttk.LabelFrame(workflow_instruction_frame, text="Workflow")
        workflow_lf.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        workflow_lf.columnconfigure(0, weight=1)
        workflow_lf.rowconfigure(0, weight=1)

        list_frame = ttk.Frame(workflow_lf)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 4))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self._list_steps = tk.Listbox(list_frame, exportselection=False, height=8)
        self._list_steps.grid(row=0, column=0, sticky="nsew")
        self._list_steps.bind("<<ListboxSelect>>", self._on_step_selection_changed)

        steps_scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=cast(Callable[..., Any], getattr(self._list_steps, "yview")),
        )
        steps_scrollbar.grid(row=0, column=1, sticky="ns")
        self._list_steps.configure(yscrollcommand=steps_scrollbar.set)

        controls_frame = ttk.Frame(workflow_lf)
        controls_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(4, 8))
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=0)

        left_controls = ttk.Frame(controls_frame)
        left_controls.grid(row=0, column=0, sticky="w")

        self._btn_edit_step = ttk.Button(left_controls, text="Modifier", command=self._notify_edit_step, state=tk.DISABLED)
        self._btn_edit_step.pack(side=tk.LEFT, padx=(0, 6))

        self._btn_delete_step = ttk.Button(left_controls, text="Supprimer", command=self._notify_delete_step, state=tk.DISABLED)
        self._btn_delete_step.pack(side=tk.LEFT, padx=(0, 6))

        self._btn_move_up = ttk.Button(left_controls, text="Monter", command=self._notify_move_up, state=tk.DISABLED)
        self._btn_move_up.pack(side=tk.LEFT, padx=(0, 6))

        self._btn_move_down = ttk.Button(left_controls, text="Descendre", command=self._notify_move_down, state=tk.DISABLED)
        self._btn_move_down.pack(side=tk.LEFT, padx=(0, 6))

        right_controls = ttk.Frame(controls_frame)
        right_controls.grid(row=0, column=1, sticky="e")

        self._btn_clear_all = ttk.Button(right_controls, text="Effacer tout", command=self._notify_clear_all)
        self._btn_clear_all.pack(side=tk.RIGHT)

        instruction_lf = ttk.LabelFrame(workflow_instruction_frame, text="Instruction")
        instruction_lf.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        instruction_lf.columnconfigure(0, weight=1)
        instruction_lf.rowconfigure(1, weight=1)

        instruction_header = ttk.Frame(instruction_lf)
        instruction_header.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        instruction_header.columnconfigure(1, weight=1)

        ttk.Label(instruction_header, text="Type:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self._var_step_type = tk.StringVar(value="Sélectionner...")
        step_type_options = ["Sélectionner..."] + list(self._ADD_OPTIONS.keys())
        self._cmb_step_type = ttk.Combobox(
            instruction_header,
            textvariable=self._var_step_type,
            values=step_type_options,
            state="readonly",
            width=28,
        )
        self._cmb_step_type.grid(row=0, column=1, sticky="ew")
        self._cmb_step_type.bind("<<ComboboxSelected>>", self._on_instruction_type_changed)

        self._instruction_form_frame = ttk.Frame(instruction_lf)
        self._instruction_form_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        self._instruction_form_frame.columnconfigure(0, weight=1)

        instruction_footer = ttk.Frame(instruction_lf)
        instruction_footer.grid(row=2, column=0, sticky="ew", padx=8, pady=(4, 8))
        self._btn_add = ttk.Button(instruction_footer, text="Ajouter", command=self._notify_add_step)
        self._btn_add.pack(side=tk.RIGHT)

        self._render_instruction_form()

        # 4. Footer
        footer_frame = ttk.Frame(main_container)
        footer_frame.pack(fill=tk.X, expand=False, pady=(10, 0))

        self._btn_save = ttk.Button(footer_frame, text="Sauvegarder", command=self._notify_save)
        self._btn_save.pack(side=tk.RIGHT, padx=5)

        self._btn_cancel = ttk.Button(footer_frame, text="Annuler", command=self._notify_cancel)
        self._btn_cancel.pack(side=tk.RIGHT, padx=5)

    def set_callbacks(
        self,
        on_save: Callable[[Dict[str, Any]], None],
        on_cancel: Callable[[], None],
        on_add_step: Callable[[str, Any], None],
        on_edit_step: Callable[[int, str, Any], None],
        on_delete_step: Callable[[int], None],
        on_move_up: Callable[[int], None],
        on_move_down: Callable[[int], None],
        on_clear_all: Callable[[], None],
    ) -> None:
        """Sets the callbacks for internal operations.

        Args:
            on_save: Callback when trying to save the form.
            on_cancel: Callback when cancelling modifications.
        """
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._on_add_step = on_add_step
        self._on_edit_step = on_edit_step
        self._on_delete_step = on_delete_step
        self._on_move_up = on_move_up
        self._on_move_down = on_move_down
        self._on_clear_all = on_clear_all

    def load_data(self, data: Dict[str, Any]) -> None:
        """Loads data into the interface fields.

        Args:
            data: Dictionary of values to load.
        """
        self._var_guid.set(data.get("provider_guid", ""))
        self._var_name.set(data.get("provider_name", ""))
        self._var_url.set(data.get("url", ""))
        self._var_version.set(data.get("version", ""))
        self._var_browser.set(data.get("browser_displayed", True))
        self._var_obfuscated.set(data.get("automation_obfuscated", True))
        self._var_created.set(data.get("created_date", ""))
        self._var_modified.set(data.get("modified_date", ""))

    def get_data(self) -> Dict[str, Any]:
        """Reads data from the interface fields.

        Returns:
            Dictionary containing the current values in the form.
        """
        return {
            "provider_guid": self._var_guid.get(),
            "provider_name": self._var_name.get(),
            "url": self._var_url.get(),
            "version": self._var_version.get(),
            "browser_displayed": self._var_browser.get(),
            "automation_obfuscated": self._var_obfuscated.get(),
            "created_date": self._var_created.get(),
            "modified_date": self._var_modified.get()
        }

    def clear_data(self) -> None:
        """Clears all UI fields."""
        self._var_guid.set("")
        self._var_name.set("")
        self._var_url.set("")
        self._var_version.set("")
        self._var_browser.set(False)
        self._var_obfuscated.set(False)
        self._var_created.set("")
        self._var_modified.set("")
        self.render_steps([])

    def render_steps(self, workflow_items: list[Dict[str, Any]]) -> None:
        """Renders workflow steps in the ordered list component.

        Args:
            workflow_items: Ordered step items with label/type/value fields.
        """
        selected_index = self.get_selected_step_index()
        self._workflow_items = [dict(item) for item in workflow_items]
        self._list_steps.delete(0, tk.END)

        for item in self._workflow_items:
            self._list_steps.insert(tk.END, str(item.get("label", "")))

        if selected_index is not None and 0 <= selected_index < len(self._workflow_items):
            self._list_steps.selection_set(selected_index)

        self._update_step_buttons_state()

    def set_selected_step(self, index: int) -> None:
        """Selects a step row by index and refreshes button states."""
        self._list_steps.selection_clear(0, tk.END)
        if 0 <= index < self._list_steps.size():
            self._list_steps.selection_set(index)
            self._list_steps.activate(index)
            self._list_steps.see(index)
        self._update_step_buttons_state()

    def get_selected_step_index(self) -> Optional[int]:
        """Returns the currently selected workflow index, if any."""
        curselection_func = cast(Callable[[], tuple[int, ...]], getattr(self._list_steps, "curselection"))
        selected = curselection_func()
        if not selected:
            return None
        return selected[0]

    def ask_overwrite_confirmation(self) -> bool:
        """Shows a popup asking if the user wants to overwrite an existing file.

        Returns:
            True if the user confirmed, False otherwise.
        """
        return messagebox.askyesno("Écraser?", "Un fournisseur avec ce GUID existe déjà. Voulez-vous l'écraser ?")

    def show_error(self, message: str) -> None:
        """Shows an error message popup.
        
        Args:
            message: The message to tell the user.
        """
        messagebox.showerror("Erreur", message)

    def _notify_save(self) -> None:
        if self._on_save:
            self._on_save(self.get_data())

    def _notify_cancel(self) -> None:
        if self._on_cancel:
            self._on_cancel()

    def _on_step_selection_changed(self, _event: tk.Event[tk.Widget]) -> None:
        """Handles list selection changes to update command button states."""
        self._update_step_buttons_state()

    def _update_step_buttons_state(self) -> None:
        """Enables or disables action buttons based on current selection."""
        selected_index = self.get_selected_step_index()
        total_steps = len(self._workflow_items)

        self._btn_edit_step.config(state=tk.NORMAL if selected_index is not None else tk.DISABLED)
        self._btn_delete_step.config(state=tk.NORMAL if selected_index is not None else tk.DISABLED)

        can_move_up = selected_index is not None and selected_index > 0
        can_move_down = selected_index is not None and selected_index < total_steps - 1
        self._btn_move_up.config(state=tk.NORMAL if can_move_up else tk.DISABLED)
        self._btn_move_down.config(state=tk.NORMAL if can_move_down else tk.DISABLED)

    def _notify_add_step(self) -> None:
        """Starts workflow-step creation from selected dropdown type."""
        selected_label = self._var_step_type.get()
        step_type = self._ADD_OPTIONS.get(selected_label)
        if step_type is None:
            self.show_error("Veuillez sélectionner un type d'étape avant d'ajouter.")
            return

        is_valid, step_value = self._collect_instruction_value(step_type)
        if not is_valid:
            return

        if self._on_add_step:
            self._on_add_step(step_type, step_value)

    def _on_instruction_type_changed(self, _event: tk.Event[tk.Widget]) -> None:
        """Updates inline instruction form based on selected step type."""
        self._render_instruction_form()

    def _render_instruction_form(self) -> None:
        """Renders in-place controls for the currently selected add-step type."""
        for child in self._instruction_form_frame.winfo_children():
            child.destroy()

        self._instruction_form_vars = {}
        selected_label = self._var_step_type.get()
        step_type = self._ADD_OPTIONS.get(selected_label)

        if step_type is None:
            ttk.Label(
                self._instruction_form_frame,
                text="Sélectionnez un type d'étape pour afficher ses paramètres.",
            ).grid(row=0, column=0, sticky="w")
            return

        form = self._instruction_form_frame
        form.columnconfigure(1, weight=1)

        if step_type == "open_url":
            ttk.Label(form, text="URL:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
            url_var = tk.StringVar()
            ttk.Entry(form, textvariable=url_var).grid(row=0, column=1, sticky="ew", pady=(0, 8))
            self._instruction_form_vars = {"url": url_var}

        elif step_type == "wait_seconds":
            ttk.Label(form, text="Durée:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
            amount_var = tk.StringVar(value="")
            ttk.Entry(form, textvariable=amount_var, width=20).grid(row=0, column=1, sticky="w", pady=(0, 8))

            ttk.Label(form, text="Unité:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
            unit_var = tk.StringVar(value="seconde")
            ttk.Combobox(
                form,
                textvariable=unit_var,
                values=["heure", "minute", "seconde", "milli-sec"],
                state="readonly",
                width=18,
            ).grid(row=1, column=1, sticky="w", pady=(0, 8))

            self._instruction_form_vars = {
                "amount": amount_var,
                "unit": unit_var,
            }

        elif step_type == "refresh_page":
            ttk.Label(form, text="Cette étape rafraîchira la page active.").grid(
                row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
            )
            clear_cache_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(
                form,
                text="Vider le cache avant rafraîchissement",
                variable=clear_cache_var,
            ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))

            self._instruction_form_vars = {"clear_cache": clear_cache_var}

        elif step_type == "download_image":
            ttk.Label(form, text="Mode de téléchargement:").grid(
                row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8)
            )

            mode_var = tk.StringVar(value="largest")
            min_width_var = tk.StringVar(value="0")
            min_height_var = tk.StringVar(value="0")
            max_width_var = tk.StringVar(value="0")
            max_height_var = tk.StringVar(value="0")

            ttk.Radiobutton(form, text="La plus grande image", variable=mode_var, value="largest").grid(
                row=0, column=1, sticky="w", pady=(0, 4)
            )
            ttk.Radiobutton(form, text="La première image", variable=mode_var, value="first").grid(
                row=1, column=1, sticky="w", pady=(0, 4)
            )
            ttk.Radiobutton(form, text="Toutes les images", variable=mode_var, value="all").grid(
                row=2, column=1, sticky="w", pady=(0, 8)
            )

            ttk.Label(form, text="Largeur min (W):").grid(
                row=3, column=0, sticky="w", padx=(0, 8), pady=(0, 8)
            )
            ttk.Entry(form, textvariable=min_width_var, width=16).grid(row=3, column=1, sticky="w", pady=(0, 8))

            ttk.Label(form, text="Hauteur min (H):").grid(
                row=4, column=0, sticky="w", padx=(0, 8), pady=(0, 8)
            )
            ttk.Entry(form, textvariable=min_height_var, width=16).grid(row=4, column=1, sticky="w", pady=(0, 8))

            ttk.Label(form, text="Largeur max (W):").grid(
                row=5, column=0, sticky="w", padx=(0, 8), pady=(0, 8)
            )
            ttk.Entry(form, textvariable=max_width_var, width=16).grid(row=5, column=1, sticky="w", pady=(0, 8))

            ttk.Label(form, text="Hauteur max (H):").grid(
                row=6, column=0, sticky="w", padx=(0, 8), pady=(0, 8)
            )
            ttk.Entry(form, textvariable=max_height_var, width=16).grid(row=6, column=1, sticky="w", pady=(0, 8))

            self._instruction_form_vars = {
                "mode": mode_var,
                "min_width": min_width_var,
                "min_height": min_height_var,
                "max_width": max_width_var,
                "max_height": max_height_var,
            }

        elif step_type == "check_if_image_here":
            ttk.Label(form, text="W1:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
            ttk.Label(form, text="W2:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
            ttk.Label(form, text="H1:").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
            ttk.Label(form, text="H2:").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(0, 8))

            w1_var = tk.StringVar(value="0")
            w2_var = tk.StringVar(value="0")
            h1_var = tk.StringVar(value="0")
            h2_var = tk.StringVar(value="0")

            ttk.Entry(form, textvariable=w1_var, width=16).grid(row=0, column=1, sticky="w", pady=(0, 8))
            ttk.Entry(form, textvariable=w2_var, width=16).grid(row=1, column=1, sticky="w", pady=(0, 8))
            ttk.Entry(form, textvariable=h1_var, width=16).grid(row=2, column=1, sticky="w", pady=(0, 8))
            ttk.Entry(form, textvariable=h2_var, width=16).grid(row=3, column=1, sticky="w", pady=(0, 8))

            ttk.Label(form, text="Condition: W1 < X < W2 et H1 < Y < H2").grid(
                row=4, column=0, columnspan=2, sticky="w", pady=(0, 8)
            )

            self._instruction_form_vars = {
                "w1": w1_var,
                "w2": w2_var,
                "h1": h1_var,
                "h2": h2_var,
            }

        elif step_type == "click_element":
            ttk.Label(form, text="Sélecteur CSS:").grid(
                row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8)
            )

            selector_var = tk.StringVar(value="")
            ttk.Entry(form, textvariable=selector_var).grid(row=0, column=1, sticky="ew", pady=(0, 8))

            normal_var = tk.BooleanVar(value=True)
            forced_var = tk.BooleanVar(value=False)
            js_direct_var = tk.BooleanVar(value=False)
            verify_present_var = tk.BooleanVar(value=False)

            ttk.Checkbutton(form, text="Normal", variable=normal_var).grid(
                row=1, column=0, columnspan=2, sticky="w", pady=(0, 4)
            )
            ttk.Checkbutton(form, text="Forced", variable=forced_var).grid(
                row=2, column=0, columnspan=2, sticky="w", pady=(0, 4)
            )
            ttk.Checkbutton(form, text="JS Direct", variable=js_direct_var).grid(
                row=3, column=0, columnspan=2, sticky="w", pady=(0, 4)
            )
            ttk.Checkbutton(form, text="Vérifier présent du bouton", variable=verify_present_var).grid(
                row=4, column=0, columnspan=2, sticky="w", pady=(0, 8)
            )

            self._instruction_form_vars = {
                "selector": selector_var,
                "normal": normal_var,
                "forced": forced_var,
                "js_direct": js_direct_var,
                "verify_present": verify_present_var,
            }

    def _collect_instruction_value(self, step_type: str) -> tuple[bool, Any]:
        """Reads and validates inline form values for selected add-step type."""
        if step_type == "open_url":
            url_var = cast(tk.StringVar, self._instruction_form_vars.get("url"))
            value = url_var.get().strip()
            if not value:
                self.show_error("La valeur URL est obligatoire.")
                return False, None
            return True, value

        if step_type == "wait_seconds":
            amount_var = cast(tk.StringVar, self._instruction_form_vars.get("amount"))
            unit_var = cast(tk.StringVar, self._instruction_form_vars.get("unit"))
            amount_raw = amount_var.get().strip()
            if not amount_raw:
                self.show_error("La durée est obligatoire.")
                return False, None
            if not amount_raw.isdigit() or int(amount_raw) <= 0:
                self.show_error("La durée doit être un entier positif.")
                return False, None

            unit_display_to_token = {
                "heure": "hours",
                "minute": "minutes",
                "seconde": "seconds",
                "milli-sec": "milliseconds",
            }
            selected_unit_display = unit_var.get()
            selected_unit_token = unit_display_to_token.get(selected_unit_display, "seconds")

            return True, {
                "amount": int(amount_raw),
                "unit": selected_unit_token,
            }

        if step_type == "refresh_page":
            clear_cache_var = cast(tk.BooleanVar, self._instruction_form_vars.get("clear_cache"))
            return True, clear_cache_var.get()

        if step_type == "download_image":
            mode_var = cast(tk.StringVar, self._instruction_form_vars.get("mode"))
            min_width_var = cast(tk.StringVar, self._instruction_form_vars.get("min_width"))
            min_height_var = cast(tk.StringVar, self._instruction_form_vars.get("min_height"))
            max_width_var = cast(tk.StringVar, self._instruction_form_vars.get("max_width"))
            max_height_var = cast(tk.StringVar, self._instruction_form_vars.get("max_height"))

            min_width = self._parse_non_negative_int(min_width_var.get(), "La largeur minimale")
            if min_width is None:
                return False, None
            min_height = self._parse_non_negative_int(min_height_var.get(), "La hauteur minimale")
            if min_height is None:
                return False, None
            max_width = self._parse_non_negative_int(max_width_var.get(), "La largeur maximale")
            if max_width is None:
                return False, None
            max_height = self._parse_non_negative_int(max_height_var.get(), "La hauteur maximale")
            if max_height is None:
                return False, None

            return True, {
                "mode": mode_var.get(),
                "min_width": min_width,
                "min_height": min_height,
                "max_width": max_width,
                "max_height": max_height,
            }

        if step_type == "check_if_image_here":
            w1_var = cast(tk.StringVar, self._instruction_form_vars.get("w1"))
            w2_var = cast(tk.StringVar, self._instruction_form_vars.get("w2"))
            h1_var = cast(tk.StringVar, self._instruction_form_vars.get("h1"))
            h2_var = cast(tk.StringVar, self._instruction_form_vars.get("h2"))

            w1 = self._parse_int(w1_var.get(), "W1")
            if w1 is None:
                return False, None
            w2 = self._parse_int(w2_var.get(), "W2")
            if w2 is None:
                return False, None
            h1 = self._parse_int(h1_var.get(), "H1")
            if h1 is None:
                return False, None
            h2 = self._parse_int(h2_var.get(), "H2")
            if h2 is None:
                return False, None

            if w1 >= w2:
                self.show_error("W1 doit être strictement inférieur à W2.")
                return False, None
            if h1 >= h2:
                self.show_error("H1 doit être strictement inférieur à H2.")
                return False, None

            return True, {"w1": w1, "w2": w2, "h1": h1, "h2": h2}

        if step_type == "click_element":
            selector_var = cast(tk.StringVar, self._instruction_form_vars.get("selector"))
            normal_var = cast(tk.BooleanVar, self._instruction_form_vars.get("normal"))
            forced_var = cast(tk.BooleanVar, self._instruction_form_vars.get("forced"))
            js_direct_var = cast(tk.BooleanVar, self._instruction_form_vars.get("js_direct"))
            verify_present_var = cast(tk.BooleanVar, self._instruction_form_vars.get("verify_present"))

            selector = selector_var.get().strip()
            if not selector:
                self.show_error("Le sélecteur CSS est obligatoire.")
                return False, None

            normal = normal_var.get()
            forced = forced_var.get()
            js_direct = js_direct_var.get()
            if not (normal or forced or js_direct):
                self.show_error("Sélectionnez au moins un mode de clic (Normal, Forced ou JS Direct).")
                return False, None

            return True, {
                "selector": selector,
                "normal": normal,
                "forced": forced,
                "js_direct": js_direct,
                "verify_present": verify_present_var.get(),
            }

        self.show_error("Type d'étape invalide.")
        return False, None

    def _parse_non_negative_int(self, raw: str, label: str) -> Optional[int]:
        """Parses an integer >= 0 from user input string."""
        value = raw.strip()
        if not value:
            self.show_error(f"{label} est obligatoire.")
            return None
        if not value.isdigit():
            self.show_error(f"{label} doit être un entier >= 0.")
            return None
        return int(value)

    def _parse_int(self, raw: str, label: str) -> Optional[int]:
        """Parses a signed integer from user input string."""
        value = raw.strip()
        if not value:
            self.show_error(f"{label} est obligatoire.")
            return None
        if value.startswith("-"):
            if not value[1:].isdigit():
                self.show_error(f"{label} doit être un entier.")
                return None
        elif not value.isdigit():
            self.show_error(f"{label} doit être un entier.")
            return None
        return int(value)

    def _notify_edit_step(self) -> None:
        """Opens the selected step in an edit dialog."""
        selected_index = self.get_selected_step_index()
        if selected_index is None or selected_index < 0 or selected_index >= len(self._workflow_items):
            return

        item = self._workflow_items[selected_index]
        raw_type = item.get("type")
        if not isinstance(raw_type, str):
            self.show_error("Type d'étape invalide.")
            return

        submitted, dialog_value = self._open_step_dialog(step_type=raw_type, initial_value=item.get("value"))
        if not submitted:
            return

        if self._on_edit_step:
            self._on_edit_step(selected_index, raw_type, dialog_value)

    def _notify_delete_step(self) -> None:
        """Deletes the currently selected workflow step."""
        selected_index = self.get_selected_step_index()
        if selected_index is None:
            return
        if self._on_delete_step:
            self._on_delete_step(selected_index)

    def _notify_move_up(self) -> None:
        """Requests moving the selected step upward."""
        selected_index = self.get_selected_step_index()
        if selected_index is None:
            return
        if self._on_move_up:
            self._on_move_up(selected_index)

    def _notify_move_down(self) -> None:
        """Requests moving the selected step downward."""
        selected_index = self.get_selected_step_index()
        if selected_index is None:
            return
        if self._on_move_down:
            self._on_move_down(selected_index)

    def _notify_clear_all(self) -> None:
        """Clears every workflow step after user confirmation."""
        if not self._workflow_items:
            return
        should_clear = messagebox.askyesno("Effacer", "Voulez-vous supprimer toutes les étapes du workflow ?")
        if not should_clear:
            return
        if self._on_clear_all:
            self._on_clear_all()

    def _open_step_dialog(self, step_type: str, initial_value: Any = None) -> tuple[bool, Any]:
        """Opens a modal dialog adapted to the specified step type.

        Args:
            step_type: Workflow step type identifier.
            initial_value: Existing value used when editing.

        Returns:
            A tuple where the first value indicates if submit was confirmed.
            The second value is the normalized step value.
        """
        if step_type not in self._TYPE_TO_LABEL:
            self.show_error("Type d'étape invalide.")
            return False, None

        dialog = tk.Toplevel(self)
        dialog.title(self._TYPE_TO_LABEL[step_type])
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.resizable(False, False)

        content = ttk.Frame(dialog, padding=12)
        content.pack(fill=tk.BOTH, expand=True)

        result: Dict[str, Any] = {"value": None, "submitted": False}

        if step_type == "open_url":
            ttk.Label(content, text="URL:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
            url_var = tk.StringVar(value=str(initial_value) if initial_value is not None else "")
            url_entry = ttk.Entry(content, textvariable=url_var, width=50)
            url_entry.grid(row=0, column=1, sticky="ew", pady=(0, 8))
            url_entry.focus_set()

            def submit() -> None:
                value = url_var.get().strip()
                if not value:
                    messagebox.showerror("Erreur", "La valeur URL est obligatoire.", parent=dialog)
                    return
                result["value"] = value
                result["submitted"] = True
                dialog.destroy()

        elif step_type == "wait_seconds":
            ttk.Label(content, text="Durée:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))

            initial_amount = ""
            initial_unit_token = "seconds"
            if isinstance(initial_value, dict):
                initial_config = cast(dict[str, Any], initial_value)
                initial_amount = str(initial_config.get("amount", ""))
                initial_unit_token = str(initial_config.get("unit", "seconds"))
            elif initial_value is not None:
                initial_amount = str(initial_value)

            wait_var = tk.StringVar(value=initial_amount)
            wait_entry = ttk.Entry(content, textvariable=wait_var, width=20)
            wait_entry.grid(row=0, column=1, sticky="w", pady=(0, 8))
            wait_entry.focus_set()

            ttk.Label(content, text="Unité:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 8))

            unit_display_to_token = {
                "heure": "hours",
                "minute": "minutes",
                "seconde": "seconds",
                "milli-sec": "milliseconds",
            }
            unit_token_to_display = {value: key for key, value in unit_display_to_token.items()}
            default_display = unit_token_to_display.get(initial_unit_token, "seconde")
            wait_unit_var = tk.StringVar(value=default_display)
            wait_unit_combo = ttk.Combobox(
                content,
                textvariable=wait_unit_var,
                values=list(unit_display_to_token.keys()),
                state="readonly",
                width=18,
            )
            wait_unit_combo.grid(row=1, column=1, sticky="w", pady=(0, 8))

            def submit() -> None:
                value = wait_var.get().strip()
                if not value:
                    messagebox.showerror("Erreur", "La durée est obligatoire.", parent=dialog)
                    return
                if not value.isdigit() or int(value) <= 0:
                    messagebox.showerror("Erreur", "La durée doit être un entier positif.", parent=dialog)
                    return

                selected_unit_display = wait_unit_var.get()
                selected_unit_token = unit_display_to_token.get(selected_unit_display, "seconds")

                result["value"] = {
                    "amount": int(value),
                    "unit": selected_unit_token,
                }
                result["submitted"] = True
                dialog.destroy()

        elif step_type == "refresh_page":
            ttk.Label(content, text="Cette étape rafraîchira la page active.").grid(
                row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
            )

            default_clear_cache = bool(initial_value)
            clear_cache_var = tk.BooleanVar(value=default_clear_cache)
            ttk.Checkbutton(
                content,
                text="Vider le cache avant rafraîchissement",
                variable=clear_cache_var,
            ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))

            def submit() -> None:
                result["value"] = clear_cache_var.get()
                result["submitted"] = True
                dialog.destroy()

        elif step_type == "download_image":
            ttk.Label(content, text="Mode de téléchargement:").grid(
                row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8)
            )

            initial_mode = "largest"
            initial_min_width = "0"
            initial_min_height = "0"
            initial_max_width = "0"
            initial_max_height = "0"
            if isinstance(initial_value, dict):
                initial_config = cast(dict[str, Any], initial_value)
                initial_mode = str(initial_config.get("mode", "largest"))
                initial_min_width = str(initial_config.get("min_width", 0))
                initial_min_height = str(initial_config.get("min_height", 0))
                initial_max_width = str(initial_config.get("max_width", 0))
                initial_max_height = str(initial_config.get("max_height", 0))

            mode_var = tk.StringVar(value=initial_mode if initial_mode in {"largest", "first", "all"} else "largest")
            min_width_var = tk.StringVar(value=initial_min_width)
            min_height_var = tk.StringVar(value=initial_min_height)
            max_width_var = tk.StringVar(value=initial_max_width)
            max_height_var = tk.StringVar(value=initial_max_height)

            ttk.Radiobutton(content, text="La plus grande image", variable=mode_var, value="largest").grid(
                row=0, column=1, sticky="w", pady=(0, 4)
            )
            ttk.Radiobutton(content, text="La première image", variable=mode_var, value="first").grid(
                row=1, column=1, sticky="w", pady=(0, 4)
            )
            ttk.Radiobutton(content, text="Toutes les images", variable=mode_var, value="all").grid(
                row=2, column=1, sticky="w", pady=(0, 8)
            )

            ttk.Label(content, text="Largeur min (W):").grid(
                row=3, column=0, sticky="w", padx=(0, 8), pady=(0, 8)
            )
            min_width_entry = ttk.Entry(content, textvariable=min_width_var, width=16)
            min_width_entry.grid(row=3, column=1, sticky="w", pady=(0, 8))

            ttk.Label(content, text="Hauteur min (H):").grid(
                row=4, column=0, sticky="w", padx=(0, 8), pady=(0, 8)
            )
            min_height_entry = ttk.Entry(content, textvariable=min_height_var, width=16)
            min_height_entry.grid(row=4, column=1, sticky="w", pady=(0, 8))

            ttk.Label(content, text="Largeur max (W):").grid(
                row=5, column=0, sticky="w", padx=(0, 8), pady=(0, 8)
            )
            max_width_entry = ttk.Entry(content, textvariable=max_width_var, width=16)
            max_width_entry.grid(row=5, column=1, sticky="w", pady=(0, 8))

            ttk.Label(content, text="Hauteur max (H):").grid(
                row=6, column=0, sticky="w", padx=(0, 8), pady=(0, 8)
            )
            max_height_entry = ttk.Entry(content, textvariable=max_height_var, width=16)
            max_height_entry.grid(row=6, column=1, sticky="w", pady=(0, 8))

            def parse_non_negative_int(raw: str, label: str) -> Optional[int]:
                value = raw.strip()
                if not value:
                    messagebox.showerror("Erreur", f"{label} est obligatoire.", parent=dialog)
                    return None
                if not value.isdigit():
                    messagebox.showerror("Erreur", f"{label} doit être un entier >= 0.", parent=dialog)
                    return None
                return int(value)

            def submit() -> None:
                mode = mode_var.get()
                min_width = parse_non_negative_int(min_width_var.get(), "La largeur minimale")
                if min_width is None:
                    return
                min_height = parse_non_negative_int(min_height_var.get(), "La hauteur minimale")
                if min_height is None:
                    return
                max_width = parse_non_negative_int(max_width_var.get(), "La largeur maximale")
                if max_width is None:
                    return
                max_height = parse_non_negative_int(max_height_var.get(), "La hauteur maximale")
                if max_height is None:
                    return

                result["value"] = {
                    "mode": mode,
                    "min_width": min_width,
                    "min_height": min_height,
                    "max_width": max_width,
                    "max_height": max_height,
                }
                result["submitted"] = True
                dialog.destroy()

        elif step_type == "check_if_image_here":
            ttk.Label(content, text="W1:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
            ttk.Label(content, text="W2:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
            ttk.Label(content, text="H1:").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
            ttk.Label(content, text="H2:").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(0, 8))

            init_w1 = "0"
            init_w2 = "0"
            init_h1 = "0"
            init_h2 = "0"
            if isinstance(initial_value, dict):
                initial_config = cast(dict[str, Any], initial_value)
                init_w1 = str(initial_config.get("w1", 0))
                init_w2 = str(initial_config.get("w2", 0))
                init_h1 = str(initial_config.get("h1", 0))
                init_h2 = str(initial_config.get("h2", 0))

            w1_var = tk.StringVar(value=init_w1)
            w2_var = tk.StringVar(value=init_w2)
            h1_var = tk.StringVar(value=init_h1)
            h2_var = tk.StringVar(value=init_h2)

            ttk.Entry(content, textvariable=w1_var, width=16).grid(row=0, column=1, sticky="w", pady=(0, 8))
            ttk.Entry(content, textvariable=w2_var, width=16).grid(row=1, column=1, sticky="w", pady=(0, 8))
            ttk.Entry(content, textvariable=h1_var, width=16).grid(row=2, column=1, sticky="w", pady=(0, 8))
            ttk.Entry(content, textvariable=h2_var, width=16).grid(row=3, column=1, sticky="w", pady=(0, 8))

            ttk.Label(content, text="Condition: W1 < X < W2 et H1 < Y < H2").grid(
                row=4, column=0, columnspan=2, sticky="w", pady=(0, 8)
            )

            def parse_int(raw: str, label: str) -> Optional[int]:
                value = raw.strip()
                if not value:
                    messagebox.showerror("Erreur", f"{label} est obligatoire.", parent=dialog)
                    return None
                if value.startswith("-"):
                    if not value[1:].isdigit():
                        messagebox.showerror("Erreur", f"{label} doit être un entier.", parent=dialog)
                        return None
                elif not value.isdigit():
                    messagebox.showerror("Erreur", f"{label} doit être un entier.", parent=dialog)
                    return None
                return int(value)

            def submit() -> None:
                w1 = parse_int(w1_var.get(), "W1")
                if w1 is None:
                    return
                w2 = parse_int(w2_var.get(), "W2")
                if w2 is None:
                    return
                h1 = parse_int(h1_var.get(), "H1")
                if h1 is None:
                    return
                h2 = parse_int(h2_var.get(), "H2")
                if h2 is None:
                    return

                if w1 >= w2:
                    messagebox.showerror("Erreur", "W1 doit être strictement inférieur à W2.", parent=dialog)
                    return
                if h1 >= h2:
                    messagebox.showerror("Erreur", "H1 doit être strictement inférieur à H2.", parent=dialog)
                    return

                result["value"] = {"w1": w1, "w2": w2, "h1": h1, "h2": h2}
                result["submitted"] = True
                dialog.destroy()

        elif step_type == "click_element":
            ttk.Label(content, text="Sélecteur CSS:").grid(
                row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8)
            )

            initial_selector = ""
            initial_normal = True
            initial_forced = False
            initial_js_direct = False
            initial_verify_present = False

            if isinstance(initial_value, dict):
                initial_config = cast(dict[str, Any], initial_value)
                initial_selector = str(initial_config.get("selector", ""))
                initial_normal = bool(initial_config.get("normal", True))
                initial_forced = bool(initial_config.get("forced", False))
                initial_js_direct = bool(initial_config.get("js_direct", False))
                initial_verify_present = bool(initial_config.get("verify_present", False))
            elif initial_value is not None:
                initial_selector = str(initial_value)

            selector_var = tk.StringVar(value=initial_selector)
            selector_entry = ttk.Entry(content, textvariable=selector_var, width=50)
            selector_entry.grid(row=0, column=1, sticky="ew", pady=(0, 8))
            selector_entry.focus_set()

            normal_var = tk.BooleanVar(value=initial_normal)
            forced_var = tk.BooleanVar(value=initial_forced)
            js_direct_var = tk.BooleanVar(value=initial_js_direct)
            verify_present_var = tk.BooleanVar(value=initial_verify_present)

            ttk.Checkbutton(content, text="Normal", variable=normal_var).grid(
                row=1, column=0, columnspan=2, sticky="w", pady=(0, 4)
            )
            ttk.Checkbutton(content, text="Forced", variable=forced_var).grid(
                row=2, column=0, columnspan=2, sticky="w", pady=(0, 4)
            )
            ttk.Checkbutton(content, text="JS Direct", variable=js_direct_var).grid(
                row=3, column=0, columnspan=2, sticky="w", pady=(0, 4)
            )
            ttk.Checkbutton(content, text="Vérifier présent du bouton", variable=verify_present_var).grid(
                row=4, column=0, columnspan=2, sticky="w", pady=(0, 8)
            )

            def submit() -> None:
                selector = selector_var.get().strip()
                if not selector:
                    messagebox.showerror("Erreur", "Le sélecteur CSS est obligatoire.", parent=dialog)
                    return

                normal = normal_var.get()
                forced = forced_var.get()
                js_direct = js_direct_var.get()
                if not (normal or forced or js_direct):
                    messagebox.showerror(
                        "Erreur",
                        "Sélectionnez au moins un mode de clic (Normal, Forced ou JS Direct).",
                        parent=dialog,
                    )
                    return

                result["value"] = {
                    "selector": selector,
                    "normal": normal,
                    "forced": forced,
                    "js_direct": js_direct,
                    "verify_present": verify_present_var.get(),
                }
                result["submitted"] = True
                dialog.destroy()

        else:
            self.show_error("Type d'étape invalide.")
            dialog.destroy()
            return False, None

        content.columnconfigure(1, weight=1)
        content.rowconfigure(98, weight=1)

        buttons = ttk.Frame(content)
        buttons.grid(row=99, column=0, columnspan=2, sticky="sew")

        ttk.Button(buttons, text="Annuler", command=dialog.destroy).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(buttons, text="Valider", command=submit).pack(side=tk.RIGHT)

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        self.wait_window(dialog)

        if not bool(result["submitted"]):
            return False, None
        return True, result["value"]
