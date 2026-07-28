"""Per-step-type label formatters for the workflow list renderer.

Each private function converts a serialised step params dict to a short
French display string.  The public ``format_step_label`` dispatcher routes
by StepTypeEnum.  No Tkinter is imported here — this module belongs to the
Presenter layer and must stay UI-agnostic.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from shared.constants import (
    C_MAXIMUM_SIZE_IMAGE,
    C_STATE_JUMP_TO_STEP_FAILURE,
    C_UNITS_TIME_ALLOWED_FOR_MODEL,
    C_UNITS_TIME_ALLOWED_FOR_VIEW,
)
from shared.enums import FilterClosedEnum, StepTypeEnum

# -----------------------------------------------------------------------------
# Module-level display mappings
# -----------------------------------------------------------------------------

# Model code → French display label (e.g. "s" → "sec")
_WAIT_UNIT_MODEL_TO_VIEW: dict[str, str] = dict(
    zip(C_UNITS_TIME_ALLOWED_FOR_MODEL, list(C_UNITS_TIME_ALLOWED_FOR_VIEW), strict=True)
)

# Operator internal name → mathematical symbol
_OP_LABELS: dict[str, str] = {
    "equal": "==",
    "not_equal": "!=",
    "greater_than": ">",
    "less_than": "<",
    "greater_or_equal": ">=",
    "less_or_equal": "<=",
}

# Minimum image dimension default shared across image-related steps
_C_DEFAULT_IMG_SIZE_MIN: int = 250

# Beyond this length, the aggregators list preview is truncated with an ellipsis
_C_MAX_AGGREGATORS_PREVIEW_LEN: int = 25

# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------


def format_step_label(
    step_type: StepTypeEnum, params_dict: dict[str, Any], idx: int, context_ids: dict[str, int]
) -> str:
    """Return the French display label for one step in the workflow list.

    Dispatches to the per-type private formatter registered in ``_REGISTRY``.
    Falls back to the enum value string when no formatter is registered.

    Args:
        step_type: The step type enum member identifying the formatter.
        params_dict: Serialised step parameters from ``IStepParams.to_dict()``.
        idx: Zero-based position of the step in the workflow (unused by most
            formatters, passed through for completeness and future use).
        context_ids: ``{step_id: zero_based_index}`` mapping used by cross-step
            formatters such as ``E_JUMP_TO_STEP``.

    Returns:
        Short multi-line French display string for the DragDropList renderer.
    """
    formatter = _REGISTRY.get(step_type)
    if formatter is None:
        return step_type.value
    return formatter(params_dict, idx, context_ids)


# -----------------------------------------------------------------------------
# Per-type formatters — private, ordered by StepTypeEnum name
# -----------------------------------------------------------------------------


def _fmt_check_url_page(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for CHECK_URL_PAGE."""
    domain_str = "oui" if params.get("check_domain") else "non"
    path_str = "oui" if params.get("check_path") else "non"
    url_contains = params.get("url_contains", "") or "<_vide_>"
    url_end_with = params.get("url_end_with", "") or "<_vide_>"

    return (
        f"Vérifier URL  |  Même domaine : {domain_str}  |  Même chemin : {path_str}\n"
        f"L'URL contient : {url_contains}  |  Se termine par : {url_end_with}"
    )


