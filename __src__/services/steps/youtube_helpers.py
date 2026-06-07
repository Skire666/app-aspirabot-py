"""YouTube textual data downloader (basic metadata + subtitles) built on yt-dlp.

This module exposes ``download_youtube_txt_data`` as the only public entry point.
It is designed to be resilient against HTTP 429 rate-limiting and partial failures:
each language is processed independently, a placeholder file is written when a
track cannot be retrieved, and the function never raises — all outcomes are
captured in the returned :class:`DownloadResult`. The caller is responsible for
inspecting that summary and reacting to recorded errors.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Final, cast

import yt_dlp
from interfaces.i_scraping_event_bus import IScrapingEventBus
from models.scraping_context_model import ScrapingContextModel
from shared.datetime_util import C_TIMESTAMP_FILE_FORMAT_YYYY_MM_DD_HH_MM_SS_FFFFFF
from shared.exception_util import (
    YoutubeNoDownloadOptionError,
    YoutubeOutputDirParameterEmptyError,
    YoutubeUrlParameterEmptyError,
)
from shared.path_util import clean_filename_youtube
from yt_dlp.utils import DownloadError

# ============================================================================
# CONSTANTS (single source of truth — tune the behaviour from here)
# ============================================================================

LOGGER_NAME: Final[str] = "youtube_txt_downloader"

# --- Basic metadata fields to extract from yt-dlp's info dict ---------------
BASIC_DATA_FIELDS: Final[tuple[str, ...]] = (
    "id",
    "title",
    "fulltitle",
    "description",
    "display_id",
    "uploader",
    "uploader_id",
    "uploader_url",
    "timestamp",
    "upload_date",
    "channel",
    "channel_id",
    "channel_url",
    "channel_follower_count",
    "channel_is_verified",
    "duration",
    "duration_string",
    "view_count",
    "like_count",
    "comment_count",
    "availability",
    "extractor",
    "url",
    "webpage_url",
    "webpage_url_basename",
    "webpage_url_domain",
    "original_url",
    "categories",
    "tags",
)

# --- Language selection rules ----------------------------------------------
TARGET_LANG_PATTERNS: Final[tuple[str, ...]] = ("french", "english")
TARGET_LANG_CODES: Final[tuple[str, ...]] = ("fr", "en")
DEFAULT_SHORT_CODE: Final[str] = "UNDEF"

# --- Rate-limit / phase pacing ---------------------------------------------
RATE_LIMIT_RETRY_DELAYS: Final[tuple[int, ...]] = (1, 3)  # old = (0, 3, 5, 7)
PHASE_PAUSE_SECONDS: Final[int] = 1
HTTP_429_PATTERNS: Final[tuple[str, ...]] = ("429", "too many requests", "rate-limit")

# --- Subtitle formats ------------------------------------------------------
SUBTITLE_FORMATS: Final[str] = "srt/vtt/json3/best"  # ordre de préférence pour yt-dlp
SUBTITLE_EXTENSIONS_KEEP: Final[tuple[str, ...]] = ("srt", "vtt", "json3")

# --- Filename patterns -----------------------------------------------------
NA_TOKEN: Final[str] = "<<_#N/A_>>"
TIMESTAMP_FMT: Final[str] = C_TIMESTAMP_FILE_FORMAT_YYYY_MM_DD_HH_MM_SS_FFFFFF
BASIC_DATA_FILENAME_FMT: Final[str] = "{vid} - basic_data - {ts}.json"
SUBTITLE_FILENAME_FMT: Final[str] = "{vid} - {origin} - {lang} - {ts}.{ext}"
NA_FILENAME_FMT: Final[str] = "{vid} - {origin} - {lang} - {ts}.{ext}"
NA_PLACEHOLDER_EXT: Final[str] = "error"

# --- Origin tags used in subtitle filenames --------------------------------
ORIGIN_MANUAL: Final[str] = "srt_manual"
ORIGIN_AUTO: Final[str] = "srt_autogen"

# Module-level logger (configuration is left to the caller).
_logger: Final[logging.Logger] = logging.getLogger(LOGGER_NAME)


# ============================================================================
# RESULT CLASS — caller-facing summary
# ============================================================================


@dataclass(slots=True)
class DownloadResult:
    """Structured summary of a ``download_youtube_txt_data`` execution.

    Attributes:
        files_written: All files persisted to disk (metadata, subtitles,
            placeholders).
        files_downloaded: Subtitle files successfully retrieved from YouTube.
            This is a subset of ``files_written`` — it excludes the basic-data
            JSON and the error placeholders.
        warnings: Non-fatal events (retries on 429, missing languages replaced
            by placeholders, etc.).
        errors: Failures the caller must inspect and decide how to handle.
    """

    files_written: list[Path] = field(default_factory=list)
    files_downloaded: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    nbr_base_success: int = 0
    nbr_srt_success: int = 0

    @property
    def success(self) -> bool:
        """Return True when no error was recorded."""
        return not self.errors

    def warn(self, message: str) -> None:
        """Record a warning and log it."""
        self.warnings.append(message)
        _logger.warning(message)

    def fail(self, message: str) -> None:
        """Record an error and log it."""
        self.errors.append(message)
        _logger.error(message)


# ============================================================================
# PUBLIC ENTRY POINT
# ============================================================================


def download_youtube_data(
    url_youtube: str,
    output_dir: str,
    get_basic_data: bool,
    get_srt: bool,
    event_bus: IScrapingEventBus,
    ctx: ScrapingContextModel,
) -> DownloadResult:
    """Orchestrate the full pipeline; record outcomes into ``result``."""
    result: DownloadResult = DownloadResult()

    if not _safe_validate(url_youtube, output_dir, get_basic_data, get_srt, result):
        event_bus.log_step(ctx, f"Paramètres invalides : {result.errors[-1]}")
        return result
    out_path = _safe_prepare_dir(output_dir, result)
    if out_path is None:
        return result

    # basic info extraction (also serves as a validation step before attempting subs download)
    all_infos = _safe_fetch_info(url_youtube, result)
    if all_infos is None:
        return result
    video_id = str(all_infos.get("id") or "unknown")

    # choices
    if get_basic_data:
        _safe_save_basic_data(all_infos, out_path, video_id, result, event_bus, ctx)
    if get_srt:
        _safe_download_subtitles(url_youtube, all_infos, out_path, video_id, result, event_bus, ctx)

    return result


# ============================================================================
# PIPELINE ORCHESTRATION
# ============================================================================


def _safe_validate(
    url_youtube: str, output_dir: str, get_basic_data: bool, get_srt: bool, result: DownloadResult
) -> bool:
    """Validate inputs; on failure, record error and return False."""
    try:
        _validate_inputs(url_youtube, output_dir, get_basic_data, get_srt)
    except ValueError as exc:
        result.fail(f"Paramètres invalides : {exc}")
        return False
    else:
        return True


def _safe_prepare_dir(output_dir: str, result: DownloadResult) -> Path | None:
    """Create the output directory; on failure, record error and return None."""
    path = Path(output_dir)
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        result.fail(f"Création du dossier '{path}' impossible : {exc}")
        return None
    else:
        return path


def _safe_fetch_info(url_youtube: str, result: DownloadResult) -> dict[str, Any] | None:
    """Fetch video info; on failure, record error and return None."""
    try:
        return _fetch_video_info(url_youtube)
    except (DownloadError, RuntimeError) as exc:
        result.fail(f"Extraction des informations vidéo échouée : {exc}")
        return None


def _safe_save_basic_data(
    info: dict[str, Any],
    out_dir: Path,
    video_id: str,
    result: DownloadResult,
    event_bus: IScrapingEventBus,
    ctx: ScrapingContextModel,
) -> None:
    """Wrap ``_save_basic_data`` to capture any unexpected exception."""
    try:
        _save_basic_data(info, out_dir, video_id, result)
        event_bus.log_step(ctx, "Données basiques téléchargées.")
        result.nbr_base_success += 1
    except Exception as exc:  # noqa: BLE001
        result.fail(f"Données basiques (erreur inattendue) : {exc!r}")


def _safe_download_subtitles(
    url: str,
    info: dict[str, Any],
    out_dir: Path,
    video_id: str,
    result: DownloadResult,
    event_bus: IScrapingEventBus,
    ctx: ScrapingContextModel,
) -> None:
    """Wrap ``_download_subtitles`` to capture any unexpected exception."""
    try:
        _download_subtitles(url, info, out_dir, video_id, result, event_bus, ctx)
    except Exception as exc:  # noqa: BLE001
        result.fail(f"Sous-titres (erreur inattendue) : {exc!r}")


# ============================================================================
# INPUT VALIDATION
# ============================================================================


def _validate_inputs(url_youtube: str, output_dir: str, get_basic_data: bool, get_srt: bool) -> None:
    """Validate the public entry point arguments, raising ValueError on issues."""
    if not url_youtube.strip():
        raise YoutubeUrlParameterEmptyError()
    if not output_dir.strip():
        raise YoutubeOutputDirParameterEmptyError()
    if not (get_basic_data or get_srt):
        raise YoutubeNoDownloadOptionError()


# ============================================================================
# VIDEO INFO EXTRACTION
# ============================================================================


def _fetch_video_info(url_youtube: str) -> dict[str, Any]:
    """Fetch the raw video metadata via yt-dlp (no media download)."""
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "writesubtitles": False,
        "writeautomaticsub": False,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:  # type: ignore[arg-type]
        raw = ydl.extract_info(url_youtube, download=False)
    return cast(dict[str, Any], raw)


def _now_timestamp() -> str:
    """Return the current local timestamp formatted for filenames."""
    return datetime.now().strftime(TIMESTAMP_FMT)


# ============================================================================
# BASIC METADATA
# ============================================================================


def _save_basic_data(info: dict[str, Any], out_dir: Path, video_id: str, result: DownloadResult) -> None:
    """Serialize the basic metadata payload to a timestamped JSON file."""
    payload = _build_basic_payload(info)
    filename = BASIC_DATA_FILENAME_FMT.format(vid=video_id, ts=_now_timestamp())
    target = out_dir / filename
    try:
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    except OSError as exc:
        result.fail(f"Écriture des données basiques échouée : {exc}")
        return
    result.files_written.append(target)
    _logger.info("Données basiques enregistrées dans %s.", target)


def _build_basic_payload(info: dict[str, Any]) -> dict[str, Any]:
    """Extract the configured basic fields; fill missing values with None."""
    payload: dict[str, Any] = {field: info.get(field) for field in BASIC_DATA_FIELDS}
    payload["subtitles_available"] = _list_available_subtitles(info)
    return payload


def _list_available_subtitles(info: dict[str, Any]) -> dict[str, list[str]]:
    """List available FR/EN subtitles, grouped by origin (manual vs automatic)."""
    return {
        "manual": _collect_fra_eng_labels(info.get("subtitles")),
        "automatic": _collect_fra_eng_labels(info.get("automatic_captions")),
    }


def _collect_fra_eng_labels(block: object) -> list[str]:
    """Return 'CODE (display name)' labels for FR/EN tracks of a subs block."""
    if not isinstance(block, dict):
        return []
    labels: list[str] = []
    block_typed: dict[str, Any] = cast(dict[str, Any], block)
    for code, tracks in block_typed.items():
        if not isinstance(tracks, list):
            continue
        name = _track_display_name(tracks)
        # code: en-orig, name: English (Original)
        if not _name_matches_targets_fra_or_eng(code, name):
            continue
        short = _short_lang_code(code, name)
        display: str = name if name else code
        labels.append(f"code:='{short}', name:='{display}'")
    return labels


def _track_display_name(tracks: list[Any]) -> str:
    """Return the 'name' field from the first track entry, or an empty string."""
    for track in tracks:
        if isinstance(track, dict):
            typed: dict[str, Any] = cast(dict[str, Any], track)
            if typed.get("name"):
                return str(typed["name"])
    return ""


def _short_lang_code(code: str, name: str) -> str:
    """Map a track to a 2-letter uppercase short code (FRA/ENG/...)."""
    lowered = name.lower()
    if lowered.startswith(TARGET_LANG_PATTERNS):
        return code
    return DEFAULT_SHORT_CODE


# ============================================================================
# SUBTITLES — TWO-PHASE DOWNLOAD
# ============================================================================


def _download_subtitles(
    url_youtube: str,
    info: dict[str, Any],
    out_dir: Path,
    video_id: str,
    result: DownloadResult,
    event_bus: IScrapingEventBus,
    ctx: ScrapingContextModel,
) -> None:
    """Run the two-phase subtitle workflow (manual then automatic)."""
    manual_block: dict[str, Any] = info.get("subtitles") or {}
    auto_block: dict[str, Any] = info.get("automatic_captions") or {}
    manual_codes = _select_lang_codes(manual_block)
    auto_codes = _select_lang_codes(auto_block)

    _logger.info("Phase manuelle - codes sélectionnés : %s", manual_codes or "aucun")
    if manual_codes:
        event_bus.log_step(ctx, f"Sous-titres manuels : {', '.join(manual_codes)}")
        time.sleep(PHASE_PAUSE_SECONDS)
        for code in manual_codes:
            _run_subtitle_phase(url_youtube, out_dir, [code], result, automatic=False)

    _logger.info("Phase automatique - codes sélectionnés : %s", auto_codes or "aucun")
    if auto_codes:
        event_bus.log_step(ctx, f"Sous-titres automatiques : {', '.join(auto_codes)}")
        time.sleep(PHASE_PAUSE_SECONDS)
        for code in auto_codes:
            _run_subtitle_phase(url_youtube, out_dir, [code], result, automatic=True)
    _rename_subtitle_files(out_dir, video_id, manual_block, auto_block, manual_codes, auto_codes, result)


def _select_lang_codes(subs_block: dict[str, Any]) -> list[str]:
    """Return language codes whose display name matches the selection rules."""
    selected: list[str] = []
    for code, tracks in subs_block.items():
        if not isinstance(tracks, list):
            continue
        name = _track_display_name(tracks)
        if _name_matches_targets_fra_or_eng(code, name):
            selected.append(code)
    return selected


def _name_matches_targets_fra_or_eng(code: str, name: str) -> bool:
    # Example :
    # code: crs, name: Seselwa Creole French
    # code: pt-PT, name: Portuguese (Portugal)
    # code: en-orig, name: English (Original)
    # code: en, name: English
    # code: fr, name: French (Original)
    """Return True if the track name contains a target language pattern."""
    cd_lowered = code.strip().lower()
    if cd_lowered.startswith(TARGET_LANG_CODES):
        return True
    name_lowered = name.strip().lower()
    return name_lowered.startswith(TARGET_LANG_PATTERNS)


# ============================================================================
# SUBTITLE DOWNLOAD WITH HTTP-429 RETRY
# ============================================================================


def _run_subtitle_phase(url: str, out_dir: Path, codes: list[str], result: DownloadResult, *, automatic: bool) -> None:
    """Run a single subtitle phase with fixed-delay retries on HTTP 429."""
    last_error: Exception | None = None
    for _, delay in enumerate(RATE_LIMIT_RETRY_DELAYS):  # idx, delay
        if delay > 0:
            time.sleep(delay)

        # ddl subtitle download; on failure, if it's a rate-limit issue, retry after the delay;
        try:
            _execute_yt_dlp_subs(url, out_dir, codes, automatic=automatic)
        except DownloadError as exc:
            last_error = exc
            if not _is_rate_limit_error(exc):
                result.fail(f"Erreur yt-dlp (non rate-limit) : {exc}")
                return
            result.warn("Limite de débit détectée (HTTP 429).")
        else:
            return
    result.fail(f"Échec définitif après réessais : {last_error}")


def _execute_yt_dlp_subs(url: str, out_dir: Path, codes: list[str], *, automatic: bool) -> None:
    """Invoke yt-dlp to download a specific set of subtitle tracks."""
    template = str(out_dir / "%(id)s.%(ext)s")
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "writesubtitles": not automatic,
        "writeautomaticsub": automatic,
        "subtitleslangs": list(codes),
        "subtitlesformat": SUBTITLE_FORMATS,
        "outtmpl": template,
        "overwrites": False,  # yt-dlp skips already-downloaded files on retry.
    }
    with yt_dlp.YoutubeDL(opts) as ydl:  # type: ignore[arg-type]
        ydl.download([url])


def _is_rate_limit_error(exc: BaseException) -> bool:
    """Return True if the exception message looks like an HTTP 429 issue."""
    message = str(exc).lower()
    return any(pattern in message for pattern in HTTP_429_PATTERNS)


# ============================================================================
# RENAMING + N/A PLACEHOLDERS
# ============================================================================


def _rename_subtitle_files(
    out_dir: Path,
    video_id: str,
    manual_block: dict[str, Any],
    auto_block: dict[str, Any],
    manual_codes: list[str],
    auto_codes: list[str],
    result: DownloadResult,
) -> None:
    """Rename downloaded subtitle files; emit N/A placeholders on failure."""
    _process_phase_rename(out_dir, video_id, manual_block, manual_codes, ORIGIN_MANUAL, result)
    _process_phase_rename(out_dir, video_id, auto_block, auto_codes, ORIGIN_AUTO, result)


def _process_phase_rename(
    out_dir: Path, video_id: str, block: dict[str, Any], codes: list[str], origin: str, result: DownloadResult
) -> None:
    """For each requested code, rename downloaded files or emit a placeholder."""
    for code in codes:
        tracks: list[Any] = block.get(code) or []
        name = _track_display_name(tracks)
        short = _short_lang_code(code, name).lower()
        renamed_any = False
        for ext in SUBTITLE_EXTENSIONS_KEEP:
            src = out_dir / f"{video_id}.{code}.{ext}"
            if src.exists():
                _rename_one(src, out_dir, video_id, short, origin, ext, result)
                renamed_any = True
        if not renamed_any:
            _emit_na_placeholder(out_dir, video_id, short, origin, result)


def _rename_one(
    src: Path, out_dir: Path, video_id: str, short: str, origin: str, ext: str, result: DownloadResult
) -> None:
    """Rename a single subtitle file to the canonical naming scheme."""
    filename = SUBTITLE_FILENAME_FMT.format(vid=video_id, origin=origin, lang=short, ts=_now_timestamp(), ext=ext)
    target = out_dir / clean_filename_youtube(filename)
    try:
        src.rename(target)
        result.nbr_srt_success += 1
    except OSError as exc:
        result.fail(f"Renommage de {src.name} échoué : {exc}")
        return
    result.files_downloaded.append(target)
    result.files_written.append(target)
    _logger.info("Fichier renommé : %s -> %s", src.name, target.name)


def _emit_na_placeholder(out_dir: Path, video_id: str, short: str, origin: str, result: DownloadResult) -> None:
    """Create a placeholder file whose content is the N/A token."""
    filename = NA_FILENAME_FMT.format(
        vid=video_id, origin=origin, lang=short, ts=_now_timestamp(), ext=NA_PLACEHOLDER_EXT
    )
    target = out_dir / clean_filename_youtube(filename)
    try:
        target.write_text(NA_TOKEN, encoding="utf-8")
    except OSError as exc:
        result.fail(f"Création du placeholder échouée : {exc}")
        return
    result.files_written.append(target)
    result.warn(f"Aucun sous-titre pour {short}/{origin}, placeholder : {target.name}")


# EOF
