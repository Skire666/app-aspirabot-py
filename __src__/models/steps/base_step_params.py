"""Pydantic base class shared by all step parameter models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


def step_label(context: dict[str, object] | None) -> str:
    """Return zero-padded step label from validation context, or '??' when absent."""
    if not context:
        return "??"
    idx = context.get("step_index", -1)
    return str(int(idx) + 1).zfill(2) if isinstance(idx, int) and idx >= 0 else "??"


class BaseStepParams(BaseModel):
    """Frozen Pydantic model base for all step parameter models.

    Subclasses declare fields and add ``@field_validator`` / ``@model_validator``
    methods.  Validators are context-aware: they only run when a
    ``context`` dict is supplied via ``model_validate(..., context=ctx)``.
    Construction without context never raises (safe for deserialization).

    The ``context`` dict passed by ``StepExecutorBase.validate_model`` contains:
        - ``step_index`` (int): zero-based position in the workflow.
        - ``steps_context`` (StepsContext): full workflow snapshot.
        - ``step_id`` (str): the current step's own ID (for self-reference checks).
    """

    model_config = ConfigDict(frozen=True)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict (delegates to ``model_dump()``)."""
        return self.model_dump()
