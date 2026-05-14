"""IStepExecutor for OPEN_URL."""

from __future__ import annotations

from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.open_url_params import OpenUrlParams
from presenters.messages import ERROR_TEMPLATES
from services.workflow_service import register_step_executor
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.enums import StepTypeEnum
from shared.time_util import convert_to_ms


class OpenUrlExecutor(IStepExecutor):
    """Executor for the open URL scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_OPEN_URL

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return OpenUrlParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = OpenUrlParams.from_dict(context.step_params)
        page = browser.get_current_page()

        # Resolve the target URL from the source provider or the custom field.
        target_url = ""
        if p.url_mode == "<<CUSTOM>>":
            if not p.url_custom:
                raise ValueError("Le champ URL personnalisée est obligatoire lorsque le mode est <<CUSTOM>>.")
            target_url = p.url_custom
        else:
            # Consume the next URL from the injected source provider.
            if context.url_source is None or not context.url_source.has_next():
                raise ValueError("Aucune URL disponible dans la source configurée.")
            target_url = context.url_source.next_url()

        # obligé de le mettre avant de goto
        # car sinon les filtres apres ne peuvent pas savoir quelle est la dernière URL ouverte
        context.last_url_opened = target_url

        timeout_ms = convert_to_ms(p.timeout_duration, p.timeout_unit)
        if timeout_ms is not None:
            page.goto(target_url, wait_until=p.wait_state, timeout=timeout_ms)
        else:
            page.goto(target_url, wait_until=p.wait_state)

        context.last_message_step = f"Page ouverte : {target_url}"

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = OpenUrlParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)

        errors: list[str] = []
        if p.url_mode is None or (p.url_mode == "<<CUSTOM>>" and not p.url_custom):
            errors.append(ERROR_TEMPLATES["open_url_url_required"].format(step=index_display))
        if p.timeout_duration <= 0:
            errors.append(ERROR_TEMPLATES["open_url_timeout_invalid"].format(step=index_display))
        if p.timeout_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(ERROR_TEMPLATES["open_url_timeout_unit_invalid"].format(step=index_display))
        return errors


register_step_executor(OpenUrlExecutor())
