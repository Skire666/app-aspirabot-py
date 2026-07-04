"""IStepExecutor for EXTRACT_JS_CUSTOM."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.extract_js_custom_params import ExtractJsCustomParams
from shared.constants import C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT, C_MAXIMUM_RETRY_EVALUATE_SCRIPT
from shared.enums import StepExecutionResultEnum, StepTypeEnum
from shared.exception_util import ScriptExecutionFailedError
from shared.step_registry import register_step_executor


class ExtractJsCustomExecutor(IStepExecutor):
    """Executor for the custom JS extraction step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type handled by this executor.

        Returns:
            StepTypeEnum.E_EXTRACT_JS_CUSTOM — used by the registry to dispatch to this executor.
        """
        return StepTypeEnum.E_EXTRACT_JS_CUSTOM

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> StepExecutionResultEnum:
        """Evaluate the custom JS code and push the resulting primary key into the context.

        Args:
            browser: Live browser service providing the current Playwright page.
            context: Scraping context.
            event_bus: Event bus for intermediate log entries.
        """
        assert context.step_scraping_data is not None

        p = cast(ExtractJsCustomParams, context.step_scraping_data.params)
        try:
            is_success, raw_value = browser.evaluate_script_with_safe_retry(
                p.js_code, C_MAXIMUM_RETRY_EVALUATE_SCRIPT, C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT
            )
            if not is_success or raw_value is None:
                raise ScriptExecutionFailedError("extract_js_custom")
            if not isinstance(raw_value, dict):
                raise ScriptExecutionFailedError("extract_js_custom", f"Expected dict, got {type(raw_value)}")
            if not isinstance(raw_value, list):
                raise ScriptExecutionFailedError("extract_js_custom", f"Expected list, got {type(raw_value)}")

            self._apply_url_cutters(raw_value, p)
            # push
            context.push_js_custom_extracted(raw_value, p.primary_key)

            # debug log
            event_bus.log_step(context, f"Clé primaire '{p.primary_key}' | str[:25] ='{str(raw_value)[:25]}'")
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Excp : {exc}")
            return StepExecutionResultEnum.E_ERROR
        else:
            return StepExecutionResultEnum.E_SUCCESS

    @staticmethod
    def _apply_url_cutters(value: object, p: ExtractJsCustomParams) -> None:
        """Apply the URL cleanup options to the raw JS result.

        Args:
            value: Raw string result returned by the custom JS code.
            p: ExtractJsCustomParams instance containing the cleanup options.
        """
        pk = p.primary_key
        if isinstance(value, dict):
            if p.url_cut_ampersand:
                value[pk] = value[pk].split("&")[0]
            if p.url_cut_question:
                value[pk] = value[pk].split("?")[0]
            if p.url_always_add_slash and value and not value[pk].endswith("/"):
                value[pk] += "/"
        elif isinstance(value, list):
            for item in value:
                if not isinstance(item, dict):
                    raise ScriptExecutionFailedError("extract_js_custom", f"Expected list of dicts, got {type(item)}")
                if p.url_cut_ampersand:
                    item[pk] = item[pk].split("&")[0]
                if p.url_cut_question:
                    item[pk] = item[pk].split("?")[0]
                if p.url_always_add_slash and item and not item[pk].endswith("/"):
                    item[pk] += "/"
        else:
            raise ScriptExecutionFailedError("extract_js_custom", f"Expected dict or list, got {type(value)}")


register_step_executor(ExtractJsCustomExecutor())


# EOF
