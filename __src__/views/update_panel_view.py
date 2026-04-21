"""Onglet d'édition et de création pour les fournisseurs de scraping.

Ce module abrite un composant UI complexe combiné à une fenêtre modale (`ActionSelectionDialog`)
afin de dicter le workflow métier JSON (séquence d'instructions asynchrones) que subira Playwright.

Exemples d'utilisation:
    >>> vue_edit = UpdatePanelView(notebook, config_app)
    >>> vue_edit.load_existing_provider("fichier.json")
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
from typing import Any, Optional, Callable, Dict

from controllers.update_controller import UpdateController
from models.config_aspirabot_model import ConfigAspirabotModel
from view_models.update_view_model import UpdateViewModel
from enum import Enum

class WorkflowAction(str, Enum):
    """Énumération des différentes actions asynchrones de scraping permises."""
    FIND_ELEMENT = "FIND_ELEMENT"
    CLICK = "CLICK"
    DOWNLOAD_IMAGE = "DOWNLOAD_IMAGE"
    WAIT = "WAIT"
    EXTRACT_TEXT = "EXTRACT_TEXT"
    CLOSE_OTHER_TABS = "CLOSE_OTHER_TABS"

class ActionSelectionDialog:
    """Fenêtre surgissante (Modale) d'aide à la sélection d'une action de workflow.

    Attributes:
        top (tk.Toplevel): Fenêtre enfant capturant le focus.
        selected_action (Optional[WorkflowAction]): Enum choisi par l'utilisateur.
        action_var (tk.StringVar): Variable de liaison pour la Combobox.
    """
    def __init__(self, parent: tk.Misc, title: str) -> None:
        """Prépare et affiche la fenêtre modale.

        Args:
            parent (tk.Misc): Composant appelant et conteneur Tkinter.
            title (str): Titre formel de la fenêtre.
        """
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
        """Enregistre le choix et ferme la modale."""
        self.selected_action = WorkflowAction(self.action_var.get())
        self.top.destroy()

    def _on_cancel(self) -> None:
        """Annule l'opération (sans sélection) et ferme."""
        self.top.destroy()

