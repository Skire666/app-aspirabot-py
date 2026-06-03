"""IStepExecutor for DOWNLOAD_IMAGE."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path
from typing import Any, cast, override
from urllib.parse import urljoin

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.download_image_params import DownloadImageParams
from services.steps._helpers import get_filtered_images
from services.steps.step_executor_base import StepExecutorBase
from shared.datetime_util import get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff
from shared.enums import StepTypeEnum
from shared.exception_util import ImageDownloadFailedError, ImageNotDownloadedError
from shared.path_util import make_all_folders_if_not_exists
from shared.step_registry import register_step_executor

_MAX_FILENAME_STEM_LENGTH = 100  # Truncate URL stem at this length to avoid filesystem limits.


def _select_images_by_mode(images: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    if not images or len(images) == 0:
        return []
    if mode == "first":
        return [images[0]]
    if mode == "last":
        return [images[-1]]
    if mode == "all":
        return list(images)
    return [max(images, key=lambda img: img["width"] * img["height"])]


class DownloadImageExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the download image scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_DOWNLOAD_IMAGE

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the download-image step for all targeted images."""
        assert context.step_scraping_data is not None
        p = cast(DownloadImageParams, context.step_scraping_data.params)
        page = browser.get_workflow_page()
        downloaded_urls = context.downloaded_urls

        images = get_filtered_images(browser, p.to_dict())
        targets = _select_images_by_mode(images, p.mode)
        make_all_folders_if_not_exists(context.folder_export, is_file_path=False)
        downloaded_count = 0

        for image in targets:
            full_url = urljoin(page.url, str(image.get("src", "")))
            if p.unique_only and full_url in downloaded_urls:
                continue
            self._save_image(page, full_url, context, downloaded_urls)
            downloaded_count += 1

        if downloaded_count == 0:
            raise ImageNotDownloadedError(len(targets))

    @staticmethod
    def _save_image(
        page: Any,  # noqa: ANN401
        full_url: str,
        context: ScrapingContextModel,
        downloaded_urls: set[str],
    ) -> None:
        """Download one image and persist it to the export folder.

        Args:
            page: The live Playwright page (provides request context).
            full_url: Resolved absolute URL of the image.
            context: Scraping context supplying the export folder.
            downloaded_urls: Mutable set updated after each successful download.
        """
        # Download via the page context request to preserve session cookies.
        response = page.context.request.get(
            full_url, headers={"Referer": page.url, "User-Agent": page.evaluate("() => navigator.userAgent")}
        )
        if not response.ok:
            raise ImageDownloadFailedError(response.status)

        # Build a safe, unique destination path.
        url_path = full_url.split("?")[0]
        suffix = Path(url_path).suffix or ".jpg"
        stem = Path(url_path).stem
        filename = stem if len(stem) < _MAX_FILENAME_STEM_LENGTH else stem[:_MAX_FILENAME_STEM_LENGTH]
        dest = context.folder_export / (filename + "_" + get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff() + suffix)
        with dest.open("wb") as fh:
            fh.write(response.body())
        downloaded_urls.add(full_url)


register_step_executor(DownloadImageExecutor())


# EOF
