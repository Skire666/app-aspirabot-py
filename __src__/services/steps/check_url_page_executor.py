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
from shared.enums import ProcessResultEnum, StepTypeEnum
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
    ) -> ProcessResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(CheckUrlPageParams, context.step_scraping_data.params)
        try:
            page = browser.get_workflow_page()
            mismatches = self._collect_mismatches(p, context.last_url_opened, page.url)

            # check errors
            if mismatches:
                raise UrlPageCheckMismatchError(" | ".join(mismatches))  # ruff: ignore[raise-within-try]
            checks = self._collect_passed_checks(p)
            event_bus.log_step(context, f"URL vérifiée : '{', '.join(checks)}'")
        except Exception as exc:  # ruff: ignore[blind-except]
            event_bus.log_step(context, f"Excp : {exc}")
            return ProcessResultEnum.E_ERROR
        else:
            return ProcessResultEnum.E_SUCCESS

    @staticmethod
    def _collect_mismatches(p: CheckUrlPageParams, expected_url: str, current_url: str) -> list[str]:
        """Run every enabled URL check and describe the failures.

        Args:
            p: Step params defining which checks are enabled.
            expected_url: URL last opened by the workflow.
            current_url: URL currently displayed by the browser page.

        Returns:
            One French description per failed check; empty when all checks pass.
        """
        expected = urlparse(expected_url)
        current = urlparse(current_url)
        mismatches: list[str] = []

        # https://developer.mozilla.org/en-US/docs/Learn_web/ -> domain = 'developer.mozilla.org'
        if p.check_domain and expected.netloc != current.netloc:
            mismatches.append(f"Domaine attendu : {expected.netloc!r}, obtenu : {current.netloc!r}")

        # # https://developer.mozilla.org/en-US/docs/Learn_web/ -> path = '/en-US/docs/Learn_web/'
        if p.check_path and expected.path != current.path:
            mismatches.append(f"Chemin attendu : {expected.path!r}, obtenu : {current.path!r}")

        if p.url_contains and p.url_contains not in current_url:
            mismatches.append(f"URL doit contenir : {p.url_contains!r}, obtenu : {current_url!r}")

        if p.url_end_with and not current_url.endswith(p.url_end_with):
            mismatches.append(f"URL doit terminer par : {p.url_end_with!r}, obtenu : {current_url!r}")
        return mismatches

    @staticmethod
    def _collect_passed_checks(p: CheckUrlPageParams) -> list[str]:
        """Return the French labels of the enabled checks, for the success log line."""
        checks: list[str] = []
        if p.check_domain:
            checks.append("Domaine = OK")
        if p.check_path:
            checks.append("Chemin = OK")
        if p.url_contains:
            checks.append("Contient = OK")
        if p.url_end_with:
            checks.append("Termine par = OK")
        return checks


register_step_executor(CheckUrlPageExecutor())


# EOF
