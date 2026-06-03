"""Tests for shared/step_registry.py."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from shared.enums import StepTypeEnum
from shared.exception_util import (
    ExecutorNotRegisteredError,
    FormNotRegisteredError,
    NoExecutorsRegisteredError,
    ParamsBuilderNotRegisteredError,
)


def _fresh_registry() -> object:
    """Return the step_registry module after clearing its internal dicts."""
    import importlib

    import shared.step_registry as reg

    importlib.reload(reg)
    return reg


class TestRegisterAndGetStepExecutor:
    def test_register_then_get(self) -> None:
        reg = _fresh_registry()
        executor = MagicMock()
        executor.step_type.return_value = StepTypeEnum.E_OPEN_URL
        reg.register_step_executor(executor)
        result = reg.get_step_executor(StepTypeEnum.E_OPEN_URL)
        assert result is executor

    def test_get_when_empty_raises_no_executors(self) -> None:
        reg = _fresh_registry()
        with pytest.raises(NoExecutorsRegisteredError):
            reg.get_step_executor(StepTypeEnum.E_OPEN_URL)

    def test_get_unregistered_type_raises_executor_not_registered(self) -> None:
        reg = _fresh_registry()
        executor = MagicMock()
        executor.step_type.return_value = StepTypeEnum.E_CLOSE_TABS
        reg.register_step_executor(executor)
        with pytest.raises(ExecutorNotRegisteredError):
            reg.get_step_executor(StepTypeEnum.E_OPEN_URL)


class TestRegisterAndGetForm:
    def test_register_then_get(self) -> None:
        reg = _fresh_registry()
        form = MagicMock()
        form.step_type.return_value = StepTypeEnum.E_SECTION_STEPS
        reg.register_form(form)
        result = reg.get_form(StepTypeEnum.E_SECTION_STEPS)
        assert result is form

    def test_get_unregistered_form_raises(self) -> None:
        reg = _fresh_registry()
        with pytest.raises(FormNotRegisteredError):
            reg.get_form(StepTypeEnum.E_OPEN_URL)


class TestRegisterAndBuildParams:
    def test_register_then_build(self) -> None:
        reg = _fresh_registry()
        fake_params = MagicMock()
        builder = MagicMock(return_value=fake_params)
        reg.register_params_builder(StepTypeEnum.E_WAIT_FIXED_TIME, builder)
        result = reg.build_params(StepTypeEnum.E_WAIT_FIXED_TIME, {"duration": 5, "unit": "s"})
        assert result is fake_params
        builder.assert_called_once_with({"duration": 5, "unit": "s"})

    def test_build_unregistered_raises(self) -> None:
        reg = _fresh_registry()
        with pytest.raises(ParamsBuilderNotRegisteredError):
            reg.build_params(StepTypeEnum.E_OPEN_URL, {})

    def test_latest_registration_overwrites(self) -> None:
        reg = _fresh_registry()
        builder1 = MagicMock(return_value="first")
        builder2 = MagicMock(return_value="second")
        reg.register_params_builder(StepTypeEnum.E_KILL_BROWSER, builder1)
        reg.register_params_builder(StepTypeEnum.E_KILL_BROWSER, builder2)
        result = reg.build_params(StepTypeEnum.E_KILL_BROWSER, {})
        assert result == "second"
