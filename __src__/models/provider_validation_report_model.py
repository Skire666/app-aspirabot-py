"""Model describing the result of a provider validation run."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from dataclasses import dataclass, field

from models.provider_validation_issue_model import ProviderValidationIssue


def _default_issues() -> list[ProviderValidationIssue]:
    return []


@dataclass
class ProviderValidationReport:
    """Represents the aggregated outcome of a providers validation pass."""

    total_files: int
    valid_files: int
    invalid_files: int
    issues: list[ProviderValidationIssue] = field(default_factory=_default_issues)
