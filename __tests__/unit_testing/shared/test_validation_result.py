"""Tests for shared/validation_result.py."""

from __future__ import annotations

import pytest

from shared.enums import SeverityEnum
from shared.error_code import ErrorCode
from shared.validation_result import ValidationIssue, ValidationResult


class _Code(ErrorCode):
    CODE_A = "Message {key} here"
    CODE_B = "Simple message"
    CODE_C = "No placeholders"


# ---------------------------------------------------------------------------
# ValidationIssue
# ---------------------------------------------------------------------------


class TestValidationIssue:
    def test_init_sets_code(self) -> None:
        issue = ValidationIssue(code=_Code.CODE_B, severity=SeverityEnum.E_ERROR)
        assert issue.code is _Code.CODE_B

    def test_init_sets_severity(self) -> None:
        issue = ValidationIssue(code=_Code.CODE_B, severity=SeverityEnum.E_WARNING)
        assert issue.severity is SeverityEnum.E_WARNING

    def test_init_default_context_is_empty_dict(self) -> None:
        issue = ValidationIssue(code=_Code.CODE_B, severity=SeverityEnum.E_ERROR)
        assert issue.context == {}

    def test_init_with_context(self) -> None:
        issue = ValidationIssue(code=_Code.CODE_A, severity=SeverityEnum.E_ERROR, context={"key": "val"})
        assert issue.context == {"key": "val"}

    def test_message_formats_context(self) -> None:
        issue = ValidationIssue(code=_Code.CODE_A, severity=SeverityEnum.E_ERROR, context={"key": "world"})
        assert issue.message == "Message world here"

    def test_message_simple(self) -> None:
        issue = ValidationIssue(code=_Code.CODE_B, severity=SeverityEnum.E_ERROR)
        assert issue.message == "Simple message"

    def test_message_missing_key_falls_back_to_template(self) -> None:
        issue = ValidationIssue(code=_Code.CODE_A, severity=SeverityEnum.E_ERROR, context={})
        assert issue.message == "Message {key} here"


# ---------------------------------------------------------------------------
# ValidationResult — counters
# ---------------------------------------------------------------------------


class TestValidationResultCounters:
    def test_initial_state_is_empty(self) -> None:
        vr = ValidationResult()
        assert vr.issues == []
        assert vr.count_warnings == 0
        assert vr.count_errors == 0
        assert vr.count_fatals == 0

    def test_append_warning_increments_warning_counter(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_B, SeverityEnum.E_WARNING)
        assert vr.count_warnings == 1
        assert vr.count_errors == 0
        assert vr.count_fatals == 0

    def test_append_error_increments_error_counter(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_B, SeverityEnum.E_ERROR)
        assert vr.count_errors == 1
        assert vr.count_warnings == 0

    def test_append_fatal_increments_fatal_counter(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_B, SeverityEnum.E_FATAL)
        assert vr.count_fatals == 1

    def test_append_adds_issue_to_list(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_B, SeverityEnum.E_ERROR, {"x": "y"})
        assert len(vr.issues) == 1
        assert vr.issues[0].code is _Code.CODE_B

    def test_extend_merges_issues_and_counters(self) -> None:
        vr1 = ValidationResult()
        vr1.append(_Code.CODE_B, SeverityEnum.E_WARNING)
        vr2 = ValidationResult()
        vr2.append(_Code.CODE_C, SeverityEnum.E_ERROR)
        vr2.append(_Code.CODE_C, SeverityEnum.E_FATAL)
        vr1.extend(vr2)
        assert len(vr1.issues) == 3
        assert vr1.count_warnings == 1
        assert vr1.count_errors == 1
        assert vr1.count_fatals == 1

    def test_extend_with_empty_result_is_no_op(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_B, SeverityEnum.E_ERROR)
        vr.extend(ValidationResult())
        assert len(vr.issues) == 1


# ---------------------------------------------------------------------------
# ValidationResult — predicates
# ---------------------------------------------------------------------------


class TestValidationResultPredicates:
    def test_has_issues_false_when_empty(self) -> None:
        assert ValidationResult().has_issues() is False

    def test_has_issues_true_when_nonempty(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_B, SeverityEnum.E_WARNING)
        assert vr.has_issues() is True

    def test_has_errors_or_fatals_false_when_only_warnings(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_B, SeverityEnum.E_WARNING)
        assert vr.has_errors_or_fatals() is False

    def test_has_errors_or_fatals_true_when_error(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_B, SeverityEnum.E_ERROR)
        assert vr.has_errors_or_fatals() is True

    def test_has_errors_or_fatals_true_when_fatal(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_B, SeverityEnum.E_FATAL)
        assert vr.has_errors_or_fatals() is True

    def test_has_warnings_false_when_no_warnings(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_B, SeverityEnum.E_ERROR)
        assert vr.has_warnings() is False

    def test_has_warnings_true_when_warning(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_B, SeverityEnum.E_WARNING)
        assert vr.has_warnings() is True


# ---------------------------------------------------------------------------
# ValidationResult — compute_displayable_issues
# ---------------------------------------------------------------------------


class TestComputeDisplayableIssues:
    def test_returns_dash_dash_when_empty(self) -> None:
        assert ValidationResult().compute_displayable_issues() == "--"

    def test_shows_fatal_first(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_C, SeverityEnum.E_FATAL)
        result = vr.compute_displayable_issues()
        assert "FATAL" in result

    def test_shows_error_when_no_fatals(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_C, SeverityEnum.E_ERROR)
        result = vr.compute_displayable_issues()
        assert "ERROR" in result

    def test_shows_warning_when_no_errors_or_fatals(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_C, SeverityEnum.E_WARNING)
        result = vr.compute_displayable_issues()
        assert "WARNING" in result

    def test_respects_nbr_max(self) -> None:
        vr = ValidationResult()
        for _ in range(5):
            vr.append(_Code.CODE_C, SeverityEnum.E_ERROR)
        result = vr.compute_displayable_issues(nbr_max=2)
        assert result.count("ERROR") == 2

    def test_fatals_fill_up_max_before_errors(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_C, SeverityEnum.E_FATAL)
        vr.append(_Code.CODE_C, SeverityEnum.E_FATAL)
        vr.append(_Code.CODE_C, SeverityEnum.E_ERROR)
        result = vr.compute_displayable_issues(nbr_max=2)
        assert result.count("FATAL") == 2
        assert "ERROR" not in result

    def test_collect_issues_private_stops_at_max(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_C, SeverityEnum.E_ERROR)
        vr.append(_Code.CODE_C, SeverityEnum.E_ERROR)
        concat, nbr_pushed = vr._collect_issues(SeverityEnum.E_ERROR, "ERROR", 1, "", 0)
        assert nbr_pushed == 1

    def test_result_is_stripped(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_C, SeverityEnum.E_ERROR)
        result = vr.compute_displayable_issues()
        assert not result.endswith("\n")


# ---------------------------------------------------------------------------
# ValidationResult — clear
# ---------------------------------------------------------------------------


class TestValidationResultClear:
    def test_clear_empties_issues(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_B, SeverityEnum.E_ERROR)
        vr.clear()
        assert vr.issues == []

    def test_clear_resets_counters(self) -> None:
        vr = ValidationResult()
        vr.append(_Code.CODE_B, SeverityEnum.E_WARNING)
        vr.append(_Code.CODE_B, SeverityEnum.E_ERROR)
        vr.append(_Code.CODE_B, SeverityEnum.E_FATAL)
        vr.clear()
        assert vr.count_warnings == 0
        assert vr.count_errors == 0
        assert vr.count_fatals == 0
