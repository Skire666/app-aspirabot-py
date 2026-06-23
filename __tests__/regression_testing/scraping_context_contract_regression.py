"""Regression tests — models/scraping_context_model.py.

Freezes the observable behaviour of ScrapingContextModel state transitions
that are NOT covered by unit tests:
  - last_step_was_success() contract for every StepExecutionResultEnum value
  - last_result_is_error() contract for every StepExecutionResultEnum value
  - reset_exported_data() clears extracted_data
  - set_result_execution() sets last_time_elapsed > 0 after prepare_step_execution()
  - push_extracted_values() auto-creates extracted_data when it is None
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from models.app_configuration_model import AppConfigurationModel
from models.extracted_data_model import ExtractedData
from models.scraping_context_model import ScrapingContextModel
from shared.enums import StepExecutionResultEnum


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_context() -> ScrapingContextModel:
    cfg = MagicMock(spec=AppConfigurationModel)
    return ScrapingContextModel(model_config=cfg)


def _make_step(step_id: str = "s1") -> MagicMock:
    s = MagicMock()
    s.step_id = step_id
    return s


# ---------------------------------------------------------------------------
# last_step_was_success — contract for every result value
# ---------------------------------------------------------------------------


class TestLastStepWasSuccess:
    @pytest.mark.parametrize(
        "result, expected",
        [
            (StepExecutionResultEnum.E_SUCCESS, True),
            (StepExecutionResultEnum.E_WARNING, True),
            (StepExecutionResultEnum.E_SKIPPED, True),
            (StepExecutionResultEnum.E_ERROR, False),
            (StepExecutionResultEnum.E_FATAL, False),
            (StepExecutionResultEnum.E_UNSET, False),
        ],
        ids=["success", "warning", "skipped", "error", "fatal", "unset"],
    )
    def test_last_step_was_success_by_result(self, result: StepExecutionResultEnum, expected: bool) -> None:
        ctx = _make_context()
        ctx.last_result_step = result
        assert ctx.last_step_was_success() is expected, (
            f"last_step_was_success() must return {expected} for result={result.name}"
        )


# ---------------------------------------------------------------------------
# last_result_is_error — contract for every result value
# ---------------------------------------------------------------------------


class TestLastResultIsError:
    @pytest.mark.parametrize(
        "result, expected",
        [
            (StepExecutionResultEnum.E_ERROR, True),
            (StepExecutionResultEnum.E_FATAL, True),
            (StepExecutionResultEnum.E_SUCCESS, False),
            (StepExecutionResultEnum.E_WARNING, False),
            (StepExecutionResultEnum.E_SKIPPED, False),
            (StepExecutionResultEnum.E_UNSET, False),
        ],
        ids=["error", "fatal", "success", "warning", "skipped", "unset"],
    )
    def test_last_result_is_error_by_result(self, result: StepExecutionResultEnum, expected: bool) -> None:
        ctx = _make_context()
        ctx.last_result_step = result
        assert ctx.last_result_is_error() is expected, (
            f"last_result_is_error() must return {expected} for result={result.name}"
        )


# ---------------------------------------------------------------------------
# reset_exported_data — clears extracted_data
# ---------------------------------------------------------------------------


class TestResetExportedData:
    def test_clears_existing_extracted_data(self) -> None:
        ctx = _make_context()
        ctx.extracted_data = ExtractedData()
        ctx.extracted_data.append_item("k", "sel", ["v"], "")
        assert not ctx.extracted_data.is_empty(), "precondition: data must be non-empty before reset"

        ctx.reset_exported_data()

        assert ctx.extracted_data is not None, "reset_exported_data must not set extracted_data to None"
        assert ctx.extracted_data.is_empty(), "reset_exported_data must produce an empty ExtractedData"

    def test_empty_after_reset_is_fresh_instance(self) -> None:
        ctx = _make_context()
        ctx.extracted_data = ExtractedData()
        old = ctx.extracted_data
        ctx.reset_exported_data()
        assert ctx.extracted_data is not old, "reset_exported_data must replace the ExtractedData instance"


# ---------------------------------------------------------------------------
# set_result_execution — time tracking
# ---------------------------------------------------------------------------


class TestSetResultExecution:
    def test_last_time_elapsed_positive_after_set(self) -> None:
        ctx = _make_context()
        ctx.prepare_step_execution(_make_step())
        ctx.set_result_execution(StepExecutionResultEnum.E_SUCCESS)
        assert ctx.last_time_elapsed > 0, (
            "last_time_elapsed must be > 0 after set_result_execution (at least 1 ms added)"
        )

    def test_last_result_step_stored(self) -> None:
        ctx = _make_context()
        ctx.prepare_step_execution(_make_step())
        ctx.set_result_execution(StepExecutionResultEnum.E_FATAL)
        assert ctx.last_result_step is StepExecutionResultEnum.E_FATAL

    def test_time_elapsed_zero_before_set(self) -> None:
        ctx = _make_context()
        step = _make_step()
        ctx.prepare_step_execution(step)
        assert ctx.last_time_elapsed == 0.0, "prepare_step_execution must reset last_time_elapsed to 0.0"


# ---------------------------------------------------------------------------
# push_extracted_values — auto-creates ExtractedData when None
# ---------------------------------------------------------------------------


class TestPushExtractedValuesNullGuard:
    def test_creates_extracted_data_when_none(self) -> None:
        ctx = _make_context()
        ctx.extracted_data = None  # type: ignore[assignment]

        ctx.push_extracted_values("key1", ".sel", "comment", ["v1", "v2"])

        assert ctx.extracted_data is not None, "push_extracted_values must create ExtractedData if it was None"
        assert "key1" in ctx.extracted_data

    def test_values_correct_after_autocreate(self) -> None:
        ctx = _make_context()
        ctx.extracted_data = None  # type: ignore[assignment]

        ctx.push_extracted_values("price", ".price", "", ["$99"])

        assert ctx.extracted_data["price"].values == ["$99"]


# ---------------------------------------------------------------------------
# reset_before_new_process — additional contracts not in unit tests
# ---------------------------------------------------------------------------


class TestResetBeforeNewProcessContract:
    def test_resets_last_result_to_success(self) -> None:
        ctx = _make_context()
        ctx.last_result_step = StepExecutionResultEnum.E_FATAL
        ctx.reset_before_new_process([])
        assert ctx.last_result_step is StepExecutionResultEnum.E_SUCCESS, (
            "reset_before_new_process must initialise last_result_step to E_SUCCESS"
        )

    def test_resets_end_process_to_false(self) -> None:
        ctx = _make_context()
        ctx.end_process = True
        ctx.reset_before_new_process([])
        assert ctx.end_process is False

    def test_resets_pending_jump_to_none(self) -> None:
        ctx = _make_context()
        ctx.pending_jump = "step_abc"
        ctx.reset_before_new_process([])
        assert ctx.pending_jump is None

    def test_resets_browser_stats(self) -> None:
        ctx = _make_context()
        ctx.browser_stats = (42, "some info")
        ctx.reset_before_new_process([])
        assert ctx.browser_stats == (0, "—"), "browser_stats must reset to (0, '—')"

    def test_clears_log_messages(self) -> None:
        ctx = _make_context()
        ctx.log_messages = ["msg1", "msg2"]
        ctx.reset_before_new_process([])
        assert ctx.log_messages == []
