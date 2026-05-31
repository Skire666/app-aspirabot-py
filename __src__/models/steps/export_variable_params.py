"""Typed parameter model for the EXPORT_VARIABLE step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from models.steps.base_step_params import BaseStepParams, step_label
from pydantic import ValidationInfo, field_validator
from shared.i18n_fra import ERROR_TEMPLATES

_ALLOWED_VARIABLES: frozenset[str] = frozenset({"date_time_now", "last_url", "last_domain"})


class ExportVariableParams(BaseStepParams):
    """Parameters for the export variable step."""

    variable: str
    comment: str = ""

    @field_validator("variable")
    @classmethod
    def check_variable(cls, v: str, info: ValidationInfo) -> str:
        """Reject unrecognised variable identifiers."""
        if not info.context:
            return v
        if v not in _ALLOWED_VARIABLES:
            raise ValueError(ERROR_TEMPLATES["export_variable_invalid"].format(step=step_label(info.context), value=v))
        return v


# EOF
