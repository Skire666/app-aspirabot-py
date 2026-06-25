# Main view sidebar width in pixels

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.enums import StepTypeEnum, TitleModuleEnum
from shared.resources_icons_util import (
    C_RESS_ICON_BLACK_CONFIG,
    C_RESS_ICON_BLACK_DEBUG,
    C_RESS_ICON_BLACK_EDITOR,
    C_RESS_ICON_BLACK_EXECUTOR,
    C_RESS_ICON_BLACK_FAQ,
    C_RESS_ICON_BLACK_LOGS,
    C_RESS_ICON_BLACK_PROFILES,
    C_RESS_ICON_BLACK_SCENARIOS,
    C_RESS_ICON_BLACK_SCRAPING,
    C_RESS_ICON_WHITE_CONFIG,
    C_RESS_ICON_WHITE_DEBUG,
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
C_EXEC_NO_PROFILE = "Veuillez sélectionner un profil de lancement."
C_EXEC_NO_EXPORT_FOLDER = "Le dossier d'export est requis."
C_EXEC_NO_URL_SOURCE = "Veuillez configurer une source d'URL."
C_EXEC_INVALID_GLOBAL_THRESHOLD = "Le seuil global d'erreurs doit être un entier entre 1 et 9 999 999."
C_EXEC_STEP_THRESHOLD_WITHOUT_STEP = "Veuillez sélectionner une étape pour le seuil par étape."
C_EXEC_INVALID_STEP_THRESHOLD = "Le seuil par étape doit être un entier entre 1 et 9 999 999."
C_EXEC_SAVE_ERROR = "La sauvegarde du profil a échoué. Vos modifications n'ont pas été enregistrées."

# Discover panel — validation and status messages
C_DISCOVER_NO_ENTRIES_IN = "Veuillez ajouter au moins une entrée [IN] dans le tableau."
C_DISCOVER_NO_ENTRIES_OUT = "Veuillez alimenter la sortie [OUT]."
C_DISCOVER_NO_URLS_COMPUTED = "Aucune nouvelle URL trouvée. Cliquez sur 'Calculer la liste' d'abord."
C_DISCOVER_COMPUTE_SUCCESS = (
    "Succès : +{new} nouvelle(s) URL(s) = IN : x{total_in} unique(s) - OUT : x{total_out} unique(s)"
)
C_DISCOVER_COMPUTE_ERROR = "Erreur lors du calcul : {exc}"
C_DISCOVER_DELETE_CONFIRM_TITLE = "Confirmer la suppression"
C_DISCOVER_DELETE_CONFIRM_MSG = "Supprimer cette entrée [IN] ?"

# Executor panel — labels
C_EXEC_SAVED_DATE_FMT = "Sauvegardé le : {date}"
C_EXEC_SAVED_DATE_EMPTY = "Sauvegardé le : --"
C_EXEC_USED_DATE_FMT = "{date}"
C_EXEC_USED_DATE_EMPTY = "--"

# Debug panel — session launch validation errors
C_DEBUG_URL_EMPTY = "L'URL ne peut pas être vide."
C_DEBUG_TIMEOUT_INVALID = "Le timeout doit être un entier entre 1 et 30 secondes."
C_DEBUG_DNS_DELAY_INVALID = "Le délai d'attente DNS doit être un entier entre 1 et 30 secondes."
C_DEBUG_REFRESH_ERROR = "Erreur lors du rafraîchissement."
C_DEBUG_TEXTS_ERROR = "Erreur lors de l'analyse des textes."
C_DEBUG_IMAGES_ERROR = "Erreur lors de l'analyse des images."
C_DEBUG_LOADING = "Chargement en cours…"

# Configuration panel — last-write timestamp label
C_CONFIG_LAST_WRITE_EMPTY = "Dernière écriture : --"
C_CONFIG_LAST_WRITE_FMT = "Dernière écriture : {date}"

# Confirmation dialogs (shared)
C_DIALOG_CONFIRM_TITLE = "Confirmer"
C_DIALOG_DUPLICATE_SCENARIO_MSG = "Voulez-vous dupliquer ce scénario ?"
C_DIALOG_DELETE_SCENARIO_MSG = "Voulez-vous vraiment supprimer ce scénario ?"
C_DIALOG_DELETE_PROFILE_MSG = "Voulez-vous vraiment supprimer le profil « {profile_name} » ?"

# Scraping panel — no URL source confirmation dialog
C_SCRAPING_NO_URL_SOURCE_TITLE = "Aucune source d'URLs"

# Scraping panel — cancel confirmation dialog
C_SCRAPING_CANCEL_CONFIRM_TITLE = "Confirmer l'annulation"
C_SCRAPING_CANCEL_CONFIRM_MSG = "Êtes-vous sûr de vouloir annuler le processus en cours ?"

# -----------------------------------------------------------------------------
# Folder setup dialog (first-launch, when folder_scenarios is unconfigured)
# -----------------------------------------------------------------------------

C_FOLDER_SETUP_TITLE = "Configuration initiale"
C_FOLDER_SETUP_DESCRIPTION = (
    "Le dossier de stockage des scénarios n'est pas encore configuré.\n"
    "Veuillez indiquer le chemin du dossier à utiliser."
)
C_FOLDER_SETUP_PATH_LABEL = "Dossier des scénarios :"
C_FOLDER_SETUP_BROWSE_BTN = "Parcourir…"
C_FOLDER_SETUP_CONFIRM_BTN = "Confirmer"
C_FOLDER_SETUP_CANCEL_BTN = "Annuler"
C_FOLDER_SETUP_INVALID_PATH = "Le chemin renseigné n'est pas valide."
C_FOLDER_SETUP_CREATE_ERROR = "Impossible de créer le dossier : {exc}"
C_FOLDER_SETUP_ABORTED = (
    "La configuration du dossier des scénarios est requise pour démarrer l'application."
)
C_FOLDER_SETUP_DEFAULT_WARNING_TITLE = "Dossier par défaut utilisé"
C_FOLDER_SETUP_DEFAULT_WARNING_MSG = (
    "Aucun dossier configuré pour les scénarios.\n"
    "Le dossier par défaut « {path} » sera utilisé.\n\n"
    "Vous pouvez modifier ce paramètre depuis l'onglet Options."
)

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
# Labels
# -----------------------------------------------------------------------------


# Mapping of module names to their corresponding black and white icon resource names.
# Order of modules is determined by the order of entries in this dictionary.
C_LISTING_MODULES: dict[TitleModuleEnum, tuple[str, str, str]] = {
    TitleModuleEnum.E_LOGS: ("Journal", C_RESS_ICON_BLACK_LOGS, C_RESS_ICON_WHITE_LOGS),
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
    StepTypeEnum.E_SCROLL_DOWN: "Défiler vers le bas",
    StepTypeEnum.E_DOWNLOAD_IMAGE: "Télécharger les images",
    StepTypeEnum.E_YOUTUBE_SUBTITLES: "Télécharger SRT - Youtube",
    StepTypeEnum.E_YOUTUBE_EXTRACT_INFOS: "Extraire infos vidéo - Youtube",
    StepTypeEnum.E_EXTRACT_TEXTS: "Extraire : Textes de la page",
    StepTypeEnum.E_EXTRACT_LINKS: "Extraire : Liens de la page",
    StepTypeEnum.E_EXTRACT_VARIABLE: "Extraire : variable système",
    StepTypeEnum.E_EXPORT_DATA_TO_JS: "Exporter données (json)",
    StepTypeEnum.E_JUMP_TO_STEP: "Sauter vers l'étape si...",
    StepTypeEnum.E_RESTART_TO_BEGINNING: "Recommencer au début",
    StepTypeEnum.E_KILL_BROWSER: "Quitter navigateur",
}

# -----------------------------------------------------------------------------
# Templates errors
# -----------------------------------------------------------------------------

ERROR_TEMPLATES: dict[str, str] = {
    # shared
    "field_comment_required": "[{step}.] : commentaire requis (important pour log).",
    "filed_comment_too_long": "[{step}.] : Le commentaire ne doit pas dépasser 50 caractères.",
    # --- check_url_page ---
    "check_url_page_nothing_to_check": "[{step}.] : Choix vides. Cocher au minimum 1 case.",
    # --- restart_to_beginning ---
    "restart_to_beginning_comment_too_long": "[{step}.] : Le commentaire ne doit pas dépasser 120 caractères.",
    # --- Shared image dimension validation (download_image, count_html_images, wait_html_images) ---
    "image_dim_not_int": "[{step}.] : {key} doit être un nombre entier.",
    "image_dim_negative": "[{step}.] : {key} doit être >= 0.",
    "image_dim_max_below_one": "[{step}.] : {key} doit être >= 1.",
    "image_dim_range_invalid": "[{step}.] : {min_key} doit être <= {max_key}.",
    # --- click_element ---
    "click_element_selector_required": "[{step}.] : le sélecteur CSS est obligatoire.",
    "click_element_index_invalid": "[{step}.] : l'index du bouton à cliquer est invalide.",
    # --- close_tabs ---
    "close_tabs_filter_required": "[{step}.] : le filtre URL est obligatoire.",
    "close_tabs_max_tabs_invalid": "[{step}.] : le nombre max. d'onglets doit être >= 1.",
    # --- count_html_elements ---
    "count_html_elements_selector_required": "[{step}.] : le sélecteur CSS est obligatoire.",
    "count_html_elements_value_negative": "[{step}.] : value doit être >= 0.",
    "count_html_elements_success_if_invalid": "[{step}.] : success_if invalide — {value!r}.",
    "count_html_elements_operator_invalid": "[{step}.] : operator invalide — {value!r}.",
    # --- count_html_images ---
    "count_html_images_value_negative": "[{step}.] : value doit être >= 0.",
    "count_html_images_success_if_invalid": "[{step}.] : success_if invalide — {value!r}.",
    "count_html_images_operator_invalid": "[{step}.] : operator invalide — {value!r}.",
    # --- end_process ---
    "end_process_wait_duration_invalid": "[{step}.] : la durée d'attente doit être >= 0.",
    "end_process_wait_unit_invalid": "[{step}.] : unité de temps invalide — {value!r}.",
    # --- export data to js ---
    "export_data_to_js_prefix_file_required": "[{step}.] : Préfixe du fichier obligatoire.",
    # --- all extracts with mapping ---
    "extract_key_mapping_already_used": "[{step}.] : clé de mapping déjà utilisé.",
    # --- extract_links ---
    "extract_links_selector_required": "[{step}.] : le sélecteur CSS est obligatoire.",
    "extract_links_target_invalid": "[{step}.] : cible '{value}' invalide.",
    "extract_links_mapping_required": "[{step}.] : clé de mapping est obligatoire.",
    # --- extract_texts ---
    "extract_texts_selector_required": "[{step}.] : le sélecteur CSS est obligatoire.",
    "extract_texts_mode_invalid": "[{step}.] : mode d'extraction '{value}' invalide.",
    "extract_texts_target_invalid": "[{step}.] : cible '{value}' invalide.",
    "extract_texts_mapping_required": "[{step}.] : la clé de mapping est obligatoire.",
    # --- jump_to_step ---
    "jump_to_step_condition_invalid": "[{step}.] : condition invalide — {value}.",
    "jump_to_step_target_missing": "[{step}.] : aucune étape référencée.",
    "jump_to_step_self_reference": "[{step}.] : ne peut pas pointer vers elle-même.",
    "jump_to_step_target_not_found": "[{step}.] : la cible [{value}] est introuvable.",
    # --- open_url ---
    "open_url_url_required": "[{step}.] : l'URL est obligatoire.",
    "open_url_wait_dns_solver_invalid": "[{step}.] : Délai DNS doit être 1 <= x <= 30 sec.",
    "open_url_timeout_invalid": "[{step}.] : le timeout doit être >= 1.",
    "open_url_timeout_unit_invalid": "[{step}.] : l'unité de timeout est invalide.",
    # --- refresh_page ---
    "refresh_page_timeout_invalid": "[{step}.] : le timeout doit être >= 1.",
    "refresh_page_timeout_unit_invalid": "[{step}.] : l'unité de timeout invalide — {value!r}.",
    # --- scroll_down ---
    "scroll_down_pixels_invalid": "[{step}.] : le nombre de pixels doit être >= 1.",
    "scroll_down_nbr_loops_invalid": "[{step}.] : le nombre de boucles doit être entre 1 et 999.",
    "scroll_down_delay_pause_invalid": "[{step}.] : la pause doit être entre 1 et 99.",
    # --- section ---
    "section_title_required": "[{step}.] : le titre de la section est obligatoire.",
    # --- export_variable ---
    "export_variable_invalid": "[{step}.] : variable invalide — {value!r}.",
    "export_variable_mapping_required": "[{step}.] : la clé de mapping est obligatoire.",
    # --- wait_html_elements ---
    "wait_html_elements_selector_required": "[{step}.] : le sélecteur CSS est obligatoire.",
    "wait_html_elements_operator_invalid": (
        "[{step}.] : l'opérateur doit être l'un des suivants : "
        "equal, not_equal, greater_than, less_than, greater_or_equal, less_or_equal."
    ),
    "wait_html_elements_quantity_negative": "[{step}.] : la quantité doit être >= 0.",
    "wait_html_elements_retry_delay_invalid": "[{step}.] : le délai de retry doit être >= 1.",
    "wait_html_elements_retry_unit_invalid": "[{step}.] : l'unité de retry est invalide.",
    "wait_html_elements_retry_max_invalid": "[{step}.] : le nombre maximum de retry doit être >= 1.",
    # --- wait_html_images ---
    "wait_html_images_operator_invalid": (
        "[{step}.] : l'opérateur doit être l'un des suivants : "
        "equal, not_equal, greater_than, less_than, greater_or_equal, less_or_equal."
    ),
    "wait_html_images_quantity_negative": "[{step}.] : la quantité doit être >= 0.",
    "wait_html_images_retry_delay_invalid": "[{step}.] : le délai de retry doit être >= 1.",
    "wait_html_images_retry_unit_invalid": "[{step}.] : l'unité de retry est invalide.",
    "wait_html_images_retry_max_invalid": "[{step}.] : le nombre maximum de retry doit être >= 1.",
    # --- wait_page_state ---
    "wait_page_state_timeout_invalid": "[{step}.] : le timeout doit être >= 1.",
    "wait_page_state_timeout_unit_invalid": "[{step}.] : l'unité de timeout est invalide.",
    # --- wait_user_action ---
    "wait_user_action_condition_invalid": "[{step}.] : condition invalide — {value!r}.",
    "wait_user_action_wait_duration_invalid": "[{step}.] : le délai post-reprise doit être >= 1.",
    "wait_user_action_wait_unit_invalid": "[{step}.] : l'unité de temps est invalide — {value!r}.",
    # --- wait_fixed_time ---
    "wait_fixed_time_duration_invalid": "[{step}.] : la durée d'attente doit être >= 0.",
}

# EOF
