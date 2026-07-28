"""IStepExecutor for EXTRACT_JS_CUSTOM."""

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
from models.steps.extract_js_custom_params import ExtractJsCustomParams
from shared.constants import C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT, C_JS_PRIMARY_KEY, C_MAXIMUM_RETRY_EVALUATE_SCRIPT
from shared.dict_util import count_items_with_value
from shared.enums import ProcessResultEnum, StepTypeEnum
from shared.exception_util import (
    InsufficientDataQualityError,
    InvalidJsExtractedValueTypeError,
    JsExtractedPrimaryKeyMissingError,
    ScriptExecutionFailedError,
)
from shared.parse_util import safe_int_from_str
from shared.step_registry import register_step_executor
from shared.url_util import transformer_url

_logger = logging.getLogger(__name__)


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
    ) -> ProcessResultEnum:
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

            if not raw_value:
                event_bus.log_step(context, "ERROR : Le code JS a retourné une ligne totalement vide")
                return ProcessResultEnum.E_ERROR

            self._normalized_all_data(raw_value, p, context)
            # push
            context.push_js_custom_extracted(raw_value, p.level_extractor)

            # debug log
            event_bus.log_step(context, f"JS Custom str[:35] ='{str(raw_value)[:35]}'")
        except Exception as exc:
            _logger.exception("An error occurred while extracting texts.")
            event_bus.log_step(context, f"Excp : {exc}")
            return ProcessResultEnum.E_ERROR
        else:
            return ProcessResultEnum.E_SUCCESS

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
            raise InvalidJsExtractedValueTypeError(type(raw_value).__name__)
        return cast("dict[str, object] | list[object]", raw_value)

    @staticmethod
    def _normalized_all_data(value: object, p: ExtractJsCustomParams, context: ScrapingContextModel) -> None:
        """Apply the URL cleanup options to the raw JS result.

        Args:
            value: Raw dict, or list of dicts, returned by the custom JS code.
            p: ExtractJsCustomParams instance containing the cleanup options.
            context: The scraping context.
        """
        if isinstance(value, dict):
            ExtractJsCustomExecutor._normalize_row(cast(dict[str, str], value), p, context)
        elif isinstance(value, list):
            for item in cast(list[object], value):
                if not isinstance(item, dict):
                    raise InvalidJsExtractedValueTypeError(type(item).__name__)
                ExtractJsCustomExecutor._normalize_row(cast(dict[str, str], item), p, context)
        else:
            raise InvalidJsExtractedValueTypeError(type(value).__name__)

    @staticmethod
    def _normalize_row(row: dict[str, str], p: ExtractJsCustomParams, context: ScrapingContextModel) -> None:
        """Apply the URL cleanup options to a single extracted row.

        Args:
            row: One extracted dict, keyed by field name.
            p: ExtractJsCustomParams instance containing the cleanup options.
            context: The scraping context.
        """
        if not row or not row[C_JS_PRIMARY_KEY]:
            raise JsExtractedPrimaryKeyMissingError(C_JS_PRIMARY_KEY)

        nbr_vals_expected = safe_int_from_str(p.quality_expected, 1)
        nbr_vals_found = count_items_with_value(row)
        if nbr_vals_found < nbr_vals_expected:
            raise InsufficientDataQualityError(nbr_vals_found, nbr_vals_expected)

        if context and context.transformer_url_regexp and context.transformer_url_base:
            row[C_JS_PRIMARY_KEY] = transformer_url(
                row[C_JS_PRIMARY_KEY],
                context.transformer_url_regexp,
                context.transformer_url_base,
                context.transformer_url_trailing_slash,
            )


register_step_executor(ExtractJsCustomExecutor())


# EOF
