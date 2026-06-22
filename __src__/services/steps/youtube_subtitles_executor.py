"""IStepExecutor for YOUTUBE_SUBTITLES."""

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
from models.steps.youtube_subtitles_params import YoutubeSubtitlesParams
from shared.enums import StepExecutionResultEnum, StepTypeEnum
from shared.step_registry import register_step_executor

_logger = logging.getLogger(__name__)


class YoutubeSubtitlesExecutor(IStepExecutor):
    """Executor for the YouTube subtitles step."""

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
        p = cast(YoutubeSubtitlesParams, context.step_scraping_data.params)
        exp_folder = str(context.folder_export) + "/srt"
        # "socket_timeout" -> 20
        # RATE_LIMIT_RETRY_DELAYS -> (1, 3)
        # PHASE_PAUSE_SECONDS -> 1

        return StepExecutionResultEnum.E_SUCCESS


register_step_executor(YoutubeSubtitlesExecutor())


# EOF
