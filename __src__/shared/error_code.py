# i_error_code.py
from __future__ import annotations

from shared.enums import ErrorSeverityEnum


class ErrorCode:
    """Interface commune à tous les ErrorCode."""

    code: str
    user_message: str
    severity: ErrorSeverityEnum
