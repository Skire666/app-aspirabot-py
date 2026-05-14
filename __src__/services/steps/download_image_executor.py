"""IStepExecutor for DOWNLOAD_IMAGE."""

from __future__ import annotations

from pathlib import Path
from typing import Any, override
from urllib.parse import urljoin

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.download_image_params import DownloadImageParams
from presenters.messages import ERROR_TEMPLATES
from services.workflow_service import register_step_executor
from shared.constants import (
    C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT,
    C_MAXIMUM_RETRY_EVALUATE_SCRIPT,
)
from shared.datetime_util import get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff
from shared.enums import StepTypeEnum
from shared.exception_util import (
    ImageDownloadFailedError,
    ImageNotDownloadedError,
)
from shared.path_util import make_all_folders_if_not_exists


def _get_filtered_images(browser: IWebBrowserService, bounds: dict[str, int]) -> list[dict[str, Any]]:
    script = """
        () => Array.from(document.querySelectorAll('img'))
            .filter(img => img.naturalWidth > 0)
            .map(img => ({src: img.src, width: img.naturalWidth, height: img.naturalHeight, complete: img.complete}))
    """
    all_imgs: list[dict[str, Any]] = browser.evaluate_script_with_safe_retry(
        script, C_MAXIMUM_RETRY_EVALUATE_SCRIPT, C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT
    )

    if all_imgs is None:
        return []
    # filter images that do not match the dimension criteria
    h_min, h_max = bounds["height_min"], bounds["height_max"]
    w_min, w_max = bounds["width_min"], bounds["width_max"]
    return [img for img in all_imgs if w_min <= img["width"] <= w_max and h_min <= img["height"] <= h_max]


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


class DownloadImageExecutor(IStepExecutor):
    """Executor for the download image scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_DOWNLOAD_IMAGE

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return DownloadImageParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p: DownloadImageParams = DownloadImageParams.from_dict(context.step_params)
        page = browser.get_current_page()
        downloaded_urls = context.downloaded_urls

        images = _get_filtered_images(browser, p.to_dict())
        targets = _select_images_by_mode(images, p.mode)
        make_all_folders_if_not_exists(context.folder_export, is_file_path=False)
        downloaded_count = 0

        for image in targets:
            img_src = str(image.get("src", ""))
            full_url = urljoin(page.url, img_src)

            # If unique_only is True, skip downloading if the URL has already been downloaded
            if p.unique_only and full_url in downloaded_urls:
                continue

            # Download via the page context request to preserve session cookies.
            response = page.context.request.get(
                full_url,
                headers={"Referer": page.url, "User-Agent": page.evaluate("() => navigator.userAgent")},
            )
            if not response.ok:
                raise ImageDownloadFailedError(response.status)

            url_path = full_url.split("?")[0]  # Remove query parameters for filename generation
            suffix = Path(url_path).suffix or ".jpg"
            filename = Path(url_path).stem if len(Path(url_path).stem) < 100 else Path(url_path).stem[:100]
            timestamp_ms = "_" + get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff()
            dest = context.folder_export / (filename + timestamp_ms + suffix)
            with dest.open("wb") as fh:
                fh.write(response.body())
            downloaded_urls.add(full_url)
            downloaded_count += 1

        if downloaded_count == 0:
            raise ImageNotDownloadedError(len(targets))

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model parameters.

        Args:
            model: The step model to validate.
            step_index: Zero-based position of the step in the workflow.

        Returns:
            A list of error strings; empty when the model is valid.
        """
        step_label = str(step_index + 1).zfill(2)
        bounds, errors = self._parse_bounds(model.params, step_label)
        errors.extend(self._validate_ranges(bounds, step_label))
        return errors

    @staticmethod
    def _parse_bounds(params: dict[str, Any], step_label: str) -> tuple[dict[str, int], list[str]]:
        """Parse dimension params as integers; return (bounds, errors).

        Args:
            params: Raw step parameter dict.
            step_label: Zero-padded step number for error messages.

        Returns:
            A tuple of (successfully parsed bounds dict, parse error list).
        """
        errors: list[str] = []
        bounds: dict[str, int] = {}

        # Attempt integer conversion for each dimension key.
        for key in ("height_min", "height_max", "width_min", "width_max"):
            try:
                bounds[key] = int(params.get(key, -1))
            except ValueError, TypeError:
                errors.append(ERROR_TEMPLATES["image_dim_not_int"].format(step=step_label, key=key))
        return bounds, errors

    @staticmethod
    def _validate_ranges(bounds: dict[str, int], step_label: str) -> list[str]:
        """Validate non-negativity, max >= 1, and min <= max constraints.

        Args:
            bounds: Successfully parsed dimension values.
            step_label: Zero-padded step number for error messages.

        Returns:
            A list of constraint violation error strings.
        """
        errors: list[str] = []

        # Check non-negativity for all bounds.
        for key in ("height_min", "height_max", "width_min", "width_max"):
            if bounds.get(key, 0) < 0:
                errors.append(ERROR_TEMPLATES["image_dim_negative"].format(step=step_label, key=key))

        # Check max bounds are at least 1.
        for key in ("height_max", "width_max"):
            if bounds.get(key, 1) < 1:
                errors.append(ERROR_TEMPLATES["image_dim_max_below_one"].format(step=step_label, key=key))

        # Check min <= max for each dimension.
        for min_k, max_k in (("height_min", "height_max"), ("width_min", "width_max")):
            if min_k in bounds and max_k in bounds and bounds[min_k] > bounds[max_k]:
                errors.append(
                    ERROR_TEMPLATES["image_dim_range_invalid"].format(
                        step=step_label, min_key=min_k, max_key=max_k
                    )
                )
        return errors


register_step_executor(DownloadImageExecutor())
