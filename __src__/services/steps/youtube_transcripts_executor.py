"""IStepExecutor for YOUTUBE_DDL."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from typing import cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.youtube_transcripts_params import YoutubeTranscriptsParams
from repositories.youtube_repository import YoutubeRepository
from services.steps.youtube_helpers import download_youtube_data
from shared.enums import StepExecutionResultEnum, StepTypeEnum
from shared.exception_util import YoutubeBaseDataNotDownloadedError, YoutubeSrtNotDownloadedError
from shared.step_registry import register_step_executor

_logger = logging.getLogger(__name__)


class YoutubeTranscriptsExecutor(IStepExecutor):
    """Executor for the YouTube transcripts step — logs the title and always returns success."""

    def __init__(self, repo: YoutubeRepository) -> None:
        """Initialise the executor with an injected YouTube repository.

        Args:
            repo: Repository that owns all yt-dlp and filesystem I/O.
        """
        self._repo = repo

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_YOUTUBE_DDL

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> StepExecutionResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(YoutubeTranscriptsParams, context.step_scraping_data.params)
        exp_folder = str(context.folder_export) + "/srt"
        try:
            # "socket_timeout" -> 20
            # RATE_LIMIT_RETRY_DELAYS -> (1, 3)
            # PHASE_PAUSE_SECONDS -> 1

            rs = download_youtube_data(
                context.last_url_opened, exp_folder, p.basic_info, p.ddl_srt, event_bus, context, self._repo
            )
            if rs.video_age_restricted:
                event_bus.log_step(context, "Vidéo marquée comme réservée aux adultes, extraction impossible.")
                raise YoutubeBaseDataNotDownloadedError("video_age_restricted")  # noqa: TRY301
            if rs.video_not_found:
                event_bus.log_step(context, "Vidéo introuvable, extraction impossible.")
                raise YoutubeBaseDataNotDownloadedError("video_not_found")  # noqa: TRY301
            if p.basic_info and rs.nbr_base_success <= 0:
                raise YoutubeBaseDataNotDownloadedError("no_ddl_basic_info")  # noqa: TRY301
            if p.ddl_srt and rs.nbr_srt_success <= 0:
                raise YoutubeSrtNotDownloadedError()  # noqa: TRY301
            msg = f"Téléchargés : Basic info +{rs.nbr_base_success} | Sous-titres +{rs.nbr_srt_success}"
            event_bus.log_step(context, msg)
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Excp : {exc}")
            return StepExecutionResultEnum.E_ERROR
        else:
            return StepExecutionResultEnum.E_SUCCESS


register_step_executor(YoutubeTranscriptsExecutor(YoutubeRepository()))


# EOF
