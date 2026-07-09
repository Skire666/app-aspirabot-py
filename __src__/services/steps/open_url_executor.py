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
from shared.enums import ProcessResultEnum, SeverityEnum, StepTypeEnum
from shared.exception_util import UrlSourceExhaustedError
from shared.step_registry import register_step_executor
from shared.time_util import convert_to_ms
from shared.url_util import transformer_url

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
    ) -> ProcessResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        result = ProcessResultEnum.E_UNSET

        p = cast(OpenUrlParams, context.step_scraping_data.params)
        try:
            target_url = self._extract_next_url_used(context, p, event_bus)
            # obligé de le mettre avant de goto
            # car sinon les filtres apres ne peuvent pas savoir quelle est la dernière URL ouverte
            if target_url:
                context.last_url_opened = target_url
                event_bus.log_step(context, f"URL suite au transformer : '{target_url}'")
                result = self._open_url_and_report(browser, context, event_bus, p, target_url)
            else:
                event_bus.log_step(context, "Aucune URL à ouvrir.")
                result = ProcessResultEnum.E_ERROR
        except Exception as exc:
            _logger.exception("An error occurred while opening the URL.")
            event_bus.log_step(context, f"Excp : {exc}")
            result = ProcessResultEnum.E_ERROR

        return result

    @staticmethod
    def _open_url_and_report(
        browser: IWebBrowserService,
        context: ScrapingContextModel,
        event_bus: IScrapingEventBus,
        p: OpenUrlParams,
        target_url: str,
    ) -> ProcessResultEnum:
        """Navigate to the target URL and translate the navigation issues into a step result.

        Args:
            browser: Live browser service performing the navigation.
            context: The current scraping context.
            event_bus: Event bus for intermediate log entries.
            p: Open URL step parameters (timeout and wait options).
            target_url: The URL to open.

        Returns:
            E_SUCCESS when the page opened cleanly, otherwise the worst issue severity.
        """
        timeout_ms = convert_to_ms(p.timeout_duration, p.timeout_unit)
        rs = browser.safe_goto_url(target_url, p.wait_until, timeout_ms, p.wait_dns_solver)

        if not rs.has_issues():
            event_bus.log_step(context, f"Page ouverte : {browser.get_workflow_page().url}.")
            return ProcessResultEnum.E_SUCCESS

        result = rs.get_worst_result_enum()
        event_bus.log_step(context, f"Alerte durant l'ouverture de l'URL :\n{rs.concat_issues_by_order(10)}")
        if result == ProcessResultEnum.E_WARNING:
            nbr_warnings = rs.count_severities(SeverityEnum.E_WARNING)
            event_bus.log_step(context, f"Page courante (x{nbr_warnings} WARNING) : {browser.get_workflow_page().url}.")
        return result

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

        return OpenUrlExecutor._cut_row(url_readed, context)

    @staticmethod
    def _cut_row(full_url: str | None, context: ScrapingContextModel) -> str | None:
        """Apply the URL cleanup options to the URL consumed from the source.

        Args:
            full_url: URL read from the source, or None when unavailable.
            context: The scraping context holding the transformer options.
        """
        if full_url and context and context.transformer_url_regexp and context.transformer_url_base:
            full_url = transformer_url(
                full_url,
                context.transformer_url_regexp,
                context.transformer_url_base,
                context.transformer_url_trailing_slash,
            )
        return full_url


register_step_executor(OpenUrlExecutor())


# EOF
