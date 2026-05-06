# Main view sidebar width in pixels
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
    StepType.WAIT_X_TIME: "Attendre une durée fixe",
    StepType.RANDOM_PAUSE: "Attendre aléatoirement",
    StepType.WAIT_USER_ACTION: "Attendre action utilisateur",
    StepType.DOWNLOAD_IMAGE: "Télécharger les images",
    StepType.WAIT_IMAGE_SIZE: "Présence d'une image",
    StepType.WAIT_ELEMENT: "Présence d'un élément",
    StepType.COUNT_ELEMENT: "Compter les éléments",
    StepType.CLICK_ELEMENT: "Cliquer sur un élément",
    StepType.EXTRACT_TEXT: "Extraire contenu textuel",
    StepType.JUMP_TO_STEP: "Si le résultat est un...",
    StepType.SCROLL_DOWN: "Défiler vers le bas",
    StepType.END_PROCESS: "Fin du processus",
}

## END
