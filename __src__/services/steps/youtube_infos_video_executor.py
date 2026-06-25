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
from models.steps.youtube_infos_video_params import YoutubeInfosVideoParams
from models.youtube_infos_video_model import YoutubeInfosVideoModel
from repositories.youtube_repository import YoutubeRepository
from shared.enums import StepExecutionResultEnum, StepTypeEnum
from shared.exception_util import YoutubeInfosVideoNotDownloadedError
from shared.step_registry import register_step_executor
from shared.validation_result import ValidationResult
from shared.youtube_util import sanitize_youtube_url

_logger = logging.getLogger(__name__)


def _require_valid_video_infos(rs: ValidationResult) -> None:
    """Raise if the validation result contains errors or fatals.

    Args:
        rs: ValidationResult to inspect.

    Raises:
        YoutubeInfosVideoNotDownloadedError: If validation has errors or fatals.
    """
    if rs.has_errors_or_fatals():
        raise YoutubeInfosVideoNotDownloadedError(rs.compute_displayable_issues(2))


class YoutubeInfosVideoExecutor(IStepExecutor):
    """Executor for the YouTube infos video step — logs the title and always returns success."""

    def __init__(self, repo: YoutubeRepository) -> None:
        """Initialise the executor with an injected YouTube repository.

        Args:
            repo: Repository that owns all yt-dlp and filesystem I/O.
        """
        self._repo = repo

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_YOUTUBE_EXTRACT_INFOS

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> StepExecutionResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(YoutubeInfosVideoParams, context.step_scraping_data.params)
        try:
            url_youtube = sanitize_youtube_url(context.last_url_opened)
            obj = self._repo.fetch_video_info(url_youtube)
            casted = YoutubeInfosVideoModel(obj)
            rs = casted.validate()
            _require_valid_video_infos(rs)
            self._repo.update_cached_subtitles(url_youtube, casted)
            for key, value in casted.to_dict().items():
                casted_list = [value] if not isinstance(value, list) else value  # pyright: ignore[reportUnknownVariableType]
                context.push_extracted_values(key, "yt-dlp", p.comment, casted_list)

        except Exception as exc:  # noqa: BLE001
            # "... in to confirm your age ..." -> video age restricted
            # "... video unavailable ..." -> video not found
            event_bus.log_step(context, f"Excp : {exc}")
            return StepExecutionResultEnum.E_ERROR
        else:
            return StepExecutionResultEnum.E_SUCCESS


register_step_executor(YoutubeInfosVideoExecutor(YoutubeRepository()))


# EOF
