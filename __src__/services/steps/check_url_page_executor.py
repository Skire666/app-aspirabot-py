"""IStepExecutor for CHECK_URL_PAGE."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast, override
from urllib.parse import urlparse

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.check_url_page_params import CheckUrlPageParams
from shared.enums import StepExecutionResultEnum, StepTypeEnum
from shared.exception_util import UrlPageCheckMismatchError
from shared.step_registry import register_step_executor

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class CheckUrlPageExecutor(IStepExecutor):
    """Executor for the check URL page scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_CHECK_URL_PAGE

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> StepExecutionResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(CheckUrlPageParams, context.step_scraping_data.params)
        try:
            page = browser.get_workflow_page()
            expected = urlparse(context.last_url_opened)
            current = urlparse(page.url)
            mismatches: list[str] = []

            # https://developer.mozilla.org/en-US/docs/Learn_web/ -> domain = 'developer.mozilla.org'
            if p.check_domain and expected.netloc != current.netloc:
                mismatches.append(f"Domaine attendu : {expected.netloc!r}, obtenu : {current.netloc!r}")

            # # https://developer.mozilla.org/en-US/docs/Learn_web/ -> path = '/en-US/docs/Learn_web/'
            if p.check_path and expected.path != current.path:
                mismatches.append(f"Chemin attendu : {expected.path!r}, obtenu : {current.path!r}")

            # check errors
            if mismatches:
                raise UrlPageCheckMismatchError(" | ".join(mismatches))  # noqa: TRY301
            checks: list[str] = []
            if p.check_domain:
                checks.append("Domaine OK")
            if p.check_path:
                checks.append("Chemin OK")
            event_bus.log_step(context, f"URL vérifiée : {', '.join(checks)}")
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Excp : {exc}")
            return StepExecutionResultEnum.E_ERROR
        else:
            return StepExecutionResultEnum.E_SUCCESS


register_step_executor(CheckUrlPageExecutor())


# EOF
