"""Objet de transfert de données (ViewModel) pour l'interface de Configuration.

Sépare les variables manipulables par Tkinter des modèles de données (domain).
"""

import tkinter as tk

class ConfigViewModel:
    """ViewModel pour les éléments de configuration de l'application.
    
    Lie de façon bidirectionnelle les valeurs modifiables par Tkinter et
    les propriétés exposables liées aux règles métier.
    """

    def __init__(self) -> None:
        """Initialise les variables Tkinter."""
        self.log_level = tk.StringVar(value="INFO")
        self.folder_logs = tk.StringVar(value="./tmp_logs")
        self.folder_providers = tk.StringVar(value="./user_folder_providers")
        self.user_data_dir = tk.StringVar(value="./tmp_chromium_session")
