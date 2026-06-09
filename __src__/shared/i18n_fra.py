# Main view sidebar width in pixels

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.enums import StepTypeEnum, TitleModuleEnum
from shared.resources_icons_util import (
    C_RESS_ICON_BLACK_CONFIG,
    C_RESS_ICON_BLACK_DEBUG,
    C_RESS_ICON_BLACK_DISCOVER,
    C_RESS_ICON_BLACK_EDITOR,
    C_RESS_ICON_BLACK_EXECUTOR,
    C_RESS_ICON_BLACK_FAQ,
    C_RESS_ICON_BLACK_LOGS,
    C_RESS_ICON_BLACK_PROFILES,
    C_RESS_ICON_BLACK_SCENARIOS,
    C_RESS_ICON_BLACK_SCRAPING,
    C_RESS_ICON_WHITE_CONFIG,
    C_RESS_ICON_WHITE_DEBUG,
    C_RESS_ICON_WHITE_DISCOVER,
    C_RESS_ICON_WHITE_EDITOR,
    C_RESS_ICON_WHITE_EXECUTOR,
    C_RESS_ICON_WHITE_FAQ,
    C_RESS_ICON_WHITE_LOGS,
    C_RESS_ICON_WHITE_PROFILES,
    C_RESS_ICON_WHITE_SCENARIOS,
    C_RESS_ICON_WHITE_SCRAPING,
)

# -----------------------------------------------------------------------------
# Views
# -----------------------------------------------------------------------------

# Scraping panel — journal lifecycle event messages
C_SCRAPING_EVENT_BROWSER_INIT = "Initialisation du navigateur..."
C_SCRAPING_EVENT_CONTEXT_INIT = "Création du contexte de navigation..."
C_SCRAPING_EVENT_WORKFLOW_INIT = "Démarrage des étapes du workflow..."
C_SCRAPING_EVENT_PAUSE_ASKED = "Mise en pause. En attente de reprise..."

# Scraping panel — final run status labels
C_SCRAPING_STATUS_CANCELLED = "Scraping annulé"
C_SCRAPING_STATUS_FINISHED = "Scraping terminé"
C_SCRAPING_STATUS_ERROR = "erreur"
C_SCRAPING_STATUS_EMERGENCY_STOP = "Processus mise en pause : seuil d'erreurs dépassé"
C_SCRAPING_STATUS_STARTING = "Démarrage..."
C_SCRAPING_STATUS_PAUSED = "En pause"
C_SCRAPING_STATUS_RUNNING = "Scraping en cours"

# Scraping panel — export error message ({exc} is the caught exception)
C_SCRAPING_EXPORT_WRITE_ERROR = "Impossible d'écrire le fichier :\n{exc}"

# Executor panel — validation messages
C_EXEC_NO_SCENARIO = "Veuillez sélectionner un scénario."
C_EXEC_NO_PROFILE = "Veuillez sélectionner un profil de lancement."
C_EXEC_NO_EXPORT_FOLDER = "Le dossier d'export est requis."
C_EXEC_NO_URL_SOURCE = "Veuillez configurer une source d'URL."
C_EXEC_INVALID_GLOBAL_THRESHOLD = "Le seuil global d'erreurs doit être un entier entre 1 et 9 999 999."
C_EXEC_STEP_THRESHOLD_WITHOUT_STEP = "Veuillez sélectionner une étape pour le seuil par étape."
C_EXEC_INVALID_STEP_THRESHOLD = "Le seuil par étape doit être un entier entre 1 et 9 999 999."
C_EXEC_FOLDER_URL_SOURCE_EMPTY = "Le chemin de la source d'URL est requis."
C_EXEC_SAVE_ERROR = "La sauvegarde du profil a échoué. Vos modifications n'ont pas été enregistrées."

# Executor panel — labels
C_EXEC_SAVED_DATE_FMT = "Sauvegardé le : {date}"
C_EXEC_SAVED_DATE_EMPTY = "Sauvegardé le : --"
C_EXEC_USED_DATE_FMT = "{date}"
C_EXEC_USED_DATE_EMPTY = "--"

# Debug panel — session launch validation errors
C_DEBUG_URL_EMPTY = "L'URL ne peut pas être vide."
C_DEBUG_TIMEOUT_INVALID = "Le timeout doit être un entier entre 1 et 30 secondes."
C_DEBUG_DNS_DELAY_INVALID = "Le délai d'attente DNS doit être un entier entre 1 et 30 secondes."

# Scraping panel — no URL source confirmation dialog
C_SCRAPING_NO_URL_SOURCE_TITLE = "Aucune source d'URLs"

# Scraping panel — cancel confirmation dialog
C_SCRAPING_CANCEL_CONFIRM_TITLE = "Confirmer l'annulation"
C_SCRAPING_CANCEL_CONFIRM_MSG = "Êtes-vous sûr de vouloir annuler le processus en cours ?"

# -----------------------------------------------------------------------------
# Common dialog / presenter messages
# -----------------------------------------------------------------------------

# Generic error dialog title used in all show_error(title, …) calls.
C_ERROR_DIALOG_TITLE = "Erreur"

