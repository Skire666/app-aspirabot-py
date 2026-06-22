"""YouTube textual data downloader (basic metadata + subtitles) built on yt-dlp.

This module exposes ``download_youtube_data`` as the only public entry point.
It is designed to be resilient against HTTP 429 rate-limiting and partial failures:
each language is processed independently, a placeholder file is written when a
track cannot be retrieved, and the function never raises — all outcomes are
captured in the returned :class:`DownloadResult`. The caller is responsible for
inspecting that summary and reacting to recorded errors.

All file and network I/O is delegated to :class:`YoutubeRepository`.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from interfaces.i_scraping_event_bus import IScrapingEventBus
from models.scraping_context_model import ScrapingContextModel
from models.youtube_infos_video_model import YoutubeInfosVideoModel
from models.Youtube_subtitles_list_model import YoutubeSubtitleModel, YoutubeSubtitlesListModel
from repositories.youtube_repository import YoutubeRepository
from shared.datetime_util import get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff
from shared.exception_util import (
    RepositoryWriteError,
    YoutubeNoDownloadOptionError,
    YoutubeOutputDirParameterEmptyError,
    YoutubeUrlParameterEmptyError,
)
from shared.path_util import clean_filename_youtube
from shared.youtube_util import sanitize_youtube_url
from yt_dlp.utils import DownloadError

# ============================================================================
# CONSTANTS (single source of truth — tune the behaviour from here)
# ============================================================================

LOGGER_NAME: Final[str] = "youtube_txt_downloader"

# --- Language selection rules ----------------------------------------------
TARGET_LANG_PATTERNS: Final[tuple[str, ...]] = ("french", "english")
TARGET_LANG_CODES: Final[tuple[str, ...]] = ("fr", "en")
DEFAULT_SHORT_CODE: Final[str] = "UNDEF"

# --- Rate-limit / phase pacing ---------------------------------------------
RATE_LIMIT_RETRY_DELAYS: Final[tuple[int, ...]] = (1, 3)  # old = (0, 3, 5, 7)
PHASE_PAUSE_SECONDS: Final[int] = 1
HTTP_429_PATTERNS: Final[tuple[str, ...]] = ("429", "too many requests", "rate-limit")

# --- Subtitle formats ------------------------------------------------------
SUBTITLE_EXTENSIONS_KEEP: Final[tuple[str, ...]] = ("srt", "vtt", "json3")

# --- Filename patterns -----------------------------------------------------
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
    """Structured summary of a ``download_youtube_data`` execution.

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
    video_not_found: bool = False
    video_age_restricted: bool = False
    nbr_base_success: int = 0
    nbr_srt_success: int = 0

    @property
    def success(self) -> bool:
        """Return True when no error was recorded."""
        return not self.errors

    def warn(self, message: str) -> None:
        """Record a warning and log it."""
        self.warnings.append(message)
        _logger.info(message)

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
    repo: YoutubeRepository,
) -> DownloadResult:
    """Orchestrate the full pipeline; record outcomes into ``result``.

    Args:
        url_youtube: Raw YouTube URL (will be cleaned and normalised).
        output_dir: Path to the output directory (created if absent).
        get_basic_data: Whether to download and save video metadata.
        get_srt: Whether to download subtitle tracks.
        event_bus: Bus used to emit progress messages to the UI.
        ctx: Scraping context carrying step and folder information.
        repo: Repository that owns all file and network I/O.

    Returns:
        A :class:`DownloadResult` summarising every file written, warning, and
        error encountered.  The function never raises — all outcomes are captured
        in the result.
    """
    result: DownloadResult = DownloadResult()

    url_youtube = sanitize_youtube_url(url_youtube)
    _logger.debug("Début du téléchargement YouTube : url='%s'", url_youtube)
    if not _safe_validate(url_youtube, output_dir, get_basic_data, get_srt, result):
        event_bus.log_step(ctx, f"Paramètres invalides : {result.errors[-1]}")
        return result
    _logger.debug("Validation des paramètres réussie.")
    out_path = _safe_prepare_dir(output_dir, result, repo)
    if out_path is None:
        return result

    _logger.debug("Préparation du répertoire de sortie.")
    # basic info extraction (also serves as a validation step before attempting subs download)
    all_infos: YoutubeInfosVideoModel | None = _safe_fetch_info(url_youtube, result, repo)
    if all_infos is None:
        return result
    video_id = str(all_infos.id or "unknown")

    _logger.debug("Extraction des informations vidéo : %s", video_id)
    # choices
    if get_basic_data:
        _logger.debug("Enregistrement des données basiques : %s", video_id)
        _safe_save_basic_data(all_infos, out_path, video_id, result, event_bus, ctx, repo)
    if get_srt:
        _logger.debug("Téléchargement des sous-titres : %s", video_id)
        _safe_download_subtitles(url_youtube, all_infos.subtitles_ls, out_path, video_id, result, event_bus, ctx, repo)

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


