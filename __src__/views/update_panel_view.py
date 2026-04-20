import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
from typing import Any, Optional, Callable, Dict

from controllers.update_controller import UpdateController
from models.config_aspirabot_model import ConfigAspirabotModel
from view_models.update_view_model import UpdateViewModel
from enum import Enum

class WorkflowAction(str, Enum):
    FIND_ELEMENT = "FIND_ELEMENT"
    CLICK = "CLICK"
    DOWNLOAD_IMAGE = "DOWNLOAD_IMAGE"
    WAIT = "WAIT"
    EXTRACT_TEXT = "EXTRACT_TEXT"
    CLOSE_OTHER_TABS = "CLOSE_OTHER_TABS"

class ActionSelectionDialog:
    def __init__(self, parent: tk.Misc, title: str):
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.transient(parent) # type: ignore
        self.top.grab_set()
        self.top.lift() # type: ignore
        self.top.focus_force()

        self.selected_action: Optional[WorkflowAction] = None

        ttk.Label(self.top, text="Choisissez une action :").pack(padx=20, pady=10)

        self.action_var = tk.StringVar()
        self.combo = ttk.Combobox(self.top, textvariable=self.action_var, state="readonly", width=40)
        self.combo['values'] = [a.value for a in WorkflowAction]
        self.combo.current(0)
        self.combo.pack(padx=20, pady=5)

        btn_frame = ttk.Frame(self.top)
        btn_frame.pack(fill="x", padx=20, pady=10)

        ttk.Button(btn_frame, text="Valider", command=self._on_ok).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Annuler", command=self._on_cancel).pack(side="right", padx=5)

        self.top.wait_window()

    def _on_ok(self) -> None:
        self.selected_action = WorkflowAction(self.action_var.get())
        self.top.destroy()

    def _on_cancel(self) -> None:
        self.top.destroy()

