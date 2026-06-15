# i_error_code.py

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from shared.enums import ErrorSeverityEnum


class ErrorCode:
    """Interface commune à tous les ErrorCode."""

    code: str
    user_message: str
    severity: ErrorSeverityEnum

    def __str__(self) -> str:
        """Retourne une représentation textuelle de l'ErrorCode."""
        return f"{self.code}: {self.user_message}"


# EOF
