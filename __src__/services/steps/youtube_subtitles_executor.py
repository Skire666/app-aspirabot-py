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
from shared.step_registry import register_step_executor
from shared.youtube_util import get_id_video_youtube, sanitize_youtube_url

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
            all_srt = self._repo.fetch_cached_subtitles(url_youtube)
            if all_srt is None:
                raise ValueError("Aucun sous-titre trouvé dans les métadonnées du flux vidéo.")
            nbr_ddl_srt = self.download_all_subtitles(url_youtube, all_srt, exp_folder, event_bus, context)
            if nbr_ddl_srt <= 0:
                raise ValueError("Aucun sous-titre téléchargé.")
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
                            event_bus.log_step(ctx, "OK: " + msg_log)
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
