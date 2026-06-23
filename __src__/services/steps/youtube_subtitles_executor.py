"""IStepExecutor for YOUTUBE_SUBTITLES."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import time
from pathlib import Path
from typing import Final, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.Youtube_subtitles_list_model import YoutubeSubtitleModel, YoutubeSubtitlesListModel
from repositories.youtube_repository import YoutubeRepository
from shared.enums import StepExecutionResultEnum, StepTypeEnum
from shared.exception_util import (
    YoutubeSubtitlesDownloadedError,
    YoutubeSubtitlesNotFoundInMetadataError,
    YoutubeSubtitlesValidationFailedError,
)
from shared.step_registry import register_step_executor
from shared.validation_result import ValidationResult
from shared.youtube_util import get_id_video_youtube, sanitize_youtube_url


def _require_subtitles_found(all_srt: YoutubeSubtitlesListModel | None) -> YoutubeSubtitlesListModel:
    """Raise if no subtitles were found in the video metadata.

    Args:
        all_srt: Subtitle list model or None when metadata contained no tracks.

    Returns:
        The subtitle list model when it is not None.

    Raises:
        YoutubeSubtitlesNotFoundInMetadataError: If all_srt is None.
    """
    if all_srt is None:
        raise YoutubeSubtitlesNotFoundInMetadataError()
    return all_srt


def _require_valid_subtitles(rs: ValidationResult) -> None:
    """Raise if the subtitle validation result contains errors or fatals.

    Args:
        rs: ValidationResult to inspect.

    Raises:
        YoutubeSubtitlesValidationFailedError: If validation has errors or fatals.
    """
    if rs.has_errors_or_fatals():
        raise YoutubeSubtitlesValidationFailedError(rs.compute_displayable_issues(2))


def _require_subtitles_downloaded(count: int) -> None:
    """Raise if no subtitles were actually downloaded.

    Args:
        count: Number of subtitle files successfully written to disk.

    Raises:
        YoutubeSubtitlesDownloadedError: If count is zero or negative.
    """
    if count <= 0:
        raise YoutubeSubtitlesDownloadedError()


# ============================================================================
# CONSTANTS (single source of truth — tune the behaviour from here)
# ============================================================================

# --- Rate-limit / phase pacing ---------------------------------------------
RATE_LIMIT_RETRY_DELAYS: Final[tuple[int, ...]] = (1, 3)  # old = (0, 3, 5, 7)
HTTP_429_PATTERNS: Final[tuple[str, ...]] = ("429", "too many requests", "rate-limit")


class YoutubeSubtitlesExecutor(IStepExecutor):
    """Executor for the YouTube subtitles step."""

    def __init__(self, repo: YoutubeRepository) -> None:
        """Initialise the executor with an injected YouTube repository.

        Args:
            repo: Repository that owns all yt-dlp and filesystem I/O.
        """
        self._repo = repo

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_YOUTUBE_SUBTITLES

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> StepExecutionResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        exp_folder = Path(str(context.folder_export) + "/srt")
        try:
            url_youtube = sanitize_youtube_url(context.last_url_opened)
            all_srt = _require_subtitles_found(self._repo.fetch_cached_subtitles(url_youtube))
            rs = all_srt.validate()
            _require_valid_subtitles(rs)

            nbr_ddl_srt = self.download_all_subtitles(url_youtube, all_srt, exp_folder, event_bus, context)
            _require_subtitles_downloaded(nbr_ddl_srt)
            event_bus.log_step(context, f"Nombre de sous-titres téléchargés : +{nbr_ddl_srt}")

        except Exception as exc:  # noqa: BLE001
            # "... in to confirm your age ..." -> video age restricted
            # "... video unavailable ..." -> video not found
            event_bus.log_step(context, f"Excp : {exc}")
            return StepExecutionResultEnum.E_ERROR
        else:
            return StepExecutionResultEnum.E_SUCCESS

    def download_all_subtitles(
        self,
        url_youtube: str,
        info: YoutubeSubtitlesListModel,
        out_dir: Path,
        event_bus: IScrapingEventBus,
        ctx: ScrapingContextModel,
    ) -> int:
        """Wrap ``_download_subtitles`` to capture any unexpected exception."""
        nbr_srt_ddl = 0
        try:
            all_subtitles = info.list_srt_better_to_worst()

            if all_subtitles:
                for st in all_subtitles:
                    msg_log = (
                        f"SRT -> Code: {st.code}, Name: {st.name}, Origine: {st.origin.value}, Qual.: {st.quality}"
                    )
                    if st.quality >= 1:
                        is_success = self.download_on_subtitle(url_youtube, out_dir, st, event_bus, ctx)
                        if is_success:
                            event_bus.log_step(ctx, "DONE: " + msg_log)
                            nbr_srt_ddl += 1
                        else:  # error...
                            event_bus.log_step(ctx, "ERROR: " + msg_log)
                    else:
                        event_bus.log_step(ctx, "SKIPPED (fait tout le temps HTTP 429): " + msg_log)
        except Exception:  # noqa: BLE001
            event_bus.log_step(ctx, "ERROR - Erreur inattendue...")
        return nbr_srt_ddl

    # ============================================================================
    # SUBTITLE DOWNLOAD WITH HTTP-429 RETRY
    # ============================================================================

    def download_on_subtitle(
        self,
        url_youtube: str,
        out_dir: Path,
        srt: YoutubeSubtitleModel,
        event_bus: IScrapingEventBus,
        ctx: ScrapingContextModel,
    ) -> bool:
        """Run a single subtitle phase with fixed-delay retries on HTTP 429."""
        id_video = get_id_video_youtube(url_youtube)

        for _, delay in enumerate(RATE_LIMIT_RETRY_DELAYS):  # idx, delay
            if delay > 0:
                event_bus.log_step(ctx, f"Attente de {delay} secondes avant tentative de téléchargement du sous-titre.")
                time.sleep(delay)

            try:
                self._repo.execute_subtitle_download(url_youtube, id_video, out_dir, srt)
            except Exception as exc:  # noqa: BLE001
                if not self._is_rate_limit_error(exc):
                    event_bus.log_step(ctx, f"Erreur yt-dlp (non rate-limit) : {exc}")
                    return False
                event_bus.log_step(ctx, "Limite de débit détectée (HTTP 429).")
            else:
                return True
        target = str(out_dir / f"{id_video} - Q{srt.quality} - {srt.origin.value} - {srt.language.value}.error")
        self._repo.write_placeholder_file_when_error(Path(target))
        return False

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        """Return True if the exception message looks like an HTTP 429 issue."""
        message = str(exc).lower()
        return any(pattern in message for pattern in HTTP_429_PATTERNS)


register_step_executor(YoutubeSubtitlesExecutor(YoutubeRepository()))


# EOF
