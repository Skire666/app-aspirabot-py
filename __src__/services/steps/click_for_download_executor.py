"""IStepExecutor for CLICK_FOR_DOWNLOAD."""

from __future__ import annotations

from typing import override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.click_on_element_params import ClickOnElementParams
from playwright.sync_api import Error as PlaywrightError
from services.workflow_service import register_step_executor
from shared.enums import StepTypeEnum
from shared.exception_util import DownloadNotDetectedError, ElementNotFoundForClickError
from shared.i18n_fra import ERROR_TEMPLATES

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# TODO: hardcoded timeout, should be configurable per step
C_LIMIT_TIMEOUT_CLICK_MS = 10000

# ---------------------------------------------------------------------------
# Class
# ---------------------------------------------------------------------------


class ClickForDownloadExecutor(IStepExecutor):
    """Executor for the click for download scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Declare which workflow step type this executor handles.

        Returns:
            StepTypeEnum.E_CLICK_FOR_DOWNLOAD
        """
        return StepTypeEnum.E_CLICK_FOR_DOWNLOAD

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Click an element to trigger a file download, then save it to the export folder.

        Tries up to three click strategies (normal, forced, JS) depending on the configured
        click mode. Blocks until the download completes before saving.

        Args:
            browser: Browser service owning the current page.
            context: Execution context; step_params must be parseable as ClickOnElementParams.
                Sets context.last_message_step on success.

        Raises:
            ElementNotFoundForClickError: If the selector matches no element on the page.
            DownloadNotDetectedError: If no download was triggered after all click attempts.
        """
        p = ClickOnElementParams.from_dict(context.step_params)
        page = browser.get_current_page()
        if page.locator(p.selector).count() <= 0:
            raise ElementNotFoundForClickError(p.selector, p.mode)
        download = self._do_click_for_download(browser, p.click_mode, p.selector, p.index_clicked)
        if not (download and download.value):
            raise DownloadNotDetectedError()
        self._save_download(download.value, context)
        context.last_message_step = f"Clique OK avec sélecteur {p.selector!r} pour téléchargement"

    @staticmethod
    def _save_download(download_value: object, context: ScrapingContextModel) -> None:
        filename = download_value.suggested_filename
        download_value.path()  # Blocks until the download file is fully written to disk
        new_path = str(context.folder_export) + "/" + filename
        download_value.save_as(new_path)

    @staticmethod
    def _try_playwright_click(page: object, elements: list, index: int, **click_kwargs: object) -> object | None:
        try:
            with page.expect_download() as download_info:
                elements[index].click(timeout=C_LIMIT_TIMEOUT_CLICK_MS, **click_kwargs)
                return download_info
        except PlaywrightError:
            return None

    @staticmethod
    def _try_js_click(page: object, elements: list, index: int) -> object:
        with page.expect_download(timeout=C_LIMIT_TIMEOUT_CLICK_MS) as download_info:
            elements[index].evaluate("element => element.click()")
        return download_info

    @staticmethod
    def _do_click_for_download(
        browser: IWebBrowserService, mode_click: str, selector: str, index_clicked: int
    ) -> object:
        page = browser.get_current_page()
        elements = page.query_selector_all(selector)
        if not elements:
            raise ElementNotFoundForClickError(selector, mode_click)
        return ClickForDownloadExecutor._try_js_click(page, elements, index_clicked)

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Check that the step parameters are valid before execution.

        Args:
            model: The step model whose params will be parsed as ClickOnElementParams.
            step_index: Zero-based index of the step in the workflow, used to format error messages.

        Returns:
            An empty list if all parameters are valid, or a list of French error messages
            describing each violation.
        """
        p = ClickOnElementParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)
        if p.index_clicked <= -1:
            return [ERROR_TEMPLATES["click_element_index_invalid"].format(step=index_display)]
        if not p.selector.strip():
            return [ERROR_TEMPLATES["click_element_selector_required"].format(step=index_display)]
        return []


register_step_executor(ClickForDownloadExecutor())
