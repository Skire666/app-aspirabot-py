# Main view sidebar width in pixels
import tkinter as tk

from models.step_scraping_model import StepType

C_VIEW_SIDEBAR_LEFT_WIDTH = 88

# All title labels for sidebar buttons
C_TITLE_MODULE_LOGS = "Journal"
C_TITLE_MODULE_PROJECTS = "Projets"
C_TITLE_MODULE_PROVIDER = "Fournisseur"
C_TITLE_MODULE_WORKFLOW = "Workflow"
C_TITLE_MODULE_SCRAPING = "Scraping"
C_TITLE_MODULE_FAQ = "F.A.Q."
C_TITLE_MODULE_CONFIG = "Paramètres"

# French display labels for each step type (Combobox values).
C_STEP_TYPE_TO_LABELS: dict[StepType, str] = {
    StepType.OPEN_URL: "Ouvrir une URL",
    StepType.CLOSE_TABS: "Fermer des onglets",
    StepType.REFRESH_PAGE: "Rafraîchir la page",
    StepType.WAIT_STATE_PAGE: "Attendre état chargement",
    StepType.WAIT_X_TIME: "Attendre une durée fixe",
    StepType.WAIT_RANDOM_PAUSE: "Attendre aléatoirement",
    StepType.WAIT_USER_ACTION: "Attendre action manuelle",
    StepType.COUNT_ELEMENTS: "Compter les éléments",
    StepType.COUNT_IMAGES: "Compter les images",
    StepType.WAIT_IMAGES: "Attendre images",
    StepType.WAIT_ELEMENTS: "Attendre éléments",
    StepType.CLICK_ELEMENT: "Cliquer sur un élément",
    StepType.DOWNLOAD_IMAGE: "Télécharger les images",
    StepType.EXTRACT_TEXT: "Extraire contenu textuel",
    StepType.JUMP_TO_STEP: "Si le résultat est un...",
    StepType.SCROLL_DOWN: "Défiler vers le bas",
    StepType.END_PROCESS: "Fin du processus",
}

# Scraping journal Treeview column configurations: (title, width, anchor, stretch)
C_VIEW_SCRAPING_HEADINGS = {
    "date": ("Date", 155, tk.W, False),
    "step_started": ("Étape démarrée", 110, tk.W, False),
    "duration": ("Durée (s)", 65, tk.E, False),
    "success": ("Résultat", 65, tk.CENTER, False),
    "msg_step_ended": ("Message de fin", 160, tk.W, True),
}

# END
