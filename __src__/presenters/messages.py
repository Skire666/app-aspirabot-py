"""User-facing message templates for all presenters.

All user-visible strings are defined here.  No presenter, service, or view
may ever write a user-facing string inline; every message must be formatted
from one of the templates below.

Example:
    >>> msg = ERROR_TEMPLATES["image_dim_not_int"].format(step="02", key="height_min")
    >>> msg
    "Étape 02 : height_min doit être un nombre entier."
"""

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

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

    # --- wait_x_time ---
    "wait_x_time_duration_invalid": "Étape {step} : la durée d'attente doit être >= 0.",
}
