# Main view sidebar width in pixels
import tkinter as tk

from shared.enums import StepTypeEnum, TitleModuleEnum
from shared.resources_icons_util import (
    C_RESS_ICON_BLACK_CONFIG,
    C_RESS_ICON_BLACK_FAQ,
    C_RESS_ICON_BLACK_LOGS,
    C_RESS_ICON_BLACK_PROJECTS,
    C_RESS_ICON_BLACK_PROVIDER,
    C_RESS_ICON_BLACK_SCRAPING,
    C_RESS_ICON_BLACK_WORKFLOW,
    C_RESS_ICON_WHITE_CONFIG,
    C_RESS_ICON_WHITE_FAQ,
    C_RESS_ICON_WHITE_LOGS,
    C_RESS_ICON_WHITE_PROJECTS,
    C_RESS_ICON_WHITE_PROVIDER,
    C_RESS_ICON_WHITE_SCRAPING,
    C_RESS_ICON_WHITE_WORKFLOW,
)

# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

# Main view sidebar width in pixels
C_VIEW_SIDEBAR_LEFT_WIDTH = 80

# Scraping panel — status labels
C_SCRAPING_STATUS_INACTIVE = "Est inactif"
C_SCRAPING_JOURNAL_PENDING_STATUS = "Scraping en cours"
C_SCRAPING_JOURNAL_PENDING_VALUE = "..."
C_SCRAPING_JOURNAL_RESULT_OK = "OK"
C_SCRAPING_JOURNAL_RESULT_ERROR = "ERR"

# Scraping panel — profile date label
C_SCRAPING_SAVED_DATE_FMT = "Sauvegardé le : {date}"
C_SCRAPING_SAVED_DATE_EMPTY = "Sauvegardé le : --"

# Scraping panel — emergency stop threshold validation warning
C_SCRAPING_EMERGENCY_STOP_INVALID_MSG = (
    "La condition d'arrêt d'urgence doit être un nombre entier entre 1 et 9 999 999."
)

# Scraping panel — no URL source confirmation dialog
C_SCRAPING_NO_URL_SOURCE_TITLE = "Aucune source d'URLs"
C_SCRAPING_NO_URL_SOURCE_MSG = (
    "Aucune source d'URLs n'est selectionnee.\n\n"
    "Les etapes OPEN_URL en mode '<<SOURCE>>' seront en erreur.\n\n"
    "Souhaitez-vous continuer quand meme ?"
)

# Scraping journal Treeview column configurations: (title, width, anchor, stretch)
C_VIEW_SCRAPING_HEADINGS = {
    "date": ("Date", 155, tk.W, False),
    "step_started": ("Étape démarrée", 110, tk.W, False),
    "duration": ("Durée (s)", 65, tk.E, False),
    "success": ("Résultat", 65, tk.CENTER, False),
    "msg_step_ended": ("Message de fin", 160, tk.W, True),
}

# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------


# Mapping of module names to their corresponding black and white icon resource names.
# Order of modules is determined by the order of entries in this dictionary.
C_LISTING_MODULES: dict[TitleModuleEnum, tuple[str, str, str]] = {
    TitleModuleEnum.E_LOGS: ["Journal", C_RESS_ICON_BLACK_LOGS, C_RESS_ICON_WHITE_LOGS],
    TitleModuleEnum.E_PROJECTS: ["Projets", C_RESS_ICON_BLACK_PROJECTS, C_RESS_ICON_WHITE_PROJECTS],
    TitleModuleEnum.E_PROVIDER: ["Fournisseurs", C_RESS_ICON_BLACK_PROVIDER, C_RESS_ICON_WHITE_PROVIDER],
    TitleModuleEnum.E_WORKFLOW: ["Workflow", C_RESS_ICON_BLACK_WORKFLOW, C_RESS_ICON_WHITE_WORKFLOW],
    TitleModuleEnum.E_SCRAPING: ["Scraping", C_RESS_ICON_BLACK_SCRAPING, C_RESS_ICON_WHITE_SCRAPING],
    TitleModuleEnum.E_FAQ: ["FAQ", C_RESS_ICON_BLACK_FAQ, C_RESS_ICON_WHITE_FAQ],
    TitleModuleEnum.E_CONFIG: ["Paramètres", C_RESS_ICON_BLACK_CONFIG, C_RESS_ICON_WHITE_CONFIG],
}


