"""IStepExecutor for YOUTUBE_DDL."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from typing import override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.youtube_infos_video_model import YoutubeInfosVideoModel
from repositories.youtube_repository import YoutubeRepository
from shared.enums import ProcessResultEnum, StepTypeEnum
from shared.errors.youtube_yt_dlp_error import ErrorCodeYYD
from shared.step_registry import register_step_executor
from shared.youtube_util import sanitize_youtube_url

_logger = logging.getLogger(__name__)


class YoutubeInfosVideoExecutor(IStepExecutor):
    """Executor for the YouTube infos video step — logs the title and always returns success."""

    def __init__(self, repo: YoutubeRepository) -> None:
        """Initialise the executor with an injected YouTube repository.

        Args:
            repo: Repository that owns all yt-dlp and filesystem I/O.
        """
        self._repo = repo
        self._logger = logging.getLogger(__name__)

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_YOUTUBE_EXTRACT_INFOS

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> ProcessResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        result = ProcessResultEnum.E_UNSET

        # TEST cast(YoutubeInfosVideoParams, context.step_scraping_data.params)
        try:
            url_youtube = sanitize_youtube_url(context.last_url_opened)
            obj = self._repo.fetch_video_info(url_youtube)
            casted = YoutubeInfosVideoModel(obj)
            rs = casted.validate()

            if not rs.has_errors_or_fatals():
                context.push_ytdlp_extracted(casted)
                self._repo.update_cached_subtitles(url_youtube, casted.subtitles_ls)
                result = ProcessResultEnum.E_SUCCESS

            if rs.has_issues():
                result = rs.get_worst_result_enum()
                event_bus.log_step(context, rs.concat_issues_by_order(10))

        except Exception as exc:
            self._logger.exception("An error occurred while fetching YouTube video info.")
            excp_msg_lower = str(exc).lower()
            err_code = self.simplify_error_message(excp_msg_lower)
            if err_code is not None:
                event_bus.log_step(context, f"Excp : {err_code} - {err_code.value}")
            else:
                event_bus.log_step(context, f"Excp : {exc}")
            result = ProcessResultEnum.E_ERROR

        return result

    @staticmethod
    def simplify_error_message(message: str) -> ErrorCodeYYD | None:
        """Simplify the error message for logging."""
        # This video is available to this channel's members
        if "video is available to this channel's members" in message:
            return ErrorCodeYYD.YYD_1003

        # Sign in to confirm your age. This video may be inappropriate for some users.
        if "may be inappropriate for" in message:
            return ErrorCodeYYD.YYD_1002
        if "in to confirm your age" in message:
            return ErrorCodeYYD.YYD_1002

        # Video unavailable. This video is not available
        if "video is not available" in message:
            return ErrorCodeYYD.YYD_1001
        if "video unavailable" in message:
            return ErrorCodeYYD.YYD_1001
        return None


register_step_executor(YoutubeInfosVideoExecutor(YoutubeRepository()))


# EOF
