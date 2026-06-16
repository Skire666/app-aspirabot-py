# i_error_code.py

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from shared.enums import SeverityEnum


class ErrorCode:
    """Interface commune à tous les ErrorCode."""

    code: str
    user_message: str
    severity: SeverityEnum

    def __str__(self) -> str:
        """Retourne une représentation textuelle de l'ErrorCode."""
        return f"{self.code}: {self.user_message}"

    def is_fatal_or_error(self) -> bool:
        """Retourne True si la sévérité est E_FATAL ou E_ERROR."""
        return self.severity in {SeverityEnum.E_FATAL, SeverityEnum.E_ERROR}

    def is_warning(self) -> bool:
        """Retourne True si la sévérité est E_WARNING."""
        return self.severity == SeverityEnum.E_WARNING


# EOF
