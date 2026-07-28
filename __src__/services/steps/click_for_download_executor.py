"""IStepExecutor for CLICK_FOR_DOWNLOAD."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.click_for_download_params import ClickForDownloadParams
from playwright.sync_api import Download, ElementHandle, Page
from shared.enums import ProcessResultEnum, StepTypeEnum
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
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> ProcessResultEnum:
        """Click an element to trigger a file download, then save it to the export folder.

        Tries up to three click strategies (normal, forced, JS) depending on the configured
        click mode. Blocks until the download completes before saving.

        Args:
            browser: Browser service owning the current page.
            context: Execution context; step params must be ClickForDownloadParams.
            event_bus: Event bus for intermediate log entries.

        Raises:
            ElementNotFoundForClickError: If the selector matches no element on the page.
            DownloadNotDetectedError: If no download was triggered after all click attempts.
        """
        assert context.step_scraping_data is not None
        p = cast(ClickForDownloadParams, context.step_scraping_data.params)
        try:
            page = browser.get_workflow_page()
            if page.locator(p.selector).count() <= 0:
                raise ElementNotFoundForClickError(p.selector, p.click_mode)  # ruff: ignore[raise-within-try]
            download_ctx: Any = self._do_click_for_download(browser, p.click_mode, p.selector, p.index_clicked)
            dl: Download | None = download_ctx.value if download_ctx is not None else None
            if dl is None:
                raise DownloadNotDetectedError()  # ruff: ignore[raise-within-try]
            self._save_download(dl, context)
            event_bus.log_step(context, f"Clique OK avec sélecteur '{p.selector}' pour téléchargement")
        except Exception as exc:  # ruff: ignore[blind-except]
            event_bus.log_step(context, f"Excp : {exc}")
            return ProcessResultEnum.E_ERROR
        else:
            return ProcessResultEnum.E_SUCCESS

    @staticmethod
    def _save_download(download_value: Download, context: ScrapingContextModel) -> None:
        """Save the completed download to the export folder."""
        filename = download_value.suggested_filename
        download_value.path()  # Blocks until the download file is fully written to disk
        new_path = str(context.folder_export) + "/" + filename
        download_value.save_as(new_path)

    @staticmethod
    def _try_js_click(page: Page, elements: list[ElementHandle], index: int) -> Any:  # ruff: ignore[any-type]
        """Trigger a JS click and capture the resulting download context manager."""
        with page.expect_download(timeout=C_LIMIT_TIMEOUT_CLICK_MS) as download_info:
            elements[index].evaluate("element => element.click()")
        return download_info

    @staticmethod
    def _do_click_for_download(browser: IWebBrowserService, mode_click: str, selector: str, index_clicked: int) -> Any:  # ruff: ignore[any-type]
        """Locate the selector and attempt a JS click to trigger a download."""
        page = browser.get_workflow_page()
        elements = page.query_selector_all(selector)
        if not elements:
            raise ElementNotFoundForClickError(selector, mode_click)
        return ClickForDownloadExecutor._try_js_click(page, elements, index_clicked)


register_step_executor(ClickForDownloadExecutor())


# EOF
