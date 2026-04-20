import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
from typing import Any, Optional, Callable, Dict
from enum import Enum

from controllers.wysiwyg_controller import WysiwygController
from models.aspirabot_app_model import AspirabotAppModel
from view_models.wysiwyg_view_model import WysiwygViewModel

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

class WysiwygPanelView(ttk.Frame):
    """Vue pour l'édition de fournisseurs et du workflow."""

    def __init__(self, parent: tk.Misc, app_config: AspirabotAppModel, on_provider_saved: Optional[Callable[[], None]] = None, **kwargs: Any):
        super().__init__(parent, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.controller = WysiwygController(app_config)
        self._current_view_model: WysiwygViewModel = WysiwygViewModel()
        self.on_provider_saved = on_provider_saved
        self._init_ui()
        self.refresh_providers_list()

    def _init_ui(self) -> None:
        """Initialise les composants de l'interface."""
        # Top Frame: Selection
        top_frame = ttk.LabelFrame(self, text="Sélection du fournisseur")
        top_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(top_frame, text="Fournisseur :").pack(side="left", padx=5, pady=5)
        self.provider_combo = ttk.Combobox(top_frame, state="readonly")
        self.provider_combo.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        self.provider_combo.bind("<<ComboboxSelected>>", self._on_provider_selected)
        
        ttk.Button(top_frame, text="Créer un nouveau fournisseur", command=self._create_new_provider).pack(side="left", padx=5, pady=5)

        # PanedWindow pour diviser l'écran
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill="both", expand=True, padx=10, pady=5)

        # Left Frame: Formulaire
        form_frame = ttk.LabelFrame(self.paned, text="Détails (WYSIWYG)")
        self.paned.add(form_frame, weight=1) # type: ignore

        ttk.Label(form_frame, text="Nom :").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(form_frame, textvariable=self._current_view_model.provider_name).grid(row=0, column=1, sticky="w", padx=5, pady=5, ipadx=50)

        ttk.Label(form_frame, text="URL :").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(form_frame, textvariable=self._current_view_model.url).grid(row=1, column=1, sticky="w", padx=5, pady=5, ipadx=100)

        ttk.Label(form_frame, text="Date de création :").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(form_frame, textvariable=self._current_view_model.created_date).grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(form_frame, text="Version :").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(form_frame, textvariable=self._current_view_model.version).grid(row=3, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(form_frame, text="Tags (séparés par virgule) :").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(form_frame, textvariable=self._current_view_model.tags_str).grid(row=4, column=1, sticky="w", padx=5, pady=5, ipadx=100)

        ttk.Checkbutton(form_frame, text="Browser caché (Headless Actif)", variable=self._current_view_model.headless).grid(row=5, column=1, sticky="w", padx=5, pady=5)

        # Right Frame: Workflow Editor
        workflow_frame = ttk.LabelFrame(self.paned, text="Workflow Playwright (50%)")
        self.paned.add(workflow_frame, weight=1) # type: ignore

        self.steps_listbox = tk.Listbox(workflow_frame, height=10)
        self.steps_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(workflow_frame)
        btn_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(btn_frame, text="Ajouter", command=self._add_step).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Supprimer", command=self._remove_step).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Monter", command=self._move_up).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Descendre", command=self._move_down).pack(side="left", padx=2)

        # Bottom Frame: Actions
        action_frame = ttk.Frame(self)
        action_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(action_frame, text="Annuler", command=self._reset_form).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Sauvegarder", command=self._save_form).pack(side="right", padx=5)

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
        """Met à jour la liste des fournisseurs."""
        providers = self.controller.get_providers_list()
        self.provider_combo["values"] = providers
        if providers:
            self.provider_combo.current(0)
            self._on_provider_selected()

    def _on_provider_selected(self, event: Optional[tk.Event] = None) -> None:
        """Charge les données du fournisseur sélectionné dans le formulaire."""
        selected = self.provider_combo.get()
        if not selected:
            return

        try:
            self.controller.get_provider_view_model(selected, self._current_view_model)
            self._update_steps_list()
            self.logger.debug(f"Données chargées pour {selected}")
        except Exception as e:
            self.logger.error(f"Erreur au chargement de {selected}: {e}")
            messagebox.showerror("Erreur", f"Erreur lors du chargement des données:\n{str(e)}")

    def _create_new_provider(self) -> None:
        """Prépare le formulaire pour la création d'un nouveau fournisseur."""
        self.provider_combo.set("")
        self.controller.load_default_view_model(self._current_view_model)
        self._current_view_model.steps = []
        self._update_steps_list()
        self.logger.debug("Formulaire préparé pour un nouveau fournisseur")

    def _reset_form(self) -> None:
        """Réinitialise le formulaire avec la dernière vue chargée (annulation)."""
        selected = self.provider_combo.get()
        if not selected:
            self._create_new_provider()
        else:
            self._on_provider_selected()

    def _save_form(self) -> None:
        """Sauvegarde les modifications via le contrôleur."""
        selected = self.provider_combo.get()
        errors = self._current_view_model.validate()
        if errors:
            messagebox.showwarning("Validation", "\n".join(errors))
            return

        try:
            if not selected:
                # Création d'un nouveau
                new_stem = self.controller.create_new_provider_from_view_model(self._current_view_model)
                self.refresh_providers_list()
                self.provider_combo.set(new_stem)
                self._on_provider_selected()
                messagebox.showinfo("Succès", f"Le fournisseur {new_stem} a été créé avec succès.")
                self.logger.info(f"Nouveau fournisseur créé : {new_stem}")
                if self.on_provider_saved:
                    self.on_provider_saved()
            else:
                # Mise à jour
                new_stem = self.controller.save_provider_from_view_model(selected, self._current_view_model)
                if new_stem != selected:
                    self.refresh_providers_list()
                    self.provider_combo.set(new_stem)
                messagebox.showinfo("Succès", f"Les données de {new_stem} ont été sauvegardées.")
                self.logger.info(f"Modifications sauvegardées pour {new_stem}")
                if self.on_provider_saved:
                    self.on_provider_saved()
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde : {e}")
            messagebox.showerror("Erreur de sauvegarde", str(e))