"""Module responsable de l'affichage des journaux (logs) dans l'IHM.

Ce module fournit un widget Tkinter personnalisé permettant d'afficher
les messages de log de l'application en temps réel, avec une coloration
syntaxique basée sur le niveau de sévérité du log.

Exemple d'utilisation:
    root = tk.Tk()
    logs_panel = LogsPanel(root)
    logs_panel.pack(fill="both", expand=True)
    root.mainloop()
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import logging
import queue
from typing import Any

from utils.logging_util import setup_logger

class LogsPanelView(ttk.Frame):
    """Panneau responsable de l'affichage des journaux (logs).

    Ce composant hérite de ttk.Frame et intègre une zone de texte avec défilement
    pour afficher les logs de l'application en temps réel.

    Attributes:
        logger (logging.Logger): Le logger dédié à l'interface graphique.
        log_textbox (scrolledtext.ScrolledText): La zone de texte affichant les logs.
        log_queue (queue.Queue): La file d'attente contenant les messages de log.
    """

    def __init__(self, parent: tk.Misc, **kwargs: Any) -> None:
        """Initialise le panneau des logs.

        Args:
            parent (tk.Misc): Le widget parent auquel ce panneau est rattaché.
            **kwargs (Any): Arguments supplémentaires passés au constructeur de ttk.Frame.
        """
        super().__init__(parent, **kwargs)
        self.logger = logging.getLogger(__name__)
        self._init_ui()
        self._init_logging()
        
    def _init_ui(self) -> None:
        """Prépare la zone d'affichage des journaux.

        Crée et configure le widget ScrolledText avec une police à espacement
        fixe et le place dans le panneau.
        """
        self.log_textbox = scrolledtext.ScrolledText(
            self, width=65, height=20, state="disabled", font=("Courier", 10)
        )
        self.log_textbox.pack(pady=10, padx=10, fill="both", expand=True)

    def _init_logging(self) -> None:
        """Connecte la zone de texte du journal au système de log.

        Initialise la file d'attente des logs, configure le gestionnaire
        via `setup_logger` et démarre la boucle de traitement des logs.
        """
        self.log_queue: queue.Queue[tuple[logging.LogRecord, str]] = queue.Queue()
        
        setup_logger(self.log_queue)
        
        self.logger.debug("Branchement du gestionnaire de logs IHM via QueueHandler.")
        self.logger.info("L'interface graphique est prête.")

        self.after(100, self._process_log_queue)

    def _process_log_queue(self) -> None:
        """Traite les enregistrements en attente depuis la file et les affiche.

        Cette méthode dépile de manière asynchrone les messages de la file d'attente
        et les insère dans le champ texte, en appliquant le style approprié au
        niveau de gravité. La boucle relance automatiquement la tâche après 100ms.
        """
        while True:
            try:
                record, msg = self.log_queue.get_nowait()
                
                self.log_textbox.configure(state="normal")
                tag_name = f"level_{record.levelname}"
                self.log_textbox.tag_config(tag_name, foreground=self._get_color_for_level(record.levelno))
                
                self.log_textbox.insert(tk.END, msg + "\n", tag_name)
                self.log_textbox.configure(state="disabled")
                self.log_textbox.see(tk.END)
                
            except queue.Empty:
                break
        
        self.after(100, self._process_log_queue)
        
    def _get_color_for_level(self, level: int) -> str:
        """Détermine la couleur textuelle Tkinter depuis le niveau de log.

        Args:
            level (int): Niveau numérique de gravité du log (e.g. logging.ERROR).

        Returns:
            str: Nom de la couleur reconnue par Tkinter pour correspondre
            à la sévérité du log.
        """
        if level >= logging.ERROR:
            return "red"
        elif level >= logging.WARNING:
            return "orange"
        elif level >= logging.INFO:
            return "black"
        else:
            return "gray"
