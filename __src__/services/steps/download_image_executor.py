"""IStepExecutor for DOWNLOAD_IMAGE."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, override
from urllib.parse import urljoin

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.download_image_params import DownloadImageParams
from services.workflow_service import register_step_executor
from shared.constants import (
    C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT,
    C_MAXIMUM_RETRY_EVALUATE_SCRIPT,
)
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
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.DOWNLOAD_IMAGE

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return DownloadImageParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, params: dict[str, Any]) -> None:
        """Execute the step."""
        p = DownloadImageParams.from_dict(params)
        page = browser.get_current_page()
        downloaded_urls: set[str] = params.get("_downloaded_urls", set())

        images = _get_filtered_images(browser, p)
        targets = _select_images_by_mode(images, p.mode)
        folder: Path = params.get("_folder", Path())
        make_all_folders_if_not_exists(folder, is_file_path=False)
        downloaded_count = 0

        for image in targets:
            img_src = str(image.get("src", ""))
            full_url = urljoin(page.url, img_src)
            if p.unique_only and full_url in downloaded_urls:
                continue

            # Download via the page context request to preserve session cookies.
            response = page.context.request.get(
                full_url,
                headers={"Referer": page.url, "User-Agent": page.evaluate("() => navigator.userAgent")},
            )
            if not response.ok:
                raise ImageDownloadFailedError(response.status)

            url_path = full_url.split("?")[0]
            suffix = Path(url_path).suffix or ".jpg"
            filename = (
                Path(url_path).stem + datetime.now().strftime("_%Y%m%d_%H%M%S%f") + f"_{downloaded_count + 1}" + suffix
            )
            dest = folder / filename
            with dest.open("wb") as fh:
                fh.write(response.body())
            downloaded_urls.add(full_url)
            downloaded_count += 1

        if downloaded_count == 0:
            raise ImageNotDownloadedError(len(targets))

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        index_display = str(step_index + 1).zfill(2)
        errors: list[str] = []
        for key in ("height_min", "height_max", "width_min", "width_max"):
            try:
                result = int(model.params.get(key, -1))
                if result < 0:
                    errors.append(f"Erreur dans l'étape {index_display}. : {key} doit être un entier positif.")
            except (ValueError, TypeError):
                errors.append(f"Erreur dans l'étape {index_display}. : {key} doit être un nombre.")
        return errors


register_step_executor(DownloadImageExecutor())
