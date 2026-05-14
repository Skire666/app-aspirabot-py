# Main view sidebar width in pixels
import tkinter as tk

from shared.enums import StepTypeEnum

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Main view sidebar width in pixels
C_VIEW_SIDEBAR_LEFT_WIDTH = 80

# All title labels for sidebar buttons
C_TITLE_MODULE_LOGS = "Journal"
C_TITLE_MODULE_PROJECTS = "Projets"
C_TITLE_MODULE_PROVIDER = "Fournisseur"
C_TITLE_MODULE_WORKFLOW = "Workflow"
C_TITLE_MODULE_SCRAPING = "Scraping"
C_TITLE_MODULE_FAQ = "F.A.Q."
C_TITLE_MODULE_CONFIG = "Paramètres"

# French display labels for each step type (Combobox values).
C_STEP_TYPE_TO_LABELS: dict[StepTypeEnum, str] = {
    StepTypeEnum.E_OPEN_URL: "Ouvrir une URL",
    StepTypeEnum.E_CLOSE_TABS: "Fermer des onglets",
    StepTypeEnum.E_REFRESH_PAGE: "Rafraîchir la page",
    StepTypeEnum.E_WAIT_PAGE_STATE: "Attendre un état de page",
    StepTypeEnum.E_WAIT_X_TIME: "Attendre une durée fixe",
    StepTypeEnum.E_WAIT_RANDOM_PAUSE: "Attendre aléatoirement",
    StepTypeEnum.E_WAIT_USER_ACTION: "Attendre action manuelle",
    StepTypeEnum.E_COUNT_HTML_ELEMENTS: "Compter les éléments",
    StepTypeEnum.E_COUNT_HTML_IMAGES: "Compter les images",
    StepTypeEnum.E_WAIT_HTML_ELEMENTS: "Attendre X éléments",
    StepTypeEnum.E_WAIT_HTML_IMAGES: "Attendre X images",
    StepTypeEnum.E_CLICK_ELEMENT: "Cliquer sur un élément",
    StepTypeEnum.E_DOWNLOAD_IMAGE: "Télécharger les images",
    StepTypeEnum.E_EXTRACT_TEXT: "Extraire contenu textuel",
    StepTypeEnum.E_JUMP_TO_STEP: "Si le résultat est un...",
    StepTypeEnum.E_SCROLL_DOWN: "Défiler vers le bas",
    StepTypeEnum.E_END_PROCESS: "Fin du processus",
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
