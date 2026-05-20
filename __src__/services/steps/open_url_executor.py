"""IStepExecutor for OPEN_URL."""

from __future__ import annotations

from typing import override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.open_url_params import OpenUrlParams
from services.workflow_service import register_step_executor
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.enums import OpenUrlModeEnum, StepTypeEnum
from shared.i18n_fra import ERROR_TEMPLATES
from shared.time_util import convert_to_ms


class OpenUrlExecutor(IStepExecutor):
    """Executor for the open URL scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_OPEN_URL

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = OpenUrlParams.from_dict(context.step_params)

        # Resolve the target URL from the source provider or the custom field.
        target_url = self._extract_next_url_used(context, p)

        # obligé de le mettre avant de goto
        # car sinon les filtres apres ne peuvent pas savoir quelle est la dernière URL ouverte
        context.last_url_opened = target_url
        timeout_ms = convert_to_ms(p.timeout_duration, p.timeout_unit)

        browser.safe_goto_url(target_url, p.wait_state, timeout_ms, p.wait_dns_solver)

        page = browser.get_current_page()
        if page.url != target_url:
            raise Exception(f"URL finale différente de la cible : {page.url} vs {target_url}")

        context.last_message_step = f"Ouvert : {target_url}"

    def _extract_next_url_used(self, context: ScrapingContextModel, p: OpenUrlParams) -> str:
        """Extract the next URL to open based on the step parameters and context.

        Args:
            context: The current scraping context, which may contain a URL source provider.
            p: The parameters for the open URL step, including mode and custom URL.

        Returns:
            The URL to open.

        Raises:
            ValueError: If the URL mode is custom but the custom URL is empty,
            or if the URL mode is source but there are no more URLs in the source provider.
        """
        if p.url_mode == OpenUrlModeEnum.E_CUSTOM.value:
            if not p.url_custom:
                raise ValueError("URL personnalisée vide")
            target_url = p.url_custom
        else:
            # Consume the next URL from the injected source provider.
            if context.url_source is None or not context.url_source.has_next():
                raise ValueError("Aucune URL dans la source")
            target_url = context.url_source.next_url()
        return target_url

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = OpenUrlParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)

        errors: list[str] = []
        if p.url_mode is None or (p.url_mode == OpenUrlModeEnum.E_CUSTOM.value and not p.url_custom):
            errors.append(ERROR_TEMPLATES["open_url_url_required"].format(step=index_display))
        if p.wait_dns_solver <= 0 or p.wait_dns_solver >= 31:
            errors.append(ERROR_TEMPLATES["open_url_wait_dns_solver_invalid"].format(step=index_display))
        if p.timeout_duration <= 0:
            errors.append(ERROR_TEMPLATES["open_url_timeout_invalid"].format(step=index_display))
        if p.timeout_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(ERROR_TEMPLATES["open_url_timeout_unit_invalid"].format(step=index_display))
        return errors


register_step_executor(OpenUrlExecutor())