class UpdatePanelView(ttk.Frame):
    """Vue pour la mise à jour de fournisseurs."""

    def __init__(self, parent: tk.Misc, app_config: ConfigAspirabotModel, on_provider_saved: Optional[Callable[[], None]] = None, on_action_complete: Optional[Callable[[], None]] = None, **kwargs: Any):
        super().__init__(parent, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.controller = UpdateController(app_config)
        self._current_view_model: UpdateViewModel = UpdateViewModel()
        self.on_provider_saved = on_provider_saved
        self.on_action_complete = on_action_complete
        self._selected_provider: Optional[str] = None
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialise les composants de l'interface."""
        # Top Frame: Formulaire
        _frame_top_form = ttk.LabelFrame(self, text="Informations")
        _frame_top_form.pack(fill="x", padx=10, pady=10)
        self.form_frame = _frame_top_form

        # ligne 1
        ttk.Label(_frame_top_form, text="Fichier :").grid(row=0, column=0, sticky="e", padx=(10, 0))
        self._filename_entry = ttk.Entry(_frame_top_form, textvariable=self._current_view_model.provider_filename, state="disabled")
        self._filename_entry.grid(row=0, column=1, sticky="w", ipadx=75, padx=(5, 10), pady=10)

        ttk.Label(_frame_top_form, text="Nom :").grid(row=0, column=2, sticky="e")
        ttk.Entry(_frame_top_form, textvariable=self._current_view_model.provider_alias).grid(row=0, column=3, sticky="w", ipadx=25, padx=(5, 10), pady=10)

        ttk.Label(_frame_top_form, text="Date de création :").grid(row=0, column=4, sticky="e")
        ttk.Entry(_frame_top_form, textvariable=self._current_view_model.created_date).grid(row=0, column=5, sticky="w", padx=(5, 10))

        ttk.Label(_frame_top_form, text="Version :").grid(row=0, column=6, sticky="e")
        ttk.Entry(_frame_top_form, textvariable=self._current_view_model.version, width=5).grid(row=0, column=7, sticky="w", padx=(5, 10))

        # ligne 2
        ttk.Label(_frame_top_form, text="URL :").grid(row=1, column=0, sticky="e", pady=(0, 10))
        ttk.Entry(_frame_top_form, textvariable=self._current_view_model.url).grid(row=1, column=1, columnspan=3, sticky="we", padx=(5, 10), pady=(0, 10))

        ttk.Checkbutton(_frame_top_form, text="Browser caché (Headless)", variable=self._current_view_model.headless).grid(row=1, column=5, columnspan=2, sticky="w", pady=(0, 10))

        # Configuration des poids de colonnes pour une meilleure répartition de l'espace
        for col in range(8):
            _frame_top_form.columnconfigure(col, weight=0)
        _frame_top_form.columnconfigure(1, weight=1)
        _frame_top_form.columnconfigure(3, weight=1)
        _frame_top_form.columnconfigure(5, weight=1)

        # Traces pour calculer dynamiquement le nom de fichier
        self._current_view_model.provider_alias.trace_add("write", self._on_filename_dependency_changed)
        self._current_view_model.created_date.trace_add("write", self._on_filename_dependency_changed)

        # Bottom Frame: Workflow Editor
        workflow_frame = ttk.LabelFrame(self, text="Workflow")
        workflow_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.workflow_frame = workflow_frame

        self.steps_listbox = tk.Listbox(workflow_frame, height=10)
        self.steps_listbox.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = ttk.Frame(workflow_frame)
        btn_frame.pack(fill="x")

        ttk.Button(btn_frame, text="Ajouter", command=self._add_step).pack(side="left", padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text="Supprimer", command=self._remove_step).pack(side="left", padx=(0, 10), pady=(0, 10))
        ttk.Button(btn_frame, text="Monter", command=self._move_up).pack(side="left", padx=(0, 10), pady=(0, 10))
        ttk.Button(btn_frame, text="Descendre", command=self._move_down).pack(side="left", padx=(0, 10), pady=(0, 10))

        # Bottom Frame: Actions
        self.action_frame = ttk.Frame(self)
        self.action_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(self.action_frame, text="Annuler modifications", command=self._reset_form).pack(side="left")
        ttk.Button(self.action_frame, text="Sauvegarder modifications", command=self._save_form).pack(side="right")

        self._set_form_state("disabled")

    def _set_form_state(self, state: str) -> None:
        def change_state(widget: tk.Misc) -> None:
            try:
                # Ne pas changer l'état du champ calculé s'il doit rester gris/désactivé
                # (on force 'disabled' si l'état désiré est 'normal')
                if getattr(self, '_filename_entry', None) is widget and state == "normal":
                    widget.configure(state="disabled")  # type: ignore
                else:
                    widget.configure(state=state)  # type: ignore
            except tk.TclError:
                pass
            for child in widget.winfo_children():
                change_state(child)

        change_state(self.form_frame)
        change_state(self.workflow_frame)
        change_state(self.action_frame)

    def _on_filename_dependency_changed(self, *args: Any) -> None:
        """Déclenché lorsque le nom ou la date changent, met à jour le nom du fichier."""
        # On passe par le contrôleur (qui utilise le service) pour la génération
        if hasattr(self.controller, 'update_filename_from_fields'):
            # Utilisation d'un flag pour éviter de déclencher l'événement en boucle si jamais
            self.controller.update_filename_from_fields(self._current_view_model)

    def _add_step(self) -> None:
        dialog = ActionSelectionDialog(self, "Ajouter une étape")
        if not dialog.selected_action:
            return
            
        action_type = dialog.selected_action.value
        step: Dict[str, Any] = {"type": action_type}
        
        if action_type in [WorkflowAction.FIND_ELEMENT, WorkflowAction.CLICK, WorkflowAction.EXTRACT_TEXT]:
            sel = simpledialog.askstring("Sélecteur", "Sélecteur CSS/XPath:", parent=self)
            step["selector"] = sel or ""
        if action_type == WorkflowAction.WAIT:
            t = simpledialog.askstring("Attendre", "Timeout (ms) ou Selecteur:", parent=self)
            if t and t.isdigit():
                step["timeout"] = int(t)
            else:
                step["selector"] = t or ""
        if action_type == WorkflowAction.EXTRACT_TEXT:
            v = simpledialog.askstring("Variable", "Nom de la variable:", parent=self)
            step["variable_name"] = v or "var1"
            
        self._current_view_model.steps.append(step)
        self._update_steps_list()

    def _remove_step(self) -> None:
        sel = self.steps_listbox.curselection() # type: ignore
        if sel:
            idx = int(str(sel[0])) # type: ignore
            del self._current_view_model.steps[idx]
            self._update_steps_list()

    def _move_up(self) -> None:
        sel = self.steps_listbox.curselection() # type: ignore
        if sel and int(str(sel[0])) > 0: # type: ignore
            idx = int(str(sel[0])) # type: ignore
            self._current_view_model.steps[idx], self._current_view_model.steps[idx-1] = self._current_view_model.steps[idx-1], self._current_view_model.steps[idx]
            self._update_steps_list()
            self.steps_listbox.selection_set(idx-1)

    def _move_down(self) -> None:
        sel = self.steps_listbox.curselection() # type: ignore
        if sel and hasattr(self._current_view_model, 'steps') and self._current_view_model.steps and int(str(sel[0])) < len(self._current_view_model.steps) - 1: # type: ignore
            idx = int(str(sel[0])) # type: ignore
            self._current_view_model.steps[idx], self._current_view_model.steps[idx+1] = self._current_view_model.steps[idx+1], self._current_view_model.steps[idx]
            self._update_steps_list()
            self.steps_listbox.selection_set(idx+1)

    def _update_steps_list(self) -> None:
        self.steps_listbox.delete(0, tk.END)
        if hasattr(self._current_view_model, 'steps') and self._current_view_model.steps:
            for step in self._current_view_model.steps:
                action_type = step.get('type')
                details = ", ".join(f"{k}={v}" for k, v in step.items() if k != "type")
                display_text = f"[{action_type}] {details}" if details else f"[{action_type}]"
                self.steps_listbox.insert(tk.END, display_text)

    def refresh_providers_list(self) -> None:
        """Met à jour la liste des fournisseurs (utile si le composant courant a été supprimé)."""
        providers = self.controller.get_providers_list()
        if self._selected_provider and self._selected_provider not in providers:
            self._selected_provider = None
            self._current_view_model.provider_alias.set("")
            self._current_view_model.url.set("")
            self._current_view_model.steps.clear()
            self._update_steps_list()
            self._set_form_state("disabled")

    def load_provider(self, provider_alias: str) -> None:
        """Charge les données d'un fournisseur spécifié pour la mise à jour."""
        self._selected_provider = provider_alias
        self._set_form_state("normal")
        try:
            self.controller.get_provider_view_model(provider_alias, self._current_view_model)
            self._update_steps_list()
            self.logger.debug(f"Données chargées pour {provider_alias}")
        except Exception as e:
            self.logger.error(f"Erreur au chargement de {provider_alias}: {e}")
            messagebox.showerror("Erreur", f"Erreur lors du chargement des données:\n{str(e)}")

    def load_default(self) -> None:
        """Prépare le formulaire pour une nouvelle création."""
        self._selected_provider = None
        self._set_form_state("normal")
        self.controller.load_default_view_model(self._current_view_model)
        self._update_steps_list()
        self.logger.debug("Données par défaut chargées pour création")

    def _reset_form(self) -> None:
        self._selected_provider = None
        self._current_view_model.provider_alias.set("")
        self._current_view_model.url.set("")
        self._current_view_model.steps.clear()
        self._update_steps_list()
        self._set_form_state("disabled")
        
        if self.on_action_complete:
            self.on_action_complete()

    def _save_form(self) -> None:
        errors = self._current_view_model.validate()
        if errors:
            messagebox.showwarning("Validation", "\n".join(errors))
            return
            
        try:
            selected = self._selected_provider
            if not selected:
                new_stem = self.controller.create_new_provider_from_view_model(self._current_view_model)
                self._selected_provider = new_stem
                messagebox.showinfo("Succès", f"Le fournisseur {new_stem} a été créé avec succès.")
                self.logger.info(f"Nouveau fournisseur créé : {new_stem}")
            else:
                new_stem = self.controller.save_provider_from_view_model(selected, self._current_view_model)
                if new_stem != selected:
                    self._selected_provider = new_stem
                messagebox.showinfo("Succès", f"Les données de {new_stem} ont été sauvegardées.")
                self.logger.info(f"Modifications sauvegardées pour {new_stem}")

            if self.on_provider_saved:
                self.on_provider_saved()
                
            if self.on_action_complete:
                self.on_action_complete()
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde:\n{str(e)}")