def _safe_prepare_dir(output_dir: str, result: DownloadResult, repo: YoutubeRepository) -> Path | None:
    """Create the output directory via the repository; on failure, record error and return None."""
    try:
        return repo.prepare_output_dir(output_dir)
    except RepositoryWriteError as exc:
        result.fail(f"Création du dossier '{output_dir}' impossible : {exc}")
        return None


def _safe_fetch_info(
    url_youtube: str, result: DownloadResult, repo: YoutubeRepository
) -> YoutubeInfosVideoModel | None:
    """Fetch video info via the repository; on failure, record error and return None."""
    try:
        obj = repo.fetch_video_info(url_youtube)
        return YoutubeInfosVideoModel(obj)
    except (DownloadError, RuntimeError) as exc:
        exc_str: str = str(exc).lower()
        if "in to confirm your age" in exc_str:
            result.video_age_restricted = True
        if "video unavailable" in exc_str:
            result.video_not_found = True
        result.fail(f"Extraction des informations vidéo échouée : {exc}")
        return None


def _safe_save_basic_data(
    info: YoutubeInfosVideoModel,
    out_dir: Path,
    video_id: str,
    result: DownloadResult,
    event_bus: IScrapingEventBus,
    ctx: ScrapingContextModel,
    repo: YoutubeRepository,
) -> None:
    """Wrap ``_save_basic_data`` to capture any unexpected exception."""
    try:
        _save_basic_data(info, out_dir, video_id, result, repo)
        event_bus.log_step(ctx, "Données basiques téléchargées.")
        result.nbr_base_success += 1
    except Exception as exc:  # noqa: BLE001
        result.fail(f"Données basiques (erreur inattendue) : {exc!r}")


def _safe_download_subtitles(
    url: str,
    info: YoutubeSubtitlesListModel,
    out_dir: Path,
    result: DownloadResult,
    event_bus: IScrapingEventBus,
    ctx: ScrapingContextModel,
    repo: YoutubeRepository,
) -> None:
    """Wrap ``_download_subtitles`` to capture any unexpected exception."""
    try:
        _download_subtitles(url, info, out_dir, result, event_bus, ctx, repo)
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
# BASIC METADATA
# ============================================================================


def _save_basic_data(
    info: YoutubeInfosVideoModel, out_dir: Path, video_id: str, result: DownloadResult, repo: YoutubeRepository
) -> None:
    """Build the target path and delegate JSON serialisation to the repository."""
    filename = BASIC_DATA_FILENAME_FMT.format(vid=video_id, ts=get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff())
    target = out_dir / filename
    try:
        repo.save_basic_data_json(info, target)
    except RepositoryWriteError as exc:
        result.fail(f"Écriture des données basiques échouée : {exc}")
        return
    result.files_written.append(target)
    _logger.info("Données basiques enregistrées dans %s.", target)


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
    info: YoutubeSubtitlesListModel,
    out_dir: Path,
    result: DownloadResult,
    event_bus: IScrapingEventBus,
    ctx: ScrapingContextModel,
    repo: YoutubeRepository,
) -> None:
    """Run the two-phase subtitle workflow (manual then automatic)."""
    manual_subtitles = info.list_manual_codes()
    auto_subtitles = info.list_auto_codes()

    _logger.info("Phase manuelle - codes sélectionnés : %s", manual_subtitles or "aucun")
    if manual_subtitles:
        event_bus.log_step(ctx, "Sous-titres manuels")
        time.sleep(PHASE_PAUSE_SECONDS)
        for srt in manual_subtitles:
            _run_subtitle_phase(url_youtube, out_dir, srt, result, repo=repo)

    _logger.info("Phase automatique - codes sélectionnés : %s", auto_subtitles or "aucun")
    if auto_subtitles:
        event_bus.log_step(ctx, "Sous-titres automatiques")
        time.sleep(PHASE_PAUSE_SECONDS)
        for srt in auto_subtitles:
            _run_subtitle_phase(url_youtube, out_dir, srt, result, repo=repo)
    # _rename_subtitle_files(out_dir, video_id, manual_subtitles, auto_subtitles, result, repo)


