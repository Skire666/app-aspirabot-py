"""IStepExecutor for YOUTUBE_TRANSCRIPTS."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from typing import cast, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.youtube_transcripts_params import YoutubeTranscriptsParams
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import StepTypeEnum
from shared.step_registry import register_step_executor
from shared.youtube_dlt_srt import download_youtube_srt

_logger = logging.getLogger(__name__)


class YoutubeTranscriptsExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the YouTube transcripts step — logs the title and always returns success."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_YOUTUBE_TRANSCRIPTS

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = cast(YoutubeTranscriptsParams, context.step_scraping_data.params)

        total_ddl = download_youtube_srt(context.last_url_opened, str(context.folder_export))
        context.last_message_step = f"Transcripts téléchargés : {total_ddl} fichier(s)"


register_step_executor(YoutubeTranscriptsExecutor())


# EOF
