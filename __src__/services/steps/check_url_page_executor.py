"""IStepExecutor for CHECK_URL_PAGE."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast, override
from urllib.parse import urlparse

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.check_url_page_params import CheckUrlPageParams
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import StepTypeEnum
from shared.step_registry import register_step_executor

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class CheckUrlPageExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the check URL page scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_CHECK_URL_PAGE

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(CheckUrlPageParams, context.step_scraping_data.params)

        page = browser.get_workflow_page()
        current_url = page.url
        expected_url = context.last_url_opened

        expected = urlparse(expected_url)
        current = urlparse(current_url)

        mismatches: list[str] = []  # list error messages

        # Check domain and path according to the parameters.
        # https://developer.mozilla.org/en-US/docs/Learn_web/ -> domain = 'developer.mozilla.org'
        if p.check_domain and expected.netloc != current.netloc:
            mismatches.append(f"Domaine attendu : {expected.netloc!r}, obtenu : {current.netloc!r}")

        # https://developer.mozilla.org/en-US/docs/Learn_web/ -> path = '/en-US/docs/Learn_web/'
        if p.check_path and expected.path != current.path:
            mismatches.append(f"Chemin attendu : {expected.path!r}, obtenu : {current.path!r}")

        if mismatches:
            raise ValueError("URL non conforme. " + " | ".join(mismatches))

        checks: list[str] = []
        if p.check_domain:
            checks.append("Domaine OK")
        if p.check_path:
            checks.append("Chemin OK")
        context.last_message_step = f"URL vérifiée : {', '.join(checks)}"


register_step_executor(CheckUrlPageExecutor())


# EOF
