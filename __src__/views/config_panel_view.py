"""Onglet de supervision des paramètres globaux de l'application.

Ce module crée l'interface requise pour valider, visualiser et configurer
manuellement les options clés (répertoires, log, headless...).
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Any

from controllers.config_controller import ConfigController
from view_models.config_view_model import ConfigViewModel

class ConfigPanelView(ttk.Frame):
    """Panneau de réglages s'appuyant sur ConfigViewModel et ConfigController.
    
    Attributes:
        logger (logging.Logger): Appareil de traçage du module.
        controller (ConfigController): Le pont vers la couche de persistance.
        view_model (ConfigViewModel): Variables interactives reliées à Tkinter.
    """

    def __init__(self, parent: tk.Misc, controller: ConfigController, **kwargs: Any) -> None:
        """Initialise la fenêtre d'édition (UI + ViewModel).

        Args:
            parent (tk.Misc): Support Tkinter.
            controller (ConfigController): Le contrôleur injecté.
            **kwargs (Any): Arguments usuels pour Frame Tk.
        """
        super().__init__(parent, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.controller = controller
        self.view_model = ConfigViewModel()
        self._init_ui()
        self._load_data()

    def _init_ui(self) -> None:
        """Construit et dispose spatialement l'ensemble du formulaire."""
        # Top Frame Informations
        _frame_info = ttk.LabelFrame(self, text="Paramètres globaux")
        _frame_info.pack(fill="x", padx=10, pady=10)
        _frame_info.columnconfigure(1, weight=1)

        ttk.Label(_frame_info, text="Niveau de Log :").grid(row=0, column=0, sticky="e", padx=10, pady=10)
        combo_level = ttk.Combobox(_frame_info, textvariable=self.view_model.log_level, state="readonly", values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        combo_level.grid(row=0, column=1, sticky="we", padx=(0, 10), pady=10)

        ttk.Label(_frame_info, text="Dossier Logs :").grid(row=1, column=0, sticky="e", padx=10, pady=(0, 10))
        ttk.Entry(_frame_info, textvariable=self.view_model.folder_logs).grid(row=1, column=1, sticky="we", padx=(0, 10), pady=(0, 10))

        ttk.Label(_frame_info, text="Dossier Fournisseurs (Providers) :").grid(row=2, column=0, sticky="e", padx=10, pady=(0, 10))
        ttk.Entry(_frame_info, textvariable=self.view_model.folder_providers).grid(row=2, column=1, sticky="we", padx=(0, 10), pady=(0, 10))

        ttk.Label(_frame_info, text="Données Utilisateur (Chromium) :").grid(row=3, column=0, sticky="e", padx=10, pady=(0, 10))
        ttk.Entry(_frame_info, textvariable=self.view_model.user_data_dir).grid(row=3, column=1, sticky="we", padx=(0, 10), pady=(0, 10))

        # Actions
        _frame_actions = ttk.Frame(self)
        _frame_actions.pack(fill="x", padx=10, pady=10)
        ttk.Button(_frame_actions, text="Réinitialiser / Annuler", command=self._load_data).pack(side="left", padx=5)
        ttk.Button(_frame_actions, text="Sauvegarder", command=self._save_data).pack(side="right", padx=5)

    def _load_data(self) -> None:
        """Charge au lancement les données persistées via le contrôleur."""
        self.controller.load_configuration(self.view_model)

    def _save_data(self) -> None:
        """Associe la demande de l'utilisateur à l'ordre de persistance au contrôleur."""
        self.controller.save_configuration(
            self.view_model,
            callback_success=lambda: messagebox.showinfo("Succès", "Configuration sauvegardée avec succès.", parent=self)
        )
