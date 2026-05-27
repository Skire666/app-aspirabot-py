# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk

from models.app_configuration_model import AppConfigurationModel

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ExecutorView(ttk.Frame):
    def __init__(self, config_model: AppConfigurationModel, parent: tk.Widget) -> None:
        super().__init__(parent)


# EOF
