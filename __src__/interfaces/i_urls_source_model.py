"""Contract for URL source scenarios used by the OPEN_URL executor.

A URL source scenario supplies URLs one at a time to the workflow engine.
Concrete implementations cover manual lists, and folder-based sources.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Protocol

from shared.enums import UrlSourceTypeEnum
from shared.validation_result import ValidationResult

# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------


class IUrlsSourceModel(Protocol):
    """Contract for URL source scenarios used by the OPEN_URL executor."""

    @classmethod
    def get_type_source(cls) -> UrlSourceTypeEnum:
        """Return the type of the URL source.

        Returns:
            The type of the URL source.
        """
        ...

    def validate(self) -> ValidationResult:
        """Check if the URL source model is valid.

        Returns:
            The validation result containing any errors.
        """
        ...


# EOF
