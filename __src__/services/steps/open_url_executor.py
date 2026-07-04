"""IStepExecutor for OPEN_URL."""

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
from models.steps.open_url_params import OpenUrlParams
from shared.enums import StepExecutionResultEnum, StepTypeEnum
from shared.exception_util import UrlSourceExhaustedError
from shared.step_registry import register_step_executor
from shared.time_util import convert_to_ms

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_DNS_SOLVER_WAIT_MAX = 30  # Maximum accepted value; values > this are rejected by validation.

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------

_logger = logging.getLogger(__name__)


class OpenUrlExecutor(IStepExecutor):
    """Executor for the open URL scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_OPEN_URL

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> StepExecutionResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(OpenUrlParams, context.step_scraping_data.params)
        try:
            target_url = self._extract_next_url_used(context, p, event_bus)
            # obligé de le mettre avant de goto
            # car sinon les filtres apres ne peuvent pas savoir quelle est la dernière URL ouverte
            if target_url is None:
                event_bus.log_step(context, "Aucune URL à ouvrir.")
                return StepExecutionResultEnum.E_ERROR
            context.last_url_opened = target_url
            timeout_ms = convert_to_ms(p.timeout_duration, p.timeout_unit)
            browser.safe_goto_url(target_url, p.wait_until, timeout_ms, p.wait_dns_solver)
            event_bus.log_step(context, f"Ouvert : '{target_url}'")
        except Exception as exc:
            _logger.exception("An error occurred while opening the URL.")
            event_bus.log_step(context, f"Excp : {exc}")
            return StepExecutionResultEnum.E_ERROR
        else:
            return StepExecutionResultEnum.E_SUCCESS

    @staticmethod
    def _extract_next_url_used(
        context: ScrapingContextModel, p: OpenUrlParams, event_bus: IScrapingEventBus
    ) -> str | None:
        """Extract the next URL to open based on the step parameters and context.

        Args:
            context: The current scraping context, which may contain a URL source scenario.
            p: The parameters for the open URL step, including mode and custom URL.
            event_bus: The event bus for logging intermediate steps.

        Returns:
            The URL to open.

        Raises:
            UrlSourceExhaustedError: If the URL mode is source but there are no more URLs.
        """
        # Consume the next URL from the injected source
        if context.url_source is None or not context.url_source.is_ready_to_consum_urls():
            event_bus.log_step(context, "Aucune URL disponible dans la source.")
            raise UrlSourceExhaustedError()
        url_readed = context.url_source.read_current_url()
        context.url_source.load_next_url()
        event_bus.log_step(context, f"Progression : {context.url_source.get_progress_text()}")

        if url_readed:
            if p.url_cut_ampersand:
                url_readed = url_readed.split("&")[0]
            if p.url_cut_question:
                url_readed = url_readed.split("?")[0]
            if p.url_always_add_slash and not url_readed.endswith("/"):
                url_readed += "/"

        return url_readed


register_step_executor(OpenUrlExecutor())


# EOF
