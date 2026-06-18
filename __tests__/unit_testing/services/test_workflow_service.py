"""Tests for services/workflow_service.py."""

from __future__ import annotations

from unittest.mock import MagicMock

from models.step_scraping_model import StepScrapingModel
from services.workflow_service import WorkflowService
from shared.enums import StepTypeEnum


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_step(step_type: StepTypeEnum = StepTypeEnum.E_SCROLL_DOWN, step_id: str = "s1") -> StepScrapingModel:
    step = MagicMock(spec=StepScrapingModel)
    step.step_type = step_type
    step.step_id = step_id
    step.params = MagicMock()
    step.params.validate_with_context.return_value = []
    return step


def _make_full_steps(validate_errors: list[str] | None = None) -> tuple[StepScrapingModel, list[StepScrapingModel]]:
    """Return (target_step, full_steps_list) with required E_OPEN_URL and E_KILL_BROWSER."""
    target = _make_step(StepTypeEnum.E_SCROLL_DOWN, "target")
    if validate_errors is not None:
        target.params.validate_with_context.return_value = validate_errors
    open_url = _make_step(StepTypeEnum.E_OPEN_URL, "open")
    kill = _make_step(StepTypeEnum.E_KILL_BROWSER, "kill")
    return target, [open_url, target, kill]


# ---------------------------------------------------------------------------
# validate_step
# ---------------------------------------------------------------------------


class TestValidateStep:
    def test_returns_empty_list_when_no_errors(self) -> None:
        target, steps = _make_full_steps(validate_errors=[])
        result = WorkflowService.validate_step(0, target, steps)
        assert result == []

    def test_returns_error_messages_from_executor(self) -> None:
        target, steps = _make_full_steps(validate_errors=["Field required"])
        result = WorkflowService.validate_step(0, target, steps)
        assert result == ["Field required"]

    def test_returns_empty_list_on_no_executors_registered(self) -> None:
        target, steps = _make_full_steps(validate_errors=[])
        result = WorkflowService.validate_step(0, target, steps)
        assert result == []

    def test_returns_empty_list_on_executor_not_registered(self) -> None:
        target, steps = _make_full_steps(validate_errors=[])
        result = WorkflowService.validate_step(0, target, steps)
        assert result == []

    def test_passes_step_index_to_executor(self) -> None:
        target, steps = _make_full_steps()
        WorkflowService.validate_step(3, target, steps)
        call_args = target.params.validate_with_context.call_args
        assert call_args[0][0] == 3
