import tkinter as tk

class ScrapingViewModel:
    """ViewModel pour le panneau de scraping."""
    def __init__(self):
        self.is_running_var = tk.BooleanVar(value=False)
        self.has_provider_var = tk.BooleanVar(value=False)
        self.provider_info_var = tk.StringVar(value="Aucun fournisseur chargé.")
        self.logs_var = tk.StringVar(value="")
        
    def add_log(self, msg: str) -> None:
        current = self.logs_var.get()
        if current:
            self.logs_var.set(f"{current}\n{msg}")
        else:
            self.logs_var.set(msg)
            
    def clear_logs(self) -> None:
        self.logs_var.set("")