class UpdatePanelView(ttk.Frame):
    """Panneau de mise à jour des paramètres et étapes métiers des fournisseurs.

    Gère tous les champs via un `UpdateViewModel` en double sens avec le `UpdateController`.
    Il s'occupe de générer automatiquement un nom de fichier standard si le fournisseur
    est en cours de création.

    Attributes:
        logger (logging.Logger): Observateur de classe.
        controller (UpdateController): Moteur contenant la logique métier.
        form_frame (ttk.Frame): Composant haut (Informations/Metadonnées).
        workflow_frame (ttk.LabelFrame): Supportant la liste séquentielle d'instructions.
    """

    def __init__(self, parent: tk.Misc, app_config: ConfigAspirabotModel, on_provider_saved: Optional[Callable[[], None]] = None, on_action_complete: Optional[Callable[[], None]] = None, **kwargs: Any) -> None:
        """Initialise la fenêtre d'édition (UI + ViewModel).

        Args:
            parent (tk.Misc): Support Tkinter.
            app_config (ConfigAspirabotModel): Accès au système de fichiers de l'application.
            on_provider_saved (Optional[Callable[[], None]]): Action signalant une sauvegarde réussie (souvent un rechargement liste).
            on_action_complete (Optional[Callable[[], None]]): Action clôturant le cycle et justifiant le changement d'onglet.
            **kwargs (Any): Arguments usuels pour Frame Tk.
        """
        super().__init__(parent, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.controller = UpdateController(app_config)
        self._current_view_model: UpdateViewModel = UpdateViewModel()
        self._event_after_provider_was_saved = on_provider_saved
        self._event_redirect_to_tab = on_action_complete
        self._selected_provider_title: Optional[str] = None
        self._init_ui()

    def _init_ui(self) -> None:
        """Construit et dispose spatialement l'ensemble du formulaire CRUD."""
        # Top Container: Split into Information and Metadata
        _top_container = ttk.Frame(self)
        _top_container.pack(fill="x", padx=10, pady=10)
        _top_container.columnconfigure(0, weight=1, uniform="half")
        _top_container.columnconfigure(1, weight=1, uniform="half")
        self.form_frame = _top_container

        # Informations (Left)
        _frame_info = ttk.LabelFrame(_top_container, text="Informations")
        _frame_info.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        ttk.Label(_frame_info, text="Nom :").grid(row=0, column=0, sticky="e", padx=(10, 5), pady=10)
        ttk.Entry(_frame_info, textvariable=self._current_view_model.provider_title).grid(row=0, column=1, sticky="we", padx=(0, 10), pady=10)
        
        ttk.Label(_frame_info, text="URL :").grid(row=1, column=0, sticky="e", padx=(10, 5), pady=(0, 10))
        ttk.Entry(_frame_info, textvariable=self._current_view_model.url).grid(row=1, column=1, sticky="we", padx=(0, 10), pady=(0, 10))
        
        # case à cocher (avec style pour les agrandir un peu)
        style = ttk.Style()
        style.configure('Big.TCheckbutton', indicatorsize=18)
        
        ttk.Checkbutton(_frame_info, text="Browser affiché (si headless alors le désactivé)", variable=self._current_view_model.browser_displayed, style="Big.TCheckbutton").grid(row=2, column=1, sticky="w", pady=(0, 5))
        ttk.Checkbutton(_frame_info, text="Automatisation obfusquée (masque l'emprunte de playwright)", variable=self._current_view_model.automation_obfuscated, style="Big.TCheckbutton").grid(row=3, column=1, sticky="w", pady=(0, 10))
        
        _frame_info.columnconfigure(1, weight=1)

        # Métadonnées (Right)
        _frame_meta = ttk.LabelFrame(_top_container, text="Métadonnées")
        _frame_meta.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        ttk.Label(_frame_meta, text="Fichier :").grid(row=0, column=0, sticky="e", padx=(10, 5), pady=10)
        self._filename_entry = ttk.Entry(_frame_meta, textvariable=self._current_view_model.provider_filename, state="disabled")
        self._filename_entry.grid(row=0, column=1, sticky="we", padx=(0, 10), pady=10)
        
        ttk.Label(_frame_meta, text="Version :").grid(row=1, column=0, sticky="e", padx=(10, 5), pady=(0, 10))
        ttk.Entry(_frame_meta, textvariable=self._current_view_model.version).grid(row=1, column=1, sticky="we", padx=(0, 10), pady=(0, 10))
        
        ttk.Label(_frame_meta, text="Date de création :").grid(row=2, column=0, sticky="e", padx=(10, 5), pady=(0, 10))
        ttk.Entry(_frame_meta, textvariable=self._current_view_model.created_date).grid(row=2, column=1, sticky="we", padx=(0, 10), pady=(0, 10))

        ttk.Label(_frame_meta, text="Date de modification :").grid(row=3, column=0, sticky="e", padx=(10, 5), pady=(0, 10))
        ttk.Entry(_frame_meta, textvariable=self._current_view_model.modified_date).grid(row=3, column=1, sticky="we", padx=(0, 10), pady=(0, 10))

        _frame_meta.columnconfigure(1, weight=1)

        # Traces pour calculer dynamiquement le nom de fichier
        self._current_view_model.provider_title.trace_add("write", self._on_filename_dependency_changed)
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
        """Modifie grossièrement l'état des entrées du composant parent ('normal' ou 'disabled')."""
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
        """Demande les informations au travers du `ActionSelectionDialog` puis ajoute une ligne."""
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
        """Détruit la ligne de la ListBox."""
        sel = self.steps_listbox.curselection() # type: ignore
        if sel:
            idx = int(str(sel[0])) # type: ignore
            del self._current_view_model.steps[idx]
            self._update_steps_list()

    def _move_up(self) -> None:
        """Permute tactiquement avec la ligne supérieure."""
        sel = self.steps_listbox.curselection() # type: ignore
        if sel and int(str(sel[0])) > 0: # type: ignore
            idx = int(str(sel[0])) # type: ignore
            self._current_view_model.steps[idx], self._current_view_model.steps[idx-1] = self._current_view_model.steps[idx-1], self._current_view_model.steps[idx]
            self._update_steps_list()
            self.steps_listbox.selection_set(idx-1)

    def _move_down(self) -> None:
        """Permute tactiquement avec la ligne inférieure."""
        sel = self.steps_listbox.curselection() # type: ignore
        if sel and hasattr(self._current_view_model, 'steps') and self._current_view_model.steps and int(str(sel[0])) < len(self._current_view_model.steps) - 1: # type: ignore
            idx = int(str(sel[0])) # type: ignore
            self._current_view_model.steps[idx], self._current_view_model.steps[idx+1] = self._current_view_model.steps[idx+1], self._current_view_model.steps[idx]
            self._update_steps_list()
            self.steps_listbox.selection_set(idx+1)

    def _update_steps_list(self) -> None:
        """Regénère les libellés condensés des étapes Playwright enregistrées."""
        self.steps_listbox.delete(0, tk.END)
        if hasattr(self._current_view_model, 'steps') and self._current_view_model.steps:
            for step in self._current_view_model.steps:
                action_type = step.get('type')
                details = ", ".join(f"{k}={v}" for k, v in step.items() if k != "type")
                display_text = f"[{action_type}] {details}" if details else f"[{action_type}]"
                self.steps_listbox.insert(tk.END, display_text)

    def load_existing_provider(self, provider_title: str) -> None:
        """Demande l'hydratation du `UpdateViewModel` depuis la structure logicielle JSON.

        Args:
            provider_title (str): L'identifiant (titre) absolu du fournisseur visé.
        """
        self._selected_provider_title = provider_title
        self._set_form_state("normal")
        try:
            self.controller.get_provider_view_model(provider_title, self._current_view_model)
            self._update_steps_list()
            self.logger.debug(f"Données chargées pour {provider_title}")
        except Exception as e:
            self.logger.error(f"Erreur au chargement de {provider_title}: {e}")
            messagebox.showerror("Erreur", f"Erreur lors du chargement des données:\n{str(e)}")

    def load_default(self) -> None:
        """Active l'UI et initie des valeurs factices ou par défaut (Nouveau Profil)."""
        self._selected_provider_title = None
        self._set_form_state("normal")
        self.controller.load_default_view_model(self._current_view_model)
        self._update_steps_list()
        self.logger.debug("Données par défaut chargées pour création")

    def _reset_form(self) -> None:
        """Annule toutes entrées, vidant et verrouillant le mode Edition."""
        self._selected_provider_title = None
        self._current_view_model.provider_title.set("")
        self._current_view_model.provider_filename.set("")
        self._current_view_model.url.set("")
        self._current_view_model.version.set("")
        self._current_view_model.created_date.set("")
        self._current_view_model.modified_date.set("")
        
    def _save_form(self) -> None:
        """Vérifie l'intégrité (via le `UpdateViewModel`) et lance l'archivage disque.
        
        Affiche des MessageBox bloquantes si des fautes de structures ou typographies
        sont observées dans le paramétrage.
        """
        erreurs = self._current_view_model.validate()
        if erreurs:
            msg = "Impossible de sauvegarder : \n- " + "\n- ".join(erreurs)
            messagebox.showwarning("Validation", msg)
            return
            
        try:
            self.controller.save_provider(self._current_view_model, self._selected_provider_title)
            messagebox.showinfo("Succès", "Fournisseur sauvegardé avec succès.")
            if self._event_after_provider_was_saved:
                self._event_after_provider_was_saved()
            if self._event_redirect_to_tab:
                self._event_redirect_to_tab()
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde: {e}")
            messagebox.showerror("Erreur", f"Une erreur est survenue:\n{e}")
        self._current_view_model.browser_displayed.set(True)
        self._current_view_model.automation_obfuscated.set(True)
        self._current_view_model.steps.clear()
        self._update_steps_list()
        self._set_form_state("disabled")
        
        if self._event_redirect_to_tab:
            self._event_redirect_to_tab()

    def _save_form(self) -> None:
        errors = self._current_view_model.validate()
        if errors:
            messagebox.showwarning("Validation", "\n".join(errors))
            return
            
        try:
            selected: str | None = self._selected_provider_title

            if not selected:
                # Vérifier si le fichier existe déjà
                import os
                from pathlib import Path
                filename = self._current_view_model.provider_filename.get()
                suggested_path = Path(self.controller.config.folder_providers) / filename
                if os.path.exists(suggested_path):
                    if not messagebox.askyesno("Attention", f"Le fichier '{filename}' existe déjà.\nVoulez-vous l'écraser ?"):
                        return

                # Création d'un nouveau fournisseur
                self.create_new_provider()
            else:
                # Mise à jour d'un fournisseur existant
                self.udpate_existing_provider(selected)

            if self._event_after_provider_was_saved:
                self._event_after_provider_was_saved()

            self._reset_form()
                
            if self._event_redirect_to_tab:
                self._event_redirect_to_tab()
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde:\n{str(e)}")

    def udpate_existing_provider(self, selected: str) -> None:
        self.logger.info(f"Mise à jour du fournisseur : {selected}")
        self.controller.save_provider_from_view_model(selected, self._current_view_model)
        messagebox.showinfo("Succès", f"Les données de {selected} ont été sauvegardées.")
        self.logger.info(f"Modifications sauvegardées pour {selected}")

    def create_new_provider(self):
        new_stem = self.controller.create_new_provider_from_view_model(self._current_view_model)
        self._selected_provider_title = new_stem
        messagebox.showinfo("Succès", f"Le fournisseur {new_stem} a été créé avec succès.")
        self.logger.info(f"Nouveau fournisseur créé : {new_stem}")
