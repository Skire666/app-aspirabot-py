"""IStepExecutor for DOWNLOAD_IMAGE."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.download_image_params import DownloadImageParams
from services.steps._helpers import evaluate_script_with_safe_retry
from services.workflow_service import register_step_executor
from shared.path_util import make_all_folders_if_not_exists

_logger = logging.getLogger(__name__)


def _extract_bounds(p: DownloadImageParams) -> dict[str, int]:
    return {"h_min": p.height_min, "h_max": p.height_max, "w_min": p.width_min, "w_max": p.width_max}


def _get_filtered_images(page: Any, bounds: dict[str, int]) -> list[dict[str, Any]]:
    h_min, h_max = bounds["h_min"], bounds["h_max"]
    w_min, w_max = bounds["w_min"], bounds["w_max"]
    script = """
        () => Array.from(document.querySelectorAll('img'))
            .filter(img => img.naturalWidth > 0)
            .map(img => ({src: img.src, width: img.naturalWidth, height: img.naturalHeight}))
    """
    all_imgs: list[dict[str, Any]] = evaluate_script_with_safe_retry(page, script, 5)
    return [img for img in all_imgs if w_min <= img["width"] <= w_max and h_min <= img["height"] <= h_max]


def _select_by_mode(images: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    if mode == "first":
        return [images[0]]
    if mode == "last":
        return [images[-1]]
    if mode == "all":
        return list(images)
    return [max(images, key=lambda img: img["width"] * img["height"])]


class DownloadImageExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.DOWNLOAD_IMAGE

    def default_params_dict(self) -> dict[str, Any]:
        return DownloadImageParams.default().to_dict()

    def execute(self, page: Any, params: dict[str, Any]) -> None:
        p = DownloadImageParams.from_dict(params)
        folder: Path = params.get("_folder", Path())
        downloaded_urls: set[str] = params.get("_downloaded_urls", set())

        bounds = _extract_bounds(p)
        images = _get_filtered_images(page, bounds)
        if not images:
            raise ValueError("No image matching the size constraints found on the page.")

        targets = _select_by_mode(images, p.mode)
        make_all_folders_if_not_exists(folder, is_file_path=False)
        downloaded_count = 0

        for image in targets:
            img_src = str(image.get("src", ""))
            full_url = urljoin(page.url, img_src)
            print(f"Attempting to download image: {full_url}")
            if p.unique_only and full_url in downloaded_urls:
                continue
            response = page.context.request.get(
                full_url,
                headers={"Referer": page.url, "User-Agent": page.evaluate("() => navigator.userAgent")},
            )
            if not response.ok:
                raise ValueError(f"Failed to download image: HTTP {response.status}")
            url_path = full_url.split("?")[0]
            suffix = Path(url_path).suffix or ".jpg"
            filename = (
                Path(url_path).stem
                + datetime.now().strftime("_%Y%m%d_%H%M%S%f")
                + f"_{downloaded_count + 1}"
                + suffix
            )
            dest = folder / filename
            with dest.open("wb") as fh:
                fh.write(response.body())
            downloaded_urls.add(full_url)
            downloaded_count += 1

        if downloaded_count == 0:
            raise ValueError("No image was downloaded.")

    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        p = DownloadImageParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)
        errors: list[str] = []
        for key in ("height_min", "height_max", "width_min", "width_max"):
            try:
                int(model.params.get(key, 0))
            except (ValueError, TypeError):
                errors.append(f"Erreur dans l'étape {index_display}. : {key} doit être un entier.")
        return errors


register_step_executor(DownloadImageExecutor())
