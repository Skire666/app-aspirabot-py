"""Model describing a validation issue detected on a provider file."""

from dataclasses import dataclass
from typing import List


@dataclass
class ProviderValidationIssue:
    """Represents a single invalid provider file and the reasons it failed."""

    file_name: str
    original_path: str
    broken_path: str
    reasons: List[str]