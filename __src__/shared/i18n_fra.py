# Main view sidebar width in pixels

from shared.enums import StepTypeEnum, TitleModuleEnum
from shared.resources_icons_util import (
    C_RESS_ICON_BLACK_CONFIG,
    C_RESS_ICON_BLACK_DEBUG,
    C_RESS_ICON_BLACK_EDITOR,
    C_RESS_ICON_BLACK_EXECUTE,
    C_RESS_ICON_BLACK_FAQ,
    C_RESS_ICON_BLACK_LOGS,
    C_RESS_ICON_BLACK_PROFILES,
    C_RESS_ICON_BLACK_SCENARIOS,
    C_RESS_ICON_WHITE_CONFIG,
    C_RESS_ICON_WHITE_DEBUG,
    C_RESS_ICON_WHITE_EDITOR,
    C_RESS_ICON_WHITE_EXECUTE,
    C_RESS_ICON_WHITE_FAQ,
    C_RESS_ICON_WHITE_LOGS,
    C_RESS_ICON_WHITE_PROFILES,
    C_RESS_ICON_WHITE_SCENARIOS,
)

# -----------------------------------------------------------------------------
# Views
# -----------------------------------------------------------------------------

# Scraping panel — status labels
C_SCRAPING_STATUS_INACTIVE = "Est inactif"
C_SCRAPING_JOURNAL_PENDING_STATUS = "Scraping en cours"
C_SCRAPING_JOURNAL_PENDING_VALUE = "..."
C_SCRAPING_JOURNAL_RESULT_OK = "OK"
C_SCRAPING_JOURNAL_RESULT_ERROR = "ERREUR"

# Scraping panel — profile date label
C_SCRAPING_SAVED_DATE_FMT = "Sauvegardé le : {date}"
C_SCRAPING_SAVED_DATE_EMPTY = "Sauvegardé le : --"

# Scraping panel — emergency stop threshold validation warning
C_SCRAPING_EMERGENCY_STOP_INVALID_MSG = (
    "La condition d'arrêt d'urgence doit être un nombre entier entre 1 et 9 999 999."
)

# Scraping panel — workflow guard warnings
C_SCRAPING_NO_PROVIDER_LOADED = "Veuillez charger un fournisseur avant de lancer le scraping."
C_SCRAPING_WORKFLOW_ACTIVE_PROVIDER = (
    "Un Workflow est déjà en cours de modification.\n"
    "Veuillez terminer ou annuler la modification avant de changer de fournisseur."
)
C_SCRAPING_WORKFLOW_ACTIVE_LAUNCH = (
    "Un Workflow est déjà en cours de modification.\n"
    "Veuillez terminer ou annuler la modification avant de lancer le scraping."
)

# Scraping panel — journal lifecycle event messages
C_SCRAPING_EVENT_BROWSER_INIT = "Initialisation du navigateur..."
C_SCRAPING_EVENT_CONTEXT_INIT = "Création du contexte de navigation..."
C_SCRAPING_EVENT_WORKFLOW_INIT = "Démarrage des étapes du workflow..."

# Scraping panel — final run status labels
C_SCRAPING_STATUS_CANCELLED = "Scraping annulé"
C_SCRAPING_STATUS_FINISHED = "Scraping terminé"
C_SCRAPING_STATUS_ERROR = "erreur"
C_SCRAPING_STATUS_EMERGENCY_STOP = "Processus mise en pause : seuil d'erreurs dépassé"

# Scraping panel — export error message ({exc} is the caught exception)
C_SCRAPING_EXPORT_WRITE_ERROR = "Impossible d'écrire le fichier :\n{exc}"

# Debug panel — session launch validation errors
C_DEBUG_URL_EMPTY = "L'URL ne peut pas être vide."
C_DEBUG_TIMEOUT_INVALID = "Le timeout doit être un entier entre 1 et 30 secondes."
C_DEBUG_DNS_DELAY_INVALID = "Le délai d'attente DNS doit être un entier entre 1 et 30 secondes."

# Scraping panel — no URL source confirmation dialog
C_SCRAPING_NO_URL_SOURCE_TITLE = "Aucune source d'URLs"
C_SCRAPING_NO_URL_SOURCE_MSG = (
    "Aucune source d'URLs n'est selectionnee.\n\n"
    "Les etapes OPEN_URL en mode '<<SOURCE>>' seront en erreur.\n\n"
    "Souhaitez-vous continuer quand meme ?"
)

