# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from enum import Enum


class ErrorCode(Enum):
    """Interface commune à tous les ErrorCode."""

    def __str__(self) -> str:
        """Retourne une représentation textuelle de l'ErrorCode."""
        return f"#{self.name}"


# EOF
