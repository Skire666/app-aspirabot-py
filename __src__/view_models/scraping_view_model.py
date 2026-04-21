"""Module d'état pour le panneau de scraping.

Consolide les booléens de chargement, les états liés aux fichiers
ainsi que l'injection des logs générés par le backend asynchrone Playwright.

Exemples d'utilisation:
    >>> vm = ScrapingViewModel()
    >>> vm.add_log("Enregistrement local effectué.")
"""

import tkinter as tk

class ScrapingViewModel:
    """Conserve l'état réactif global du panneau de scraping principal.

    Variables d'état:
        is_running_var (tk.BooleanVar): Flag d'activation du scraper.
        has_provider_var (tk.BooleanVar): Drapeau de présence d'un fournisseur ciblé en mémoire.
        provider_info_var (tk.StringVar): Information sommaire du fournisseur actif.
        logs_var (tk.StringVar): Puits de logs consolidé visualisable dans le panneau Tkinter.
        
    Attributes:
        Aucun des attributs Python fixes n'est directement manipulé car tout l'état
        repose sur ces variables Tkinter.
    """
    def __init__(self) -> None:
        """Initialisation de l'état asynchrone pour l'UI de scraping.
        
        Exemples d'utilisation:
            >>> vm_instance = ScrapingViewModel()
        """
        self.is_running_var = tk.BooleanVar(value=False)
        self.has_provider_var = tk.BooleanVar(value=False)
        self.provider_info_var = tk.StringVar(value="Aucun fournisseur chargé.")
        self.logs_var = tk.StringVar(value="")
        
    def add_log(self, msg: str) -> None:
        """Ajoute incrémentalement un texte de journalisation au `logs_var`.

        Args:
            msg (str): Nouvelle ligne de log formatée et prête pour insertion.

        Exemples d'utilisation:
            >>> vm.add_log("[INFO] Ligne chargée : ...")
            >>> vm.add_log("[WARN] Timeout au clic du selecteur.")
        """
        current = self.logs_var.get()
        if current:
            self.logs_var.set(f"{current}\n{msg}")
        else:
            self.logs_var.set(msg)
            
    def clear_logs(self) -> None:
        """Réinitialise intégralement la valeur de log de l'instance d'état.
        
        Exemples d'utilisation:
            >>> vm.clear_logs()  # Avant le début d'un grand cycle
        """
        self.logs_var.set("")
