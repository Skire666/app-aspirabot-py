"""Tests for WorkflowService business-rule validation.

All tests run in isolation — no file I/O, no Tkinter.
"""

import sys
from pathlib import Path

# Allow imports from __src__ without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "__src__"))

import pytest
from models.step_scrapping_model import StepScrappingModel, StepType
from models.workflow_model import WorkflowModel
from services.workflow_service import WorkflowService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def service() -> WorkflowService:
    """Returns a fresh WorkflowService instance."""
    return WorkflowService()


def _open_url_step(url: str = "https://example.com/") -> StepScrappingModel:
    """Creates a valid OPEN_URL step."""
    return StepScrappingModel(
        step_type=StepType.OPEN_URL,
        params={"url": url, "wait_state": "domcontentloaded"},
    )


def _sleep_step(duration: float = 1.0, unit: str = "second") -> StepScrappingModel:
    """Creates a valid SLEEP step."""
    return StepScrappingModel(
        step_type=StepType.SLEEP,
        params={"duration": duration, "unit": unit},
    )


def _random_pause_step(
    min_val: float = 1.0, max_val: float = 3.0, unit: str = "second"
) -> StepScrappingModel:
    """Creates a valid RANDOM_PAUSE step."""
    return StepScrappingModel(
        step_type=StepType.RANDOM_PAUSE,
        params={"min": min_val, "max": max_val, "unit": unit},
    )


# ---------------------------------------------------------------------------
# Empty workflow
# ---------------------------------------------------------------------------


def test_validate_empty_workflow_returns_error(service: WorkflowService) -> None:
    """An empty step list must produce exactly one error."""
    workflow = WorkflowModel(provider_id_file="x")
    errors = service.validate(workflow)
    assert len(errors) == 1
    assert "au moins une étape" in errors[0]


# ---------------------------------------------------------------------------
# First-step constraint
# ---------------------------------------------------------------------------


def test_validate_first_step_not_open_url_returns_error(
    service: WorkflowService,
) -> None:
    """First step that is not OPEN_URL must produce a specific error."""
    workflow = WorkflowModel(provider_id_file="x", steps=[_sleep_step()])
    errors = service.validate(workflow)
    assert any("OPEN_URL" in e for e in errors)


def test_validate_first_step_open_url_passes(service: WorkflowService) -> None:
    """A workflow starting with OPEN_URL must not produce that error."""
    workflow = WorkflowModel(provider_id_file="x", steps=[_open_url_step()])
    errors = service.validate(workflow)
    assert not any("OPEN_URL" in e for e in errors)


# ---------------------------------------------------------------------------
# OPEN_URL param validation
# ---------------------------------------------------------------------------


def test_validate_open_url_empty_url_returns_error(service: WorkflowService) -> None:
    """OPEN_URL with a blank URL must be flagged."""
    step = StepScrappingModel(step_type=StepType.OPEN_URL, params={"url": "   ", "wait_state": "load"})
    workflow = WorkflowModel(provider_id_file="x", steps=[step])
    errors = service.validate(workflow)
    assert any("url" in e.lower() for e in errors)


def test_validate_open_url_invalid_wait_state(service: WorkflowService) -> None:
    """OPEN_URL with an unknown wait_state must be flagged."""
    step = StepScrappingModel(
        step_type=StepType.OPEN_URL,
        params={"url": "https://example.com/", "wait_state": "invalid"},
    )
    workflow = WorkflowModel(provider_id_file="x", steps=[step])
    errors = service.validate(workflow)
    assert any("wait_state" in e for e in errors)


def test_validate_open_url_valid(service: WorkflowService) -> None:
    """A valid OPEN_URL step must produce no errors."""
    workflow = WorkflowModel(provider_id_file="x", steps=[_open_url_step()])
    assert service.validate(workflow) == []


# ---------------------------------------------------------------------------
# RANDOM_PAUSE min < max constraint
# ---------------------------------------------------------------------------


def test_validate_random_pause_min_equals_max(service: WorkflowService) -> None:
    """RANDOM_PAUSE where min == max must produce an error."""
    workflow = WorkflowModel(
        provider_id_file="x",
        steps=[_open_url_step(), _random_pause_step(min_val=2.0, max_val=2.0)],
    )
    errors = service.validate(workflow)
    assert any("min" in e and "max" in e for e in errors)


