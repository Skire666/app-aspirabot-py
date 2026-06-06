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
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import StepExecutionResultEnum, StepTypeEnum
from shared.exception_util import YoutubeBaseDataNotDownloadedError, YoutubeSrtNotDownloadedError
from shared.step_registry import register_step_executor
from shared.youtube_downloader import DownloadResult, download_youtube_data

_logger = logging.getLogger(__name__)


class YoutubeTranscriptsExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the YouTube transcripts step — logs the title and always returns success."""

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
        try:
            rs: DownloadResult = download_youtube_data(
                context.last_url_opened, str(context.folder_export), p.basic_info, p.ddl_srt
            )
            if p.basic_info and rs.nbr_base_success <= 0:
                raise YoutubeBaseDataNotDownloadedError()  # noqa: TRY301
            if p.ddl_srt and rs.nbr_srt_success <= 0:
                raise YoutubeSrtNotDownloadedError()  # noqa: TRY301
            msg = f"Téléchargés : Basic info +{rs.nbr_base_success} | Sous-titres +{rs.nbr_srt_success}"
            event_bus.log_step(context, msg)
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Erreur : {exc}")
            return StepExecutionResultEnum.ERROR
        else:
            return StepExecutionResultEnum.SUCCESS


register_step_executor(YoutubeTranscriptsExecutor())


# EOF
