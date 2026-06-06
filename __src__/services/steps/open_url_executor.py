"""IStepExecutor for OPEN_URL."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.open_url_params import OpenUrlParams
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import OpenUrlModeEnum, StepExecutionResultEnum, StepTypeEnum
from shared.exception_util import EmptyCustomUrlError, UrlSourceExhaustedError
from shared.step_registry import register_step_executor
from shared.time_util import convert_to_ms

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_DNS_SOLVER_WAIT_MAX = 30  # Maximum accepted value; values > this are rejected by validation.

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class OpenUrlExecutor(StepExecutorBase, IStepExecutor):
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
            target_url = self._extract_next_url_used(context, p)
            # obligé de le mettre avant de goto
            # car sinon les filtres apres ne peuvent pas savoir quelle est la dernière URL ouverte
            context.last_url_opened = target_url
            timeout_ms = convert_to_ms(p.timeout_duration, p.timeout_unit)
            browser.safe_goto_url(target_url, p.wait_until, timeout_ms, p.wait_dns_solver)
            event_bus.log_step(context, f"Ouvert : {target_url}")
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Erreur : {exc}")
            return StepExecutionResultEnum.E_ERROR
        else:
            return StepExecutionResultEnum.E_SUCCESS

    @staticmethod
    def _extract_next_url_used(context: ScrapingContextModel, p: OpenUrlParams) -> str:
        """Extract the next URL to open based on the step parameters and context.

        Args:
            context: The current scraping context, which may contain a URL source scenario.
            p: The parameters for the open URL step, including mode and custom URL.

        Returns:
            The URL to open.

        Raises:
            EmptyCustomUrlError: If the URL mode is custom but the custom URL is empty.
            UrlSourceExhaustedError: If the URL mode is source but there are no more URLs.
        """
        if p.url_mode == OpenUrlModeEnum.E_CUSTOM.value:
            if not p.url_custom:
                raise EmptyCustomUrlError()
            target_url = p.url_custom
        else:
            # Consume the next URL from the injected source
            if context.url_source is None or not context.url_source.load_url_if_available():
                raise UrlSourceExhaustedError()
            target_url = context.url_source.pop_url()
        return target_url


register_step_executor(OpenUrlExecutor())


# EOF
