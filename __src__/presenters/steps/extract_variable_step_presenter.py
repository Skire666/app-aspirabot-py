"""Per-step presenter for EXTRACT_VARIABLE — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.extract_variable_params import ExtractVariableParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_ALLOWED_VARIABLES: list[str] = ["datetime_now", "last_url_full", "last_url_domain", "last_url_cutted"]

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------


def _build(data: dict[str, Any]) -> ExtractVariableParams:
    """Build ExtractVariableParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated ExtractVariableParams instance.
    """
    return ExtractVariableParams(
        variable=data.get("variable", C_ALLOWED_VARIABLES[-1]),
        mapping=data.get("mapping", ""),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_EXTRACT_VARIABLE, _build)


# EOF
