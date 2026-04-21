import tkinter as tk
from tkinter import ttk
import logging

from controllers.scraping_controller import ScrapingController
from view_models.scraping_view_model import ScrapingViewModel
from models.config_aspirabot_model import ConfigAspirabotModel

class ScrapingPanelView(ttk.Frame):
    """Panneau d'ex\u00e9cution et de suivi du scraping."""

    def __init__(self, parent: tk.Misc, app_config: ConfigAspirabotModel, on_lock_actions: callable, on_unlock_actions: callable, **kwargs):
        super().__init__(parent, **kwargs)
        self.logger = logging.getLogger(__name__)
        
        self.on_lock_actions = on_lock_actions
        self.on_unlock_actions = on_unlock_actions
        
        self.view_model = ScrapingViewModel()
        self.controller = ScrapingController(app_config)
        
        self._init_ui()

    def _init_ui(self) -> None:
        """Construit l'interface du panneau de scraping."""
        # Top Frame 1\u00e8re ligne : Boutons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        self.stop_btn = ttk.Button(btn_frame, text="Stopper le scrapping", command=self._event_stop_scrapping, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        self.launch_btn = ttk.Button(btn_frame, text="Lancer / Relancer", command=self._event_launch_scrapping, state="disabled")
        self.launch_btn.pack(side="left", padx=5)
        
        # 2\u00e8me ligne : Texte r\u00e9sum\u00e9
        info_label = ttk.Label(self, textvariable=self.view_model.provider_info_var, font=("Helvetica", 10, "bold"))
        info_label.pack(fill="x", padx=10, pady=5)
        
        # Bas : Zone de log
        self.log_text = tk.Text(self, state="disabled", wrap="word", height=20)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)

    def load_provider(self, stem: str) -> None:
        """S\u00e9lectionne un fournisseur pour le scrapping."""
        self.controller.set_provider(stem, self.view_model)
        self._update_buttons_state()
        self._clear_text()
        self._add_text_log(f"Pr\u00eat \u00e0 lancer le scraping pour le fournisseur '{stem}'.")

    def _event_launch_scrapping(self) -> None:
        """\u00c9v\u00e8nement du bouton Lancer/Relancer."""
        if not self.view_model.has_provider_var.get() or self.view_model.is_running_var.get():
            return
            
        self.on_lock_actions()
        self.view_model.is_running_var.set(True)
        self._update_buttons_state()
        self._clear_text()
        
        # Le callback depuis le view_model vers l'IHM
        def ui_logger(msg: str):
            self.after(0, self._add_text_log, msg)
            
        def on_finish():
            self.after(0, self._on_scrapping_finished)
            
        self.controller.launch_scraping(self.view_model, ui_logger, on_finish)

    def _event_stop_scrapping(self) -> None:
        """\u00c9v\u00e8nement du bouton Stopper."""
        self.controller.request_stop()
        self._add_text_log("Demande d'arr\u00eat envoy\u00e9e (patientez...)")

    def _update_buttons_state(self) -> None:
        running = self.view_model.is_running_var.get()
        has_provider = self.view_model.has_provider_var.get()
        
        if running:
            self.launch_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
        else:
            if has_provider:
                self.launch_btn.config(state="normal")
            else:
                self.launch_btn.config(state="disabled")
            self.stop_btn.config(state="disabled")

    def _on_scrapping_finished(self) -> None:
        self.view_model.is_running_var.set(False)
        self._update_buttons_state()
        self.on_unlock_actions()

    def _clear_text(self) -> None:
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")

    def _add_text_log(self, msg: str) -> None:
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")
