"""IStepExecutor for CLICK_FOR_DOWNLOAD."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.click_for_download_params import ClickForDownloadParams
from playwright.sync_api import Error as PlaywrightError
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import StepTypeEnum
from shared.exception_util import DownloadNotDetectedError, ElementNotFoundForClickError
from shared.step_registry import register_step_executor

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# TODO: hardcoded timeout, should be configurable per step
C_LIMIT_TIMEOUT_CLICK_MS = 10000

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class ClickForDownloadExecutor(StepExecutorBase, IStepExecutor):
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
            context: Execution context; step params must be ClickForDownloadParams.
                Sets context.last_message_step on success.

        Raises:
            ElementNotFoundForClickError: If the selector matches no element on the page.
            DownloadNotDetectedError: If no download was triggered after all click attempts.
        """
        p = cast(ClickForDownloadParams, context.step_scraping_data.params)
        page = browser.get_workflow_page()
        if page.locator(p.selector).count() <= 0:
            raise ElementNotFoundForClickError(p.selector, p.click_mode)
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
        page = browser.get_workflow_page()
        elements = page.query_selector_all(selector)
        if not elements:
            raise ElementNotFoundForClickError(selector, mode_click)
        return ClickForDownloadExecutor._try_js_click(page, elements, index_clicked)


register_step_executor(ClickForDownloadExecutor())


# EOF