# -----------------------------------------------------------------------------
# Labels
# -----------------------------------------------------------------------------


# Mapping of module names to their corresponding black and white icon resource names.
# Order of modules is determined by the order of entries in this dictionary.
C_LISTING_MODULES: dict[TitleModuleEnum, tuple[str, str, str]] = {
    TitleModuleEnum.E_LOGS: ["Journal", C_RESS_ICON_BLACK_LOGS, C_RESS_ICON_WHITE_LOGS],
    TitleModuleEnum.E_PROFILES: ["Profils", C_RESS_ICON_BLACK_PROFILES, C_RESS_ICON_WHITE_PROFILES],
    TitleModuleEnum.E_SCENARIOS: ["Scénarios", C_RESS_ICON_BLACK_SCENARIOS, C_RESS_ICON_WHITE_SCENARIOS],
    TitleModuleEnum.E_EDITOR: ["Modifier", C_RESS_ICON_BLACK_EDITOR, C_RESS_ICON_WHITE_EDITOR],
    TitleModuleEnum.E_EXECUTOR: ["Exécuter", C_RESS_ICON_BLACK_EXECUTE, C_RESS_ICON_WHITE_EXECUTE],
    TitleModuleEnum.E_FAQ: ["F.A.Q.", C_RESS_ICON_BLACK_FAQ, C_RESS_ICON_WHITE_FAQ],
    TitleModuleEnum.E_DEBUG: ["Debug", C_RESS_ICON_BLACK_DEBUG, C_RESS_ICON_WHITE_DEBUG],
    TitleModuleEnum.E_OPTIONS: ["Options", C_RESS_ICON_BLACK_CONFIG, C_RESS_ICON_WHITE_CONFIG],
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
    StepTypeEnum.E_CLICK_ON_ELEMENT: "Cliquer sur un élément",
    StepTypeEnum.E_CLICK_FOR_DOWNLOAD: "Cliquer pour télécharger",
    StepTypeEnum.E_DOWNLOAD_IMAGE: "Télécharger les images",
    StepTypeEnum.E_EXTRACT_TEXTS: "Extraire textes",
    StepTypeEnum.E_EXTRACT_LINKS: "Extraire liens",
    StepTypeEnum.E_EXPORT_DATA_TO_JS: "Exporter données (json)",
    StepTypeEnum.E_JUMP_TO_STEP: "Sauter vers l'étape si...",
    StepTypeEnum.E_SCROLL_DOWN: "Défiler vers le bas",
    StepTypeEnum.E_KILL_BROWSER: "Quitter navigateur",
}

# -----------------------------------------------------------------------------
# Templates errors
# -----------------------------------------------------------------------------

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
    "click_element_index_invalid": "Étape {step} : l'index du bouton à cliquer est invalide.",
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
    # --- export data to js ---
    "export_data_to_js_prefix_file_required": "Étape {step} : le préfixe de nom de fichier est obligatoire.",
    # --- extract_links ---
    "extract_links_selector_required": "Étape {step} : le sélecteur CSS est obligatoire.",
    "extract_links_target_invalid": "Étape {step} : cible '{value}' invalide.",
    "extract_links_mapping_required": "Étape {step} : la clé de mapping est obligatoire.",
    # --- extract_texts ---
    "extract_texts_selector_required": "Étape {step} : le sélecteur CSS est obligatoire.",
    "extract_texts_mode_invalid": "Étape {step} : mode d'extraction '{value}' invalide.",
    "extract_texts_target_invalid": "Étape {step} : cible '{value}' invalide.",
    "extract_texts_mapping_required": "Étape {step} : la clé de mapping est obligatoire.",
    # --- jump_to_step ---
    "jump_to_step_condition_invalid": "Étape {step} : condition invalide — {value}.",
    "jump_to_step_target_missing": "Étape {step} : aucune étape référencée.",
    "jump_to_step_self_reference": "Étape {step} : ne peut pas pointer vers elle-même.",
    "jump_to_step_target_not_found": "Étape {step} : la cible [{value}] est introuvable.",
    # --- open_url ---
    "open_url_url_required": "Étape {step} : l'URL est obligatoire.",
    "open_url_wait_dns_solver_invalid": "Étape {step} : Délai DNS doit être 1 <= x <= 30 sec.",
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
