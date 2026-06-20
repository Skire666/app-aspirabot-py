# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass, field
from typing import Any

from shared.enums import SeverityEnum
from shared.error_code import ErrorCode


@dataclass
class ValidationIssue:
    """Represents a validation issue with its code, severity, and context."""

    code: ErrorCode
    severity: SeverityEnum
    context: dict[str, Any] = field(default_factory=dict[str, Any])

    def __init__(self, code: ErrorCode, severity: SeverityEnum, context: dict[str, Any] | None = None) -> None:
        """Initialize the ValidationIssue with its attributes."""
        self.code = code
        self.severity = severity
        self.context = context or {}

    @property
    def message(self) -> str:
        """Return the formatted message for the validation issue."""
        try:
            return self.code.value.format(**self.context)
        except KeyError, IndexError:
            return self.code.value  # fallback si contexte incomplet


@dataclass
class ValidationResult:
    """Accumulates validation issues with severity-keyed counters for efficient querying."""

    issues: list[ValidationIssue] = field(default_factory=list[ValidationIssue])
    count_warnings: int = 0
    count_errors: int = 0
    count_fatals: int = 0

    def append(self, code: ErrorCode, severity: SeverityEnum, context: dict[str, Any] | None = None) -> None:
        """Append a new ValidationIssue and increment the matching severity counter."""
        self.issues.append(ValidationIssue(code=code, severity=severity, context=context or {}))
        if severity == SeverityEnum.E_WARNING:
            self.count_warnings += 1
        elif severity == SeverityEnum.E_ERROR:
            self.count_errors += 1
        elif severity == SeverityEnum.E_FATAL:
            self.count_fatals += 1

    def extend(self, other: ValidationResult) -> None:
        """Merge another ValidationResult into this one."""
        self.issues.extend(other.issues)
        self.count_warnings += other.count_warnings
        self.count_errors += other.count_errors
        self.count_fatals += other.count_fatals

    def has_issues(self) -> bool:
        """Return True if there are any validation issues, False otherwise."""
        return bool(self.issues)

    def has_errors_or_fatals(self) -> bool:
        """Return True if there are any validation errors or fatals, False otherwise."""
        return self.count_errors > 0 or self.count_fatals > 0

    def has_warnings(self) -> bool:
        """Return True if there are any validation warnings, False otherwise."""
        return self.count_warnings > 0

    def _collect_issues(
        self, severity: SeverityEnum, label: str, nbr_max: int, concat: str, nbr_pushed: int
    ) -> tuple[str, int]:
        """Append formatted issues of one severity to concat, stopping at nbr_max total."""
        for issue in self.issues:
            if nbr_pushed >= nbr_max:
                break
            if issue.severity == severity:
                concat += f"{label} : {issue.code} - {issue.message}\n"
                nbr_pushed += 1
        return concat, nbr_pushed

    def compute_displayable_issues(self, nbr_max: int = 2) -> str:
        """Compute a displayable string of validation issues."""
        if not self.issues:
            return "--"
        concat = ""
        nbr_pushed = 0
        if self.count_fatals > 0:
            concat, nbr_pushed = self._collect_issues(SeverityEnum.E_FATAL, "FATAL", nbr_max, concat, nbr_pushed)
        if self.count_errors > 0 and nbr_pushed < nbr_max:
            concat, nbr_pushed = self._collect_issues(SeverityEnum.E_ERROR, "ERROR", nbr_max, concat, nbr_pushed)
        if self.count_warnings > 0 and nbr_pushed < nbr_max:
            concat, nbr_pushed = self._collect_issues(SeverityEnum.E_WARNING, "WARNING", nbr_max, concat, nbr_pushed)
        return concat.strip()

    def clear(self) -> None:
        """Clear all validation issues and reset counts."""
        self.issues.clear()
        self.count_warnings = 0
        self.count_errors = 0
        self.count_fatals = 0


# EOF
