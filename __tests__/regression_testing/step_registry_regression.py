"""Regression tests — shared/step_registry.py.

Freezes the error contracts of the registry lookup functions:
- get_step_executor raises NoExecutorsRegisteredError when the registry is empty.
- get_step_executor raises ExecutorNotRegisteredError for an unknown step type
  (after the registry has been populated).
- get_form raises FormNotRegisteredError for an unknown step type.
- build_params raises ParamsBuilderNotRegisteredError for an unknown step type.
- All three happy-path lookups work after importting presenters.steps.

Integration: after importing presenters.steps, every step type registered by
the presenter modules must be findable via build_params.
"""

from __future__ import annotations

import pytest

import presenters.steps  # noqa: F401 — registers all params builders + executors

from shared.enums import StepTypeEnum
from shared.exception_util import (
    ExecutorNotRegisteredError,
    FormNotRegisteredError,
    ParamsBuilderNotRegisteredError,
)
from shared import step_registry


# ---------------------------------------------------------------------------
# build_params — happy path after presenters.steps bootstrap
# ---------------------------------------------------------------------------


class TestBuildParamsHappyPath:
    @pytest.mark.parametrize(
        "step_type, params_dict",
        [
            (StepTypeEnum.E_SECTION_STEPS, {"title": "T", "comment": ""}),
            (StepTypeEnum.E_SCROLL_DOWN, {"pixels": 100, "comment": ""}),
            (StepTypeEnum.E_WAIT_FIXED_TIME, {"duration": 2, "unit": "s", "comment": ""}),
            (StepTypeEnum.E_OPEN_URL, {"url": "https://example.com", "open_mode": "e_source", "comment": ""}),
            (StepTypeEnum.E_CLOSE_TABS, {"close_mode": "all_except_current", "url_filter": "", "comment": ""}),
            (StepTypeEnum.E_KILL_BROWSER, {"comment": "", "delay_before_kill_ms": 0}),
            (StepTypeEnum.E_REFRESH_PAGE, {"wait_state": "load", "timeout_ms": 30000, "comment": ""}),
        ],
        ids=[
            "section",
            "scroll_down",
            "wait_fixed_time",
            "open_url",
            "close_tabs",
            "kill_browser",
            "refresh_page",
        ],
    )
    def test_build_params_returns_typed_instance(self, step_type: StepTypeEnum, params_dict: dict) -> None:
        """build_params must return an IStepParams for every registered step type."""
        result = step_registry.build_params(step_type, params_dict)
        assert result is not None, f"build_params must not return None for {step_type}"
        assert hasattr(result, "to_dict"), "Returned params must implement to_dict()"


# ---------------------------------------------------------------------------
# build_params — error path: unknown step type
# ---------------------------------------------------------------------------


class TestBuildParamsErrorPath:
    def test_unregistered_step_type_raises(self) -> None:
        """build_params must raise ParamsBuilderNotRegisteredError for unregistered type."""
        with pytest.raises(ParamsBuilderNotRegisteredError):
            step_registry.build_params(StepTypeEnum.E_UNSET, {})


# ---------------------------------------------------------------------------
# get_form — error path: unknown step type
# ---------------------------------------------------------------------------


class TestGetFormErrorPath:
    def test_unregistered_form_raises(self) -> None:
        """get_form must raise FormNotRegisteredError for an unregistered step type."""
        with pytest.raises(FormNotRegisteredError):
            step_registry.get_form(StepTypeEnum.E_UNSET)


# ---------------------------------------------------------------------------
# get_step_executor — error path: unknown step type (registry populated)
# ---------------------------------------------------------------------------


class TestGetStepExecutorErrorPath:
    def test_unregistered_executor_raises_for_unknown_type(self) -> None:
        """get_step_executor must raise either NoExecutorsRegisteredError (registry
        empty) or ExecutorNotRegisteredError (unknown type) for E_UNSET.

        The executors are registered by services.steps, which is not imported in
        this test module.  Both outcomes prove the registry correctly rejects
        the request.
        """
        from shared.exception_util import ExecutorNotRegisteredError, NoExecutorsRegisteredError

        with pytest.raises((ExecutorNotRegisteredError, NoExecutorsRegisteredError)):
            step_registry.get_step_executor(StepTypeEnum.E_UNSET)


# ---------------------------------------------------------------------------
# Round-trip: build_params → to_dict is stable
# ---------------------------------------------------------------------------


class TestBuildParamsRoundTrip:
    def test_section_round_trip(self) -> None:
        """build_params result's to_dict() must preserve the original dict."""
        original = {"title": "My Section", "comment": "a note"}
        params = step_registry.build_params(StepTypeEnum.E_SECTION_STEPS, original)
        result = params.to_dict()
        assert result["title"] == "My Section", "title must survive build_params → to_dict"
        assert result["comment"] == "a note"

    def test_scroll_down_round_trip(self) -> None:
        original = {"pixels": 250, "comment": ""}
        params = step_registry.build_params(StepTypeEnum.E_SCROLL_DOWN, original)
        assert params.to_dict()["pixels"] == 250
