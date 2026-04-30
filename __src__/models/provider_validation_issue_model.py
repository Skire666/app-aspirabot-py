"""Model describing a validation issue detected on a provider file."""

from dataclasses import dataclass


@dataclass
class ProviderValidationIssue:
    """Represents a single invalid provider file and the reasons it failed."""

    file_name: str # "provider1.json"
    original_path: str # "providers/provider1.json"
    broken_path: str # "providers/broken/provider1.json"
    reasons: list[str] # ["Missing required field 'name'", "Invalid value for 'type' ...]
