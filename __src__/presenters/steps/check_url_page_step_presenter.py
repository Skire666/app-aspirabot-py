"""Per-step presenter for CHECK_URL_PAGE — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.check_url_page_params import CheckUrlPageParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> CheckUrlPageParams:
    """Build CheckUrlPageParams from a raw JSON params dict."""
    return CheckUrlPageParams(
        check_domain=bool(data.get("check_domain", True)),
        check_path=bool(data.get("check_path")),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_CHECK_URL_PAGE, _build)


# EOF
