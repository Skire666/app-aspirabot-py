"""Additional tests for services/workflow_service.py — validate_all_steps and structure validation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from models.step_scraping_model import StepScrapingModel
from services.workflow_service import WorkflowService
from shared.enums import StepTypeEnum
from shared.exception_util import ExecutorNotRegisteredError, NoExecutorsRegisteredError

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


def _minimal_valid_steps(validate_errors: list[str] | None = None) -> list[StepScrapingModel]:
    """Minimal structurally valid workflow that passes all structure checks."""
    open_url = _make_step(StepTypeEnum.E_OPEN_URL, "open")
    kill = _make_step(StepTypeEnum.E_KILL_BROWSER, "kill")
    if validate_errors is not None:
        open_url.params.validate_with_context.return_value = validate_errors
    return [open_url, kill]


# ---------------------------------------------------------------------------
# validate_step edge cases
# ---------------------------------------------------------------------------


class TestValidateStepEdgeCases:
    def test_returns_message_when_params_is_none(self) -> None:
        step = _make_step()
        step.params = None
        result = WorkflowService.validate_step(0, step, [])
        assert len(result) == 1
        assert "no params" in result[0].lower()

    def test_returns_message_when_validate_with_context_is_none(self) -> None:
        step = _make_step()
        step.params = MagicMock()
        step.params.validate_with_context = None
        result = WorkflowService.validate_step(0, step, [])
        assert len(result) == 1

    def test_returns_empty_on_no_executors_registered(self) -> None:
        step = _make_step()
        step.params.validate_with_context.side_effect = NoExecutorsRegisteredError()
        result = WorkflowService.validate_step(0, step, [])
        assert result == []

    def test_returns_empty_on_executor_not_registered(self) -> None:
        step = _make_step()
        step.params.validate_with_context.side_effect = ExecutorNotRegisteredError("x")
        result = WorkflowService.validate_step(0, step, [])
        assert result == []


# ---------------------------------------------------------------------------
# validate_all_steps
# ---------------------------------------------------------------------------


class TestValidateAllSteps:
    def test_returns_errors_when_no_open_url(self) -> None:
        steps = [_make_step(StepTypeEnum.E_KILL_BROWSER, "kill")]
        result = WorkflowService.validate_all_steps(steps)
        assert len(result) > 0

    def test_returns_errors_when_no_kill_browser(self) -> None:
        steps = [_make_step(StepTypeEnum.E_OPEN_URL, "open")]
        result = WorkflowService.validate_all_steps(steps)
        assert len(result) > 0

    def test_structure_errors_halt_before_param_validation(self) -> None:
        open_url = _make_step(StepTypeEnum.E_OPEN_URL, "open")
        open_url.params.validate_with_context.return_value = ["step error"]
        steps = [open_url]  # missing KILL_BROWSER → structure error
        result = WorkflowService.validate_all_steps(steps)
        # Should return structure errors, not step-level errors
        assert "step error" not in result


# ---------------------------------------------------------------------------
# _validate_workflow_structure (via validate_all_steps indirectly)
# ---------------------------------------------------------------------------


class TestStructureValidation:
    def test_error_when_two_open_url_steps(self) -> None:
        steps = [
            _make_step(StepTypeEnum.E_OPEN_URL, "open1"),
            _make_step(StepTypeEnum.E_OPEN_URL, "open2"),
            _make_step(StepTypeEnum.E_KILL_BROWSER, "kill"),
        ]
        result = WorkflowService.validate_all_steps(steps)
        assert len(result) > 0

    def test_error_when_open_url_not_at_beginning(self) -> None:
        steps = [
            _make_step(StepTypeEnum.E_SCROLL_DOWN, "s"),
            _make_step(StepTypeEnum.E_OPEN_URL, "open"),
            _make_step(StepTypeEnum.E_KILL_BROWSER, "kill"),
        ]
        result = WorkflowService.validate_all_steps(steps)
        assert len(result) > 0

    def test_error_when_two_kill_browser_steps(self) -> None:
        steps = [
            _make_step(StepTypeEnum.E_OPEN_URL, "open"),
            _make_step(StepTypeEnum.E_KILL_BROWSER, "kill1"),
            _make_step(StepTypeEnum.E_KILL_BROWSER, "kill2"),
        ]
        result = WorkflowService.validate_all_steps(steps)
        assert len(result) > 0

    def test_error_when_kill_browser_not_at_end(self) -> None:
        steps = [
            _make_step(StepTypeEnum.E_OPEN_URL, "open"),
            _make_step(StepTypeEnum.E_KILL_BROWSER, "kill"),
            _make_step(StepTypeEnum.E_SCROLL_DOWN, "s"),
        ]
        result = WorkflowService.validate_all_steps(steps)
        assert len(result) > 0

    def test_error_when_consecutive_jump_to_steps(self) -> None:
        steps = [
            _make_step(StepTypeEnum.E_OPEN_URL, "open"),
            _make_step(StepTypeEnum.E_JUMP_TO_STEP, "j1"),
            _make_step(StepTypeEnum.E_JUMP_TO_STEP, "j2"),
            _make_step(StepTypeEnum.E_KILL_BROWSER, "kill"),
        ]
        result = WorkflowService.validate_all_steps(steps)
        assert len(result) > 0

    def test_error_when_duplicate_step_ids(self) -> None:
        steps = [_make_step(StepTypeEnum.E_OPEN_URL, "dup"), _make_step(StepTypeEnum.E_KILL_BROWSER, "dup")]
        result = WorkflowService.validate_all_steps(steps)
        assert len(result) > 0

    def test_error_when_consecutive_restart_to_beginning(self) -> None:
        steps = [
            _make_step(StepTypeEnum.E_OPEN_URL, "open"),
            _make_step(StepTypeEnum.E_RESTART_TO_BEGINNING, "r1"),
            _make_step(StepTypeEnum.E_RESTART_TO_BEGINNING, "r2"),
            _make_step(StepTypeEnum.E_KILL_BROWSER, "kill"),
        ]
        result = WorkflowService.validate_all_steps(steps)
        assert len(result) > 0

    def test_error_when_restart_not_after_open_url(self) -> None:
        steps = [_make_step(StepTypeEnum.E_RESTART_TO_BEGINNING, "r1"), _make_step(StepTypeEnum.E_KILL_BROWSER, "kill")]
        result = WorkflowService.validate_all_steps(steps)
        assert len(result) > 0

    def test_error_when_extract_step_without_export_step(self) -> None:
        steps = [
            _make_step(StepTypeEnum.E_OPEN_URL, "open"),
            _make_step(StepTypeEnum.E_EXTRACT_TEXTS, "extract"),
            _make_step(StepTypeEnum.E_KILL_BROWSER, "kill"),
        ]
        result = WorkflowService.validate_all_steps(steps)
        assert len(result) > 0


class TestValidateAllStepsOuterExcept:
    def test_returns_empty_when_collection_constructor_raises(self) -> None:
        with patch("services.workflow_service.StepsCollections", side_effect=NoExecutorsRegisteredError()):
            result = WorkflowService.validate_all_steps([])
        assert result == []
