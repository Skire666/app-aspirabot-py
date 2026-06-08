"""Per-step presenter for EXTRACT_LINKS — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.extract_links_params import ExtractLinksParams
from shared.enums import ExtractTargetEnum, StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> ExtractLinksParams:
    """Build ExtractLinksParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated ExtractLinksParams instance.
    """
    return ExtractLinksParams(
        selector=data.get("selector", ""),
        target=data.get("target", ExtractTargetEnum.E_ALL.value),
        mapping=data.get("mapping", "key_name"),
        cutted_ampersand=data.get("cutted_ampersand", True),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_EXTRACT_LINKS, _build)


# EOF
