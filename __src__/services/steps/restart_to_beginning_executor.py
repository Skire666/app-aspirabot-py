"""IStepExecutor for RESTART_TO_BEGINNING."""

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
from models.steps.restart_to_beginning_params import RestartToBeginningParams
from shared.enums import ProcessResultEnum, StepTypeEnum
from shared.step_registry import register_step_executor

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------

_logger = logging.getLogger(__name__)


class RestartToBeginningExecutor(IStepExecutor):
    """Executor for the restart to beginning scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_RESTART_TO_BEGINNING

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> ProcessResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(RestartToBeginningParams, context.step_scraping_data.params)
        assert context.url_source is not None, "RESTART_TO_BEGINNING requires a URL source to be configured"
        try:
            if p.jump_only_if_urls_remaining:
                has_next_url = context.url_source.has_next_url()
                if not has_next_url:
                    event_bus.log_step(context, "Aucune URL restante (etape SKIP)")
                    return ProcessResultEnum.E_SKIPPED
                event_bus.log_step(context, "URL restante (va reprendre au début)")
                return ProcessResultEnum.E_SUCCESS

            event_bus.log_step(context, "Recommence au début")
        except Exception as exc:
            _logger.exception("Exception in RESTART_TO_BEGINNING step: %s", exc)
            print(f"DEBUG: Exception in RESTART_TO_BEGINNING step: {exc}")
            event_bus.log_step(context, f"Excp : {exc}")
            return ProcessResultEnum.E_ERROR
        else:
            return ProcessResultEnum.E_SUCCESS


register_step_executor(RestartToBeginningExecutor())


# EOF
