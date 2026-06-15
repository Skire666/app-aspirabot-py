"""Shared helpers for step parameter models."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from pydantic import ValidationError


def step_label(context: dict[str, object] | None) -> str:
    """Return zero-padded step label from validation context, or '??' when absent."""
    if not context:
        return "??"
    idx = context.get("step_index", -1)
    return str(int(idx) + 1).zfill(2) if isinstance(idx, int) and idx >= 0 else "??"


def extract_pydantic_errors(exc: ValidationError) -> list[str]:
    """Extract human-readable error strings from a Pydantic ValidationError."""
    return [
        str(err["ctx"]["error"]) if "ctx" in err and "error" in err["ctx"] else err["msg"]
        for err in exc.errors()
    ]


# EOF
