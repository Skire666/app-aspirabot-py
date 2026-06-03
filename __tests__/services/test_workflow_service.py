"""Tests for services/workflow_service.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from models.step_scraping_model import StepScrapingModel
from services.workflow_service import WorkflowService
from shared.enums import StepTypeEnum
from shared.exception_util import ExecutorNotRegisteredError, NoExecutorsRegisteredError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_step(step_type: StepTypeEnum = StepTypeEnum.E_SCROLL_DOWN) -> StepScrapingModel:
    step = MagicMock(spec=StepScrapingModel)
    step.step_type = step_type
    step.step_id = "s1"
    return step


# ---------------------------------------------------------------------------
# validate_step
# ---------------------------------------------------------------------------


class TestValidateStep:
    def test_returns_empty_list_when_no_errors(self) -> None:
        step = _make_step()
        mock_executor = MagicMock()
        mock_executor.validate_model.return_value = []
        with patch("services.workflow_service.get_step_executor", return_value=mock_executor):
            result = WorkflowService.validate_step(0, step, [step])
        assert result == []

    def test_returns_error_messages_from_executor(self) -> None:
        step = _make_step()
        mock_executor = MagicMock()
        mock_executor.validate_model.return_value = ["Field required"]
        with patch("services.workflow_service.get_step_executor", return_value=mock_executor):
            result = WorkflowService.validate_step(0, step, [step])
        assert result == ["Field required"]

    def test_returns_empty_list_on_no_executors_registered(self) -> None:
        step = _make_step()
        with patch("services.workflow_service.get_step_executor", side_effect=NoExecutorsRegisteredError()):
            result = WorkflowService.validate_step(0, step, [step])
        assert result == []

    def test_returns_empty_list_on_executor_not_registered(self) -> None:
        step = _make_step()
        with patch("services.workflow_service.get_step_executor", side_effect=ExecutorNotRegisteredError(StepTypeEnum.E_SCROLL_DOWN)):
            result = WorkflowService.validate_step(0, step, [step])
        assert result == []

    def test_passes_step_index_to_executor(self) -> None:
        step = _make_step()
        mock_executor = MagicMock()
        mock_executor.validate_model.return_value = []
        with patch("services.workflow_service.get_step_executor", return_value=mock_executor):
            WorkflowService.validate_step(3, step, [step])
        call_args = mock_executor.validate_model.call_args
        assert call_args[0][1] == 3