# French display labels for each step type (Combobox values).
C_STEP_TYPE_TO_LABELS: dict[StepTypeEnum, str] = {
    StepTypeEnum.E_OPEN_URL: "Ouvrir une URL",
    StepTypeEnum.E_CLOSE_TABS: "Fermer des onglets",
    StepTypeEnum.E_REFRESH_PAGE: "Rafraîchir la page",
    StepTypeEnum.E_WAIT_PAGE_STATE: "Attendre un état de page",
    StepTypeEnum.E_WAIT_FIXED_TIME: "Attendre une durée fixe",
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

# ---------------------------------------------------------------------------
# Templates errors
# ---------------------------------------------------------------------------

"""User-facing message templates for all presenters.

All user-visible strings are defined here.  No presenter, service, or view
may ever write a user-facing string inline; every message must be formatted
from one of the templates below.

Example:
    >>> msg = ERROR_TEMPLATES["image_dim_not_int"].format(step="02", key="height_min")
    >>> msg
    "Étape 02 : height_min doit être un nombre entier."
"""

ERROR_TEMPLATES: dict[str, str] = {
    # --- Shared image dimension validation (download_image, count_html_images, wait_html_images) ---
    "image_dim_not_int": "Étape {step} : {key} doit être un nombre entier.",
    "image_dim_negative": "Étape {step} : {key} doit être >= 0.",
    "image_dim_max_below_one": "Étape {step} : {key} doit être >= 1.",
    "image_dim_range_invalid": "Étape {step} : {min_key} doit être <= {max_key}.",
    # --- click_element ---
    "click_element_selector_required": "Étape {step} : le sélecteur CSS est obligatoire.",
    # --- close_tabs ---
    "close_tabs_filter_required": "Étape {step} : le filtre URL est obligatoire.",
    "close_tabs_max_tabs_invalid": "Étape {step} : le nombre max. d'onglets doit être >= 1.",
    # --- count_html_elements ---
    "count_html_elements_selector_required": "Étape {step} : le sélecteur CSS est obligatoire.",
    "count_html_elements_value_negative": "Étape {step} : value doit être >= 0.",
    "count_html_elements_success_if_invalid": "Étape {step} : success_if invalide — {value!r}.",
    "count_html_elements_operator_invalid": "Étape {step} : operator invalide — {value!r}.",
    # --- count_html_images ---
    "count_html_images_value_negative": "Étape {step} : value doit être >= 0.",
    "count_html_images_success_if_invalid": "Étape {step} : success_if invalide — {value!r}.",
    "count_html_images_operator_invalid": "Étape {step} : operator invalide — {value!r}.",
    # --- end_process ---
    "end_process_wait_duration_invalid": "Étape {step} : la durée d'attente doit être >= 0.",
    "end_process_wait_unit_invalid": "Étape {step} : unité de temps invalide — {value!r}.",
    # --- extract_text ---
    "extract_text_selector_required": "Étape {step} : le sélecteur CSS est obligatoire.",
    "extract_text_mode_invalid": "Étape {step} : mode d'extraction '{value}' invalide.",
    "extract_text_target_invalid": "Étape {step} : cible '{value}' invalide.",
    # --- jump_to_step ---
    "jump_to_step_condition_invalid": "Étape {step} : condition invalide — {value}.",
    "jump_to_step_target_missing": "Étape {step} : aucune étape référencée.",
    "jump_to_step_self_reference": "Étape {step} : ne peut pas pointer vers elle-même.",
    "jump_to_step_target_not_found": "Étape {step} : la cible [{value}] est introuvable.",
    # --- open_url ---
    "open_url_url_required": "Étape {step} : l'URL est obligatoire.",
    "open_url_timeout_invalid": "Étape {step} : le timeout doit être >= 1.",
    "open_url_timeout_unit_invalid": "Étape {step} : l'unité de timeout est invalide.",
    # --- refresh_page ---
    "refresh_page_timeout_invalid": "Étape {step} : le timeout doit être >= 1.",
    "refresh_page_timeout_unit_invalid": "Étape {step} : l'unité de timeout est invalide — {value!r}.",
    # --- scroll_down ---
    "scroll_down_pixels_invalid": "Étape {step} : le nombre de pixels doit être >= 1.",
    # --- wait_html_elements ---
    "wait_html_elements_selector_required": "Étape {step} : le sélecteur CSS est obligatoire.",
    "wait_html_elements_operator_invalid": (
        "Étape {step} : l'opérateur doit être l'un des suivants : "
        "equal, not_equal, greater_than, less_than, greater_or_equal, less_or_equal."
    ),
    "wait_html_elements_quantity_negative": "Étape {step} : la quantité doit être >= 0.",
    "wait_html_elements_retry_delay_invalid": "Étape {step} : le délai de retry doit être >= 1.",
    "wait_html_elements_retry_unit_invalid": "Étape {step} : l'unité de retry est invalide.",
    "wait_html_elements_retry_max_invalid": "Étape {step} : le nombre maximum de retry doit être >= 1.",
    # --- wait_html_images ---
    "wait_html_images_operator_invalid": (
        "Étape {step} : l'opérateur doit être l'un des suivants : "
        "equal, not_equal, greater_than, less_than, greater_or_equal, less_or_equal."
    ),
    "wait_html_images_quantity_negative": "Étape {step} : la quantité doit être >= 0.",
    "wait_html_images_retry_delay_invalid": "Étape {step} : le délai de retry doit être >= 1.",
    "wait_html_images_retry_unit_invalid": "Étape {step} : l'unité de retry est invalide.",
    "wait_html_images_retry_max_invalid": "Étape {step} : le nombre maximum de retry doit être >= 1.",
    # --- wait_page_state ---
    "wait_page_state_timeout_invalid": "Étape {step} : le timeout doit être >= 1.",
    "wait_page_state_timeout_unit_invalid": "Étape {step} : l'unité de timeout est invalide.",
    # --- wait_rng_pause ---
    "wait_rng_pause_min_invalid": "Étape {step} : la valeur min. doit être >= 1.",
    "wait_rng_pause_max_invalid": "Étape {step} : la valeur max. doit être >= 1.",
    "wait_rng_pause_range_invalid": "Étape {step} : la valeur min. doit être <= la valeur max.",
    # --- wait_user_action ---
    "wait_user_action_condition_invalid": "Étape {step} : condition invalide — {value!r}.",
    "wait_user_action_wait_duration_invalid": "Étape {step} : le délai post-reprise doit être >= 1.",
    "wait_user_action_wait_unit_invalid": "Étape {step} : l'unité de temps est invalide — {value!r}.",
    # --- wait_fixed_time ---
    "wait_fixed_time_duration_invalid": "Étape {step} : la durée d'attente doit être >= 0.",
}

# EOF