def _fmt_restart_to_beginning(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for RESTART_TO_BEGINNING."""
    urls_str = (
        "Uniquement si URL restantes"
        if params.get("jump_only_if_urls_remaining")
        else "Toujours (aucune vérif. si URL restantes)"
    )
    return f"Recommencer au début.\n{urls_str}"


def _fmt_click_for_download(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for CLICK_FOR_DOWNLOAD."""
    selector = params.get("selector") or "<vide>"
    index_clicked = params.get("index_clicked", 0)
    return f"Cliquer pour télécharger  -  Index {index_clicked}\nSél. : {selector}"


def _fmt_click_on_element(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for CLICK_ON_ELEMENT."""
    selector = params.get("selector") or "<vide>"
    index_clicked = params.get("index_clicked", 0)
    return f"Cliquer sur un élément  -  Index {index_clicked}\nSél. {selector})"


def _fmt_close_tabs(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for CLOSE_TABS."""
    max_tabs = params.get("max_tabs", 1)
    filter_mode = params.get("filter_mode", FilterClosedEnum.E_SOURCE.value)
    if filter_mode == FilterClosedEnum.E_CUSTOM.value:
        filter_custom = params.get("filter_custom", "")
        return f"Fermer les onglets  -  {max_tabs} onglet(s) max.\nFiltre URL : *{filter_custom}*"
    return f"Fermer les onglets  -  {max_tabs} onglet(s) max.\nFiltre : Garde l'URL de départ."


def _fmt_count_html_elements(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for COUNT_HTML_ELEMENTS."""
    op = _OP_LABELS.get(params.get("operator", ""), "?")
    selector = params.get("selector") or "<vide>"
    val_str = str(params.get("value", 1))
    return f"Compter les éléments  -  Doit être {op} {val_str}\nSél. : {selector}"


def _fmt_count_html_images(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for COUNT_HTML_IMAGES."""
    op = _OP_LABELS.get(params.get("operator", ""), "?")
    val_str = str(params.get("value", 1))
    width_min = params.get("width_min", _C_DEFAULT_IMG_SIZE_MIN)
    height_min = params.get("height_min", _C_DEFAULT_IMG_SIZE_MIN)
    width_max = params.get("width_max", C_MAXIMUM_SIZE_IMAGE)
    height_max = params.get("height_max", C_MAXIMUM_SIZE_IMAGE)
    return (
        f"Compter les images  -  Doit être {op} {val_str}\n"
        f"Taille : {width_min}x{height_min} -> {width_max}x{height_max}"
    )


def _fmt_download_image(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for DOWNLOAD_IMAGE."""
    mode = params.get("mode", "all")
    unique_only = bool(params.get("unique_only", True))
    width_min = params.get("width_min", _C_DEFAULT_IMG_SIZE_MIN)
    height_min = params.get("height_min", _C_DEFAULT_IMG_SIZE_MIN)
    width_max = params.get("width_max", C_MAXIMUM_SIZE_IMAGE)
    height_max = params.get("height_max", C_MAXIMUM_SIZE_IMAGE)
    dup_str = "(doublons refusés)" if unique_only else "(doublons autorisés)"
    return f"Télécharger images {dup_str}\n{mode}  -  Taille : {width_min}x{height_min} -> {width_max}x{height_max}"


def _fmt_export_data_to_js(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for EXPORT_DATA_TO_CSV."""
    csv_fname = params.get("csv_filename") or "<vide>"
    aggregators = params.get("aggregators_list") or "<vide>"
    pp = (
        f"{aggregators.replace(chr(10), ''):.{_C_MAX_AGGREGATORS_PREVIEW_LEN}}...(len x{len(aggregators)})"
        if len(aggregators) > _C_MAX_AGGREGATORS_PREVIEW_LEN
        else aggregators
    )
    return f"Exporter vers fichier CSV - Préfixe : {csv_fname} (.csv)\nAgréger : {pp}"


def _fmt_extract_links(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for EXTRACT_LINKS."""
    selector = params.get("selector") or "<vide>"
    target = params.get("target", "")
    mapping = params.get("mapping", "")
    return f"Extraire liens  -  Clé : {mapping}\nCible : {target}  |  Sél. : {selector}"


def _fmt_extract_js_custom(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for EXTRACT_JS_CUSTOM."""
    return "Extraction - JS Personnalisé"


def _fmt_extract_texts(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for EXTRACT_TEXTS."""
    selector = params.get("selector") or "<vide>"
    extract_mode = params.get("extract_mode", "")
    target = params.get("target", "")
    mapping = params.get("mapping", "")
    return f"Extraire textes  -  Clé : {mapping}  -  Cible : {target}\nMode : {extract_mode}  |  Sél. : {selector}"


def _fmt_jump_to_step(params: dict[str, Any], _idx: int, ctx: dict[str, int]) -> str:
    """Format label for JUMP_TO_STEP — resolves target position from context_ids."""
    target_hexastring = params.get("target_hexastring", "") or "????"
    idx_found = ctx.get(target_hexastring)
    if idx_found is None:
        target_hexastring = "????"
        target_index = "??"
    else:
        target_index = str(idx_found + 1).zfill(2)
    cond = params.get("condition", "")
    if cond == "success":
        return f"Sauter vers l'étape - si était un succès\nSe rendre à {target_index}.  #{target_hexastring}"
    if cond == C_STATE_JUMP_TO_STEP_FAILURE:
        return f"Sauter vers l'étape - si était un échec\nSe rendre à {target_index}.  #{target_hexastring}"
    return f"Sauter vers l'étape - [TOUJOURS]\nAller à {target_index}.  #{target_hexastring}"


def _fmt_kill_browser(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for KILL_BROWSER."""
    unit_time = params.get("wait_unit", "")
    unit_display = _WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)
    qty_time = params.get("wait_duration", 3)
    return f"Quitter navigateur\nAttendre {qty_time} {unit_display} avant de quitter"


def _fmt_open_url(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for OPEN_URL."""
    timeout_duration = params.get("timeout_duration", 10)
    timeout_unit = params.get("timeout_unit", "")
    unit_display = _WAIT_UNIT_MODEL_TO_VIEW.get(timeout_unit, timeout_unit)
    url_mode = params.get("url_mode", FilterClosedEnum.E_SOURCE.value)
    if url_mode == FilterClosedEnum.E_SOURCE.value:
        url_used = "Prochaine URL dans la source"
    else:
        url_used = f"Url : {params.get('url_custom', '')}"
    return f"Ouvrir une URL  -  timeout : {timeout_duration} {unit_display}\n{url_used}"


def _fmt_refresh_page(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for REFRESH_PAGE."""
    clear_cache = bool(params.get("clear_cache"))
    mode_str = "Vide le cache (Ctrl+F5)" if clear_cache else "Garde le cache (F5)"
    timeout = params.get("timeout_duration", 10)
    unit_time = params.get("timeout_unit", "")
    unit_display = _WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)
    wait_until = params.get("wait_until", "networkidle")
    return f"Rafraîchir la page  -  timeout : {timeout} {unit_display}\n{mode_str}  -  Attendre : {wait_until}"


def _fmt_scroll_down(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for SCROLL_DOWN."""
    pixels = params.get("pixels", 1000)
    nbr_loops = params.get("nbr_loops", 1)
    delay_pause = params.get("delay_pause", 1)
    return f"Défilement vers le bas\nLongueur: {pixels} px  —  x{nbr_loops} boucle(s)  —  pause: {delay_pause}"


def _fmt_section(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for SECTION_STEPS."""
    title = params.get("title", "")
    return f"- - - - {title} - - - -"


def _fmt_youtube_infos_video(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for YOUTUBE_DDL."""
    return "YouTube - Extraire infos d'une page vidéo via yt-dlp"


def _fmt_youtube_subtitles(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for YOUTUBE_SUBTITLES."""
    return "Youtube - Télécharger les sous-titres vidéo via yt-dlp"


def _fmt_export_variable(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for EXTRACT_VARIABLE."""
    variable = params.get("variable", "")
    mapping = params.get("mapping", "")
    return f"Lire variable système  -  Clé : {mapping}\n{variable} -> calculé dynamiquement"


def _fmt_wait_fixed_time(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for WAIT_FIXED_TIME."""
    duration = params.get("duration", 3)
    unit_raw = params.get("unit", "")
    unit_display = _WAIT_UNIT_MODEL_TO_VIEW.get(unit_raw, unit_raw)
    return f"Attendre une durée fixe\n{duration} {unit_display}"


def _fmt_wait_html_elements(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for WAIT_HTML_ELEMENTS."""
    op = _OP_LABELS.get(params.get("operator", ""), "?")
    quantity = params.get("quantity", 1)
    selector = params.get("selector", "")
    return f"Attendre éléments  -  Attendu {op} {quantity}\nSél. : {selector}"


def _fmt_wait_html_images(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for WAIT_HTML_IMAGES."""
    retry_delay = params.get("retry_delay", 400)
    retry_unit = params.get("retry_unit", "")
    unit_display = _WAIT_UNIT_MODEL_TO_VIEW.get(retry_unit, retry_unit)
    width_min = params.get("width_min", _C_DEFAULT_IMG_SIZE_MIN)
    height_min = params.get("height_min", _C_DEFAULT_IMG_SIZE_MIN)
    width_max = params.get("width_max", C_MAXIMUM_SIZE_IMAGE)
    height_max = params.get("height_max", C_MAXIMUM_SIZE_IMAGE)
    return (
        f"Attendre images  -  Toutes les : {retry_delay} {unit_display}\n"
        f"Taille : {width_min}x{height_min} -> {width_max}x{height_max}"
    )


def _fmt_wait_page_state(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for WAIT_PAGE_STATE."""
    timeout = params.get("timeout_duration", 8)
    unit_time = params.get("timeout_unit", "")
    unit_display = _WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)
    wait_until = params.get("wait_until", "networkidle")
    return f"Attendre l'état de chargement  -  timeout : {timeout} {unit_display}\nAttendre : {wait_until}"


def _fmt_wait_user_action(params: dict[str, Any], _idx: int, _ctx: dict[str, int]) -> str:
    """Format label for WAIT_USER_ACTION."""
    cond_labels: dict[str, str] = {
        "success": "Si succès",
        C_STATE_JUMP_TO_STEP_FAILURE: "Si échec",
        "always": "Toujours",
    }
    condition = cond_labels.get(params.get("condition", ""), "Toujours")
    wd = params.get("wait_duration", 3)
    unit_time = params.get("wait_unit", "")
    unit_display = _WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)
    delay_str = f"Si reprise demandée, patienter {wd} {unit_display}" if wd > 0 else ""
    return f"{condition} attendre action manuelle\n{delay_str}"


# -----------------------------------------------------------------------------
# Dispatch registry — populated after all formatters are defined above
# -----------------------------------------------------------------------------

_FormatterFn = Callable[[dict[str, Any], int, dict[str, int]], str]

_REGISTRY: dict[StepTypeEnum, _FormatterFn] = {
    StepTypeEnum.E_CHECK_URL_PAGE: _fmt_check_url_page,
    StepTypeEnum.E_RESTART_TO_BEGINNING: _fmt_restart_to_beginning,
    StepTypeEnum.E_CLICK_FOR_DOWNLOAD: _fmt_click_for_download,
    StepTypeEnum.E_CLICK_ON_ELEMENT: _fmt_click_on_element,
    StepTypeEnum.E_CLOSE_TABS: _fmt_close_tabs,
    StepTypeEnum.E_COUNT_HTML_ELEMENTS: _fmt_count_html_elements,
    StepTypeEnum.E_COUNT_HTML_IMAGES: _fmt_count_html_images,
    StepTypeEnum.E_DOWNLOAD_IMAGE: _fmt_download_image,
    StepTypeEnum.E_EXPORT_DATA_TO_CSV: _fmt_export_data_to_js,
    StepTypeEnum.E_EXTRACT_LINKS: _fmt_extract_links,
    StepTypeEnum.E_EXTRACT_JS_CUSTOM: _fmt_extract_js_custom,
    StepTypeEnum.E_EXTRACT_TEXTS: _fmt_extract_texts,
    StepTypeEnum.E_JUMP_TO_STEP: _fmt_jump_to_step,
    StepTypeEnum.E_KILL_BROWSER: _fmt_kill_browser,
    StepTypeEnum.E_OPEN_URL: _fmt_open_url,
    StepTypeEnum.E_REFRESH_PAGE: _fmt_refresh_page,
    StepTypeEnum.E_SCROLL_DOWN: _fmt_scroll_down,
    StepTypeEnum.E_SECTION_STEPS: _fmt_section,
    StepTypeEnum.E_YOUTUBE_EXTRACT_INFOS: _fmt_youtube_infos_video,
    StepTypeEnum.E_YOUTUBE_SUBTITLES: _fmt_youtube_subtitles,
    StepTypeEnum.E_EXTRACT_VARIABLE: _fmt_export_variable,
    StepTypeEnum.E_WAIT_FIXED_TIME: _fmt_wait_fixed_time,
    StepTypeEnum.E_WAIT_HTML_ELEMENTS: _fmt_wait_html_elements,
    StepTypeEnum.E_WAIT_HTML_IMAGES: _fmt_wait_html_images,
    StepTypeEnum.E_WAIT_PAGE_STATE: _fmt_wait_page_state,
    StepTypeEnum.E_WAIT_USER_ACTION: _fmt_wait_user_action,
}


# EOF