# Open-folder error messages ({exc} is the caught exception).
C_LOG_OPEN_FOLDER_ERROR = "Impossible d'ouvrir le dossier des logs :\n{exc}"
C_OPEN_EXPORT_FOLDER_ERROR = "Impossible d'ouvrir le dossier d'export :\n{exc}"

# Workflow session guard — shown when a second edit session is attempted.
C_WORKFLOW_ALREADY_ACTIVE_WARNING = (
    "Un Workflow est déjà en cours de modification.\n"
    "Veuillez terminer ou annuler la modification en cours avant de continuer."
)

# Scenario/profile operation errors ({exc} is the caught exception).
C_DUPLICATE_SCENARIO_FAILED = "La duplication a échoué : {exc}"
C_DELETE_SCENARIO_FAILED = "La suppression a échoué : {exc}"

# Step-not-found warning in StepsListPresenter.
C_STEP_NOT_FOUND_FOR_UPDATE = "L'étape n'existe plus. Impossible de mettre à jour."

# Scenario-not-found error in WorkflowPresenter ({id_file} is the missing ID).
C_SCENARIO_NOT_FOUND_BY_ID = "Le scénario avec l'ID '{id_file}' n'existe pas."

# -----------------------------------------------------------------------------
# Discover panel
# -----------------------------------------------------------------------------

# Project management labels
C_DISCOVER_SAVED_DATE_FMT = "Sauvegardé le : {date}"
C_DISCOVER_SAVED_DATE_EMPTY = "Sauvegardé le : --"
C_DISCOVER_RENAME_DIALOG_TITLE = "Renommer le projet"
C_DISCOVER_RENAME_DIALOG_MSG = "Nouveau nom du projet :"
C_DISCOVER_DELETE_CONFIRM_TITLE = "Supprimer le projet"
C_DISCOVER_DELETE_CONFIRM_MSG = "Êtes-vous sûr de vouloir supprimer le projet '{name}' ?"

# Verification labels
C_DISCOVER_FILES_COUNT_OK = "{count} fichier(s)"
C_DISCOVER_FILES_COUNT_ZERO = "Aucun fichier"
C_DISCOVER_FILES_COUNT_ERROR = "Erreur : {exc}"
C_DISCOVER_URLS_COUNT_OK = "{count} URL(s)"
C_DISCOVER_URLS_COUNT_ZERO = "Aucun URL"
C_DISCOVER_URLS_COUNT_COMPUTING = "Calcul en cours..."
C_DISCOVER_URLS_COUNT_ERROR = "Erreur : {exc}"

# Compute result label
C_DISCOVER_COMPUTE_OK = (
    "Entrée : {in_total} total, {in_unique} unique(s), {in_dupes} doublon(s)"
    "  —  Sortie : {out_total} total, {out_unique} unique(s), {out_dupes} doublon(s)"
    "  —  {new_count} nouvelle(s) URL(s)."
)

# Profile save result labels
C_DISCOVER_PROFILE_SAVE_OK = "{count} lien(s) ajouté(s) au profil."
C_DISCOVER_PROFILE_SAVE_ZERO = "Aucun nouveau lien à ajouter."
C_DISCOVER_PROFILE_SAVE_ERROR = "Erreur lors de la sauvegarde : {exc}"

# Profile save button blocking hints
C_DISCOVER_SAVE_LIST_HINT_INPUT = "URLs d'entrée non valides"
C_DISCOVER_SAVE_LIST_HINT_OUTPUT = "URLs de sortie non valides"
C_DISCOVER_SAVE_LIST_HINT_BOTH = "URLs d'entrée et de sortie non valides"
C_DISCOVER_SAVE_LIST_HINT_NO_NAME = "Nom du profil vide"

# Error messages
C_DISCOVER_PROJECT_NAME_EMPTY = "Le nom du projet ne peut pas être vide."
C_DISCOVER_SAVE_FAILED = "La sauvegarde a échoué : {exc}"
C_DISCOVER_NO_PROFILE_SELECTED = "Veuillez sélectionner un profil."

# -----------------------------------------------------------------------------
# Labels
# -----------------------------------------------------------------------------