def test_validate_random_pause_min_greater_than_max(service: WorkflowService) -> None:
    """RANDOM_PAUSE where min > max must produce an error."""
    workflow = WorkflowModel(
        provider_id_file="x",
        steps=[_open_url_step(), _random_pause_step(min_val=5.0, max_val=2.0)],
    )
    errors = service.validate(workflow)
    assert any("min" in e and "max" in e for e in errors)


def test_validate_random_pause_valid(service: WorkflowService) -> None:
    """A valid RANDOM_PAUSE step must produce no errors."""
    workflow = WorkflowModel(
        provider_id_file="x",
        steps=[_open_url_step(), _random_pause_step(min_val=1.0, max_val=3.0)],
    )
    assert service.validate(workflow) == []


# ---------------------------------------------------------------------------
# SLEEP validation
# ---------------------------------------------------------------------------


def test_validate_sleep_non_numeric_duration(service: WorkflowService) -> None:
    """SLEEP with a string duration must be flagged."""
    step = StepScrappingModel(step_type=StepType.SLEEP, params={"duration": "fast", "unit": "second"})
    workflow = WorkflowModel(provider_id_file="x", steps=[_open_url_step(), step])
    errors = service.validate(workflow)
    assert any("duration" in e for e in errors)


def test_validate_sleep_invalid_unit(service: WorkflowService) -> None:
    """SLEEP with an unknown unit must be flagged."""
    step = StepScrappingModel(step_type=StepType.SLEEP, params={"duration": 1, "unit": "nanosecond"})
    workflow = WorkflowModel(provider_id_file="x", steps=[_open_url_step(), step])
    errors = service.validate(workflow)
    assert any("unit" in e for e in errors)


# ---------------------------------------------------------------------------
# CLICK_ELEMENT validation
# ---------------------------------------------------------------------------


def test_validate_click_element_empty_selector(service: WorkflowService) -> None:
    """CLICK_ELEMENT with a blank selector must be flagged."""
    step = StepScrappingModel(
        step_type=StepType.CLICK_ELEMENT,
        params={"selector": "", "click_mode": "Normal"},
    )
    workflow = WorkflowModel(provider_id_file="x", steps=[_open_url_step(), step])
    errors = service.validate(workflow)
    assert any("selector" in e for e in errors)


def test_validate_click_element_invalid_mode(service: WorkflowService) -> None:
    """CLICK_ELEMENT with an unknown click_mode must be flagged."""
    step = StepScrappingModel(
        step_type=StepType.CLICK_ELEMENT,
        params={"selector": ".btn", "click_mode": "Magic"},
    )
    workflow = WorkflowModel(provider_id_file="x", steps=[_open_url_step(), step])
    errors = service.validate(workflow)
    assert any("click_mode" in e for e in errors)


# ---------------------------------------------------------------------------
# SCROLL_DOWN validation
# ---------------------------------------------------------------------------


def test_validate_scroll_down_non_int_pixels(service: WorkflowService) -> None:
    """SCROLL_DOWN with a float pixels value must be flagged."""
    step = StepScrappingModel(step_type=StepType.SCROLL_DOWN, params={"pixels": 1.5})
    workflow = WorkflowModel(provider_id_file="x", steps=[_open_url_step(), step])
    errors = service.validate(workflow)
    assert any("pixels" in e for e in errors)


def test_validate_scroll_down_valid(service: WorkflowService) -> None:
    """A valid SCROLL_DOWN step must produce no errors."""
    step = StepScrappingModel(step_type=StepType.SCROLL_DOWN, params={"pixels": 500})
    workflow = WorkflowModel(provider_id_file="x", steps=[_open_url_step(), step])
    assert service.validate(workflow) == []


# ---------------------------------------------------------------------------
# Full valid workflow
# ---------------------------------------------------------------------------


def test_validate_multi_step_valid_workflow(service: WorkflowService) -> None:
    """A well-formed multi-step workflow must return no errors."""
    steps = [
        _open_url_step(),
        _sleep_step(2, "second"),
        StepScrappingModel(
            step_type=StepType.CLICK_ELEMENT,
            params={"selector": "#submit", "click_mode": "Normal"},
        ),
        StepScrappingModel(step_type=StepType.SCROLL_DOWN, params={"pixels": 300}),
    ]
    workflow = WorkflowModel(provider_id_file="x", steps=steps)
    assert service.validate(workflow) == []