# ============================================================================
# SUBTITLE DOWNLOAD WITH HTTP-429 RETRY
# ============================================================================


def _run_subtitle_phase(
    url: str, out_dir: Path, srt: YoutubeSubtitleModel, result: DownloadResult, *, repo: YoutubeRepository
) -> None:
    """Run a single subtitle phase with fixed-delay retries on HTTP 429."""
    last_error: Exception | None = None
    for _, delay in enumerate(RATE_LIMIT_RETRY_DELAYS):  # idx, delay
        if delay > 0:
            time.sleep(delay)

        try:
            repo.execute_subtitle_download(url, out_dir, srt)
        except DownloadError as exc:
            last_error = exc
            if not _is_rate_limit_error(exc):
                result.fail(f"Erreur yt-dlp (non rate-limit) : {exc}")
                return
            result.warn("Limite de débit détectée (HTTP 429).")
        else:
            return
    result.fail(f"Échec définitif après réessais : {last_error}")


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
    manual_codes: list[str],
    auto_codes: list[str],
    result: DownloadResult,
    repo: YoutubeRepository,
) -> None:
    """Rename downloaded subtitle files; emit N/A placeholders on failure."""
    _process_phase_rename(out_dir, video_id, manual_codes, ORIGIN_MANUAL, result, repo)
    _process_phase_rename(out_dir, video_id, auto_codes, ORIGIN_AUTO, result, repo)


def _process_phase_rename(
    out_dir: Path, video_id: str, codes: list[str], origin: str, result: DownloadResult, repo: YoutubeRepository
) -> None:
    """For each requested code, rename downloaded files or emit a placeholder."""
    for code in codes:
        renamed_any = False
        for ext in SUBTITLE_EXTENSIONS_KEEP:
            src = out_dir / f"{video_id}.{code}.{ext}"
            if src.exists():
                _rename_one(src, out_dir, video_id, code, origin, ext, result, repo)
                renamed_any = True
        if not renamed_any:
            _emit_na_placeholder(out_dir, video_id, code, origin, result, repo)


def _rename_one(
    src: Path,
    out_dir: Path,
    video_id: str,
    short: str,
    origin: str,
    ext: str,
    result: DownloadResult,
    repo: YoutubeRepository,
) -> None:
    """Build the canonical filename and delegate the rename to the repository."""
    filename = SUBTITLE_FILENAME_FMT.format(
        vid=video_id, origin=origin, lang=short, ts=get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff(), ext=ext
    )
    target = out_dir / clean_filename_youtube(filename)
    try:
        repo.rename_subtitle_file(src, target)
        result.nbr_srt_success += 1
    except RepositoryWriteError as exc:
        result.fail(f"Renommage de {src.name} échoué : {exc}")
        return
    result.files_downloaded.append(target)
    result.files_written.append(target)


def _emit_na_placeholder(
    out_dir: Path, video_id: str, short: str, origin: str, result: DownloadResult, repo: YoutubeRepository
) -> None:
    """Build the placeholder path and delegate the write to the repository."""
    filename = NA_FILENAME_FMT.format(
        vid=video_id,
        origin=origin,
        lang=short,
        ts=get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff(),
        ext=NA_PLACEHOLDER_EXT,
    )
    target = out_dir / clean_filename_youtube(filename)
    try:
        repo.write_placeholder_file_when_error(target)
    except RepositoryWriteError as exc:
        result.fail(f"Création du placeholder échouée : {exc}")
        return
    result.files_written.append(target)
    result.warn(f"Aucun sous-titre pour {short}/{origin}, placeholder : {target.name}")


# EOF
