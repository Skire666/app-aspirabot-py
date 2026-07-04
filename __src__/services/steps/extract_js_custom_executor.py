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
            raw_value = self._evaluate_and_validate(browser, p)
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
    def _evaluate_and_validate(
        browser: IWebBrowserService, p: ExtractJsCustomParams
    ) -> dict[str, object] | list[object]:
        """Evaluate the custom JS code and validate that it produced a usable result.

        Args:
            browser: Live browser service providing the current Playwright page.
            p: ExtractJsCustomParams instance holding the JS code to run.

        Returns:
            The raw dict or list returned by the custom JS code.

        Raises:
            ScriptExecutionFailedError: If the script failed or returned an unusable value.
        """
        is_success, raw_value = browser.evaluate_script_with_safe_retry(
            p.js_code, C_MAXIMUM_RETRY_EVALUATE_SCRIPT, C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT
        )
        if not is_success or raw_value is None:
            raise ScriptExecutionFailedError("extract_js_custom")
        if not isinstance(raw_value, dict | list):
            raise ScriptExecutionFailedError("extract_js_custom")
        return cast("dict[str, object] | list[object]", raw_value)

    @staticmethod
    def _apply_url_cutters(value: object, p: ExtractJsCustomParams) -> None:
        """Apply the URL cleanup options to the raw JS result.

        Args:
            value: Raw dict, or list of dicts, returned by the custom JS code.
            p: ExtractJsCustomParams instance containing the cleanup options.
        """
        if isinstance(value, dict):
            ExtractJsCustomExecutor._cut_row(cast(dict[str, str], value), p)
        elif isinstance(value, list):
            for item in cast(list[object], value):
                if not isinstance(item, dict):
                    raise ScriptExecutionFailedError("extract_js_custom")
                ExtractJsCustomExecutor._cut_row(cast(dict[str, str], item), p)
        else:
            raise ScriptExecutionFailedError("extract_js_custom")

    @staticmethod
    def _cut_row(row: dict[str, str], p: ExtractJsCustomParams) -> None:
        """Apply the URL cleanup options to a single extracted row.

        Args:
            row: One extracted dict, keyed by field name.
            p: ExtractJsCustomParams instance containing the cleanup options.
        """
        pk = p.primary_key
        if p.url_cut_ampersand:
            row[pk] = row[pk].split("&")[0]
        if p.url_cut_question:
            row[pk] = row[pk].split("?")[0]
        if p.url_always_add_slash and row and not row[pk].endswith("/"):
            row[pk] += "/"


register_step_executor(ExtractJsCustomExecutor())


# EOF
