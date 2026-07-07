"""Per-step presenter for OPEN_URL — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.open_url_params import OpenUrlParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL
from shared.enums import StepTypeEnum, WaitUntilEnum
from shared.step_registry import register_params_builder


def format_step_start(prefix: str, _step: StepScrapingModel, context: ScrapingContextModel) -> str:
    """Format E_STEP_START journal line for OPEN_URL."""
    next_url = context.url_source.read_current_url() if context.url_source else None
    return f"{prefix} | Prochaine : {next_url!s}"


def _build(data: dict[str, Any]) -> OpenUrlParams:
    """Build OpenUrlParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated OpenUrlParams instance.
    """
    return OpenUrlParams(
        wait_until=data.get("wait_until", WaitUntilEnum.E_IDLE.value),
        wait_dns_solver=int(data.get("wait_dns_solver", 6)),
        timeout_duration=int(data.get("timeout_duration", 1)),
        timeout_unit=data.get("timeout_unit", C_UNITS_TIME_DEFAULT_MODEL),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_OPEN_URL, _build)


# EOF
