"""Module fournissant l'interface WYSIWYG pour l'édition de fournisseurs.

Ce panneau permet de sélectionner un fournisseur dans une liste,
d'éditer ses informations (URL, nom, date de création, version, tags, 
et le mode headless) et d'annuler ou enregistrer ces modifications.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Any, Optional, Callable

from controllers.wysiwyg_controller import WysiwygController
from models.aspirabot_app_model import AspirabotAppModel
from view_models.wysiwyg_view_model import WysiwygViewModel

class WysiwygPanelView(ttk.Frame):
    """Vue pour l'édition de fournisseurs."""

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

        # Middle Frame: Formulaire
        form_frame = ttk.LabelFrame(self, text="Détails (WYSIWYG)")
        form_frame.pack(fill="both", expand=True, padx=10, pady=5)

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

        # Bottom Frame: Actions
        action_frame = ttk.Frame(self)
        action_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(action_frame, text="Annuler", command=self._reset_form).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Sauvegarder", command=self._save_form).pack(side="right", padx=5)

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
            self.logger.debug(f"Données chargées pour {selected}")
        except Exception as e:
            self.logger.error(f"Erreur au chargement de {selected}: {e}")
            messagebox.showerror("Erreur", f"Erreur lors du chargement des données:\n{str(e)}")

    def _create_new_provider(self) -> None:
        """Prépare le formulaire pour la création d'un nouveau fournisseur."""
        self.provider_combo.set("")
        self.controller.load_default_view_model(self._current_view_model)
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