# Mapping of module names to their corresponding black and white icon resource names.
# Order of modules is determined by the order of entries in this dictionary.
C_LISTING_MODULES: dict[TitleModuleEnum, tuple[str, str, str]] = {
    TitleModuleEnum.E_LOGS: ("Journal", C_RESS_ICON_BLACK_LOGS, C_RESS_ICON_WHITE_LOGS),
    TitleModuleEnum.E_DISCOVER: ("Découvrir", C_RESS_ICON_BLACK_DISCOVER, C_RESS_ICON_WHITE_DISCOVER),
    TitleModuleEnum.E_PROFILES: ("Profils", C_RESS_ICON_BLACK_PROFILES, C_RESS_ICON_WHITE_PROFILES),
    TitleModuleEnum.E_SCENARIOS: ("Scénarios", C_RESS_ICON_BLACK_SCENARIOS, C_RESS_ICON_WHITE_SCENARIOS),
    TitleModuleEnum.E_WORKFLOW: ("Modifier", C_RESS_ICON_BLACK_EDITOR, C_RESS_ICON_WHITE_EDITOR),
    TitleModuleEnum.E_EXECUTOR: ("Exécuter", C_RESS_ICON_BLACK_EXECUTOR, C_RESS_ICON_WHITE_EXECUTOR),
    TitleModuleEnum.E_SCRAPING: ("Scraping", C_RESS_ICON_BLACK_SCRAPING, C_RESS_ICON_WHITE_SCRAPING),
    TitleModuleEnum.E_FAQ: ("F.A.Q.", C_RESS_ICON_BLACK_FAQ, C_RESS_ICON_WHITE_FAQ),
    TitleModuleEnum.E_DEBUG: ("Debug", C_RESS_ICON_BLACK_DEBUG, C_RESS_ICON_WHITE_DEBUG),
    TitleModuleEnum.E_OPTIONS: ("Options", C_RESS_ICON_BLACK_CONFIG, C_RESS_ICON_WHITE_CONFIG),
}


# French display labels for each step type (Combobox values).
C_STEP_TYPE_TO_LABELS: dict[StepTypeEnum, str] = {
    StepTypeEnum.E_SECTION_STEPS: "Section",
    StepTypeEnum.E_OPEN_URL: "Ouvrir une URL",
    StepTypeEnum.E_CHECK_URL_PAGE: "Vérifier URL de la page",
    StepTypeEnum.E_CLOSE_TABS: "Fermer des onglets",
    StepTypeEnum.E_REFRESH_PAGE: "Rafraîchir la page",
    StepTypeEnum.E_WAIT_PAGE_STATE: "Attendre un état de page",
    StepTypeEnum.E_WAIT_FIXED_TIME: "Attendre une durée fixe",
    StepTypeEnum.E_WAIT_USER_ACTION: "Attendre action manuelle",
    StepTypeEnum.E_COUNT_HTML_ELEMENTS: "Compter les éléments",
    StepTypeEnum.E_COUNT_HTML_IMAGES: "Compter les images",
    StepTypeEnum.E_WAIT_HTML_ELEMENTS: "Attendre X éléments",
    StepTypeEnum.E_WAIT_HTML_IMAGES: "Attendre X images",
    StepTypeEnum.E_CLICK_ON_ELEMENT: "Cliquer sur un élément",
    StepTypeEnum.E_CLICK_FOR_DOWNLOAD: "Cliquer pour télécharger",
    StepTypeEnum.E_DOWNLOAD_IMAGE: "Télécharger les images",
    StepTypeEnum.E_YOUTUBE_DDL: "YouTube info/srt",
    StepTypeEnum.E_EXTRACT_TEXTS: "Extraire textes de la page",
    StepTypeEnum.E_EXTRACT_LINKS: "Extraire liens de la page",
    StepTypeEnum.E_EXTRACT_VARIABLE: "Extraire variable système",
    StepTypeEnum.E_EXPORT_DATA_TO_JS: "Exporter données (json)",
    StepTypeEnum.E_JUMP_TO_STEP: "Sauter vers l'étape si...",
    StepTypeEnum.E_SCROLL_DOWN: "Défiler vers le bas",
    StepTypeEnum.E_KILL_BROWSER: "Quitter navigateur",
}

# -----------------------------------------------------------------------------
# Templates errors
# -----------------------------------------------------------------------------

ERROR_TEMPLATES: dict[str, str] = {
    # --- check_url_page ---
    "check_url_page_nothing_to_check": "Étape {step} : Choix vides. Cocher au minimum 1 case.",
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
    "export_data_to_js_prefix_file_required": "Étape {step} : Préfixe du fichier obligatoire.",
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
    "refresh_page_timeout_unit_invalid": "Étape {step} : l'unité de timeout invalide — {value!r}.",
    # --- scroll_down ---
    "scroll_down_pixels_invalid": "Étape {step} : le nombre de pixels doit être >= 1.",
    "scroll_down_nbr_loops_invalid": "Étape {step} : le nombre de boucles doit être entre 1 et 99.",
    "scroll_down_delay_pause_invalid": "Étape {step} : la pause doit être entre 1 et 99.",
    # --- section ---
    "section_title_required": "Étape {step} : le titre de la section est obligatoire.",
    # --- youtube_transcripts ---
    "youtube_transcripts_title_required": "Étape {step} : Le titre est obligatoire.",
    # --- export_variable ---
    "export_variable_invalid": "Étape {step} : variable invalide — {value!r}.",
    "export_variable_mapping_required": "Étape {step} : la clé de mapping est obligatoire.",
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
    # --- wait_user_action ---
    "wait_user_action_condition_invalid": "Étape {step} : condition invalide — {value!r}.",
    "wait_user_action_wait_duration_invalid": "Étape {step} : le délai post-reprise doit être >= 1.",
    "wait_user_action_wait_unit_invalid": "Étape {step} : l'unité de temps est invalide — {value!r}.",
    # --- wait_fixed_time ---
    "wait_fixed_time_duration_invalid": "Étape {step} : la durée d'attente doit être >= 0.",
}

# EOF
