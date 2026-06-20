"""Per-step presenter for SCROLL_DOWN — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, cast

from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.scroll_down_params import ScrollDownParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def format_step_start(prefix: str, step: StepScrapingModel, _context: ScrapingContextModel) -> str:
    """Format E_STEP_START journal line for SCROLL_DOWN."""
    scroll_params = cast(ScrollDownParams, step.params)
    return f"{prefix} | Dist. : {scroll_params.pixels} | Boucle : {scroll_params.nbr_loops}"


def _build(data: dict[str, Any]) -> ScrollDownParams:
    """Build ScrollDownParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated ScrollDownParams instance.
    """
    return ScrollDownParams(
        pixels=int(data.get("pixels", 1000)),
        nbr_loops=int(data.get("nbr_loops", 1)),
        delay_pause=int(data.get("delay_pause", 1)),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_SCROLL_DOWN, _build)


# EOF
