"""Unit tests for JumpToStepExecutor."""

from __future__ import annotations

from models.step_scraping_model import StepScrapingModel
from services.steps.jump_to_step_executor import JumpToStepExecutor
from shared.enums import StepTypeEnum


def _make_step(step_id: str, step_type: StepTypeEnum = StepTypeEnum.E_OPEN_URL) -> StepScrapingModel:
    """Return a minimal StepScrapingModel for test setup."""
    return StepScrapingModel(step_type=step_type, step_id=step_id)


# ---------------------------------------------------------------------------
# step_type / default_params_dict
# ---------------------------------------------------------------------------


def test_step_type_returns_jump_to_step() -> None:
    """step_type() class method must return JUMP_TO_STEP."""
    assert JumpToStepExecutor.step_type() == StepTypeEnum.E_JUMP_TO_STEP


def test_default_params_dict_has_expected_keys() -> None:
    """default_params_dict() must contain condition and target_hexastring."""
    d = JumpToStepExecutor().default_params_dict()
    assert d["condition"] == "success"
    assert d["target_hexastring"] == ""


# ---------------------------------------------------------------------------
# execute_logical — jump conditions
# ---------------------------------------------------------------------------


def test_success_condition_jumps_on_prev_success() -> None:
    """condition='success' with _prev_success=True must set _pending_jump."""
    params: dict = {"condition": "success", "target_hexastring": "abcd", "_prev_success": True}
    JumpToStepExecutor().execute_logical(None, params)  # type: ignore[arg-type]
    assert params.get("_pending_jump") == "abcd"


def test_success_condition_no_jump_on_prev_failure() -> None:
    """condition='success' with _prev_success=False must not jump."""
    params: dict = {"condition": "success", "target_hexastring": "abcd", "_prev_success": False}
    JumpToStepExecutor().execute_logical(None, params)  # type: ignore[arg-type]
    assert "_pending_jump" not in params


def test_failure_condition_jumps_on_prev_failure() -> None:
    """condition='failure' with _prev_success=False must set _pending_jump."""
    params: dict = {"condition": "failure", "target_hexastring": "abcd", "_prev_success": False}
    JumpToStepExecutor().execute_logical(None, params)  # type: ignore[arg-type]
    assert params.get("_pending_jump") == "abcd"


def test_failure_condition_no_jump_on_prev_success() -> None:
    """condition='failure' with _prev_success=True must not jump."""
    params: dict = {"condition": "failure", "target_hexastring": "abcd", "_prev_success": True}
    JumpToStepExecutor().execute_logical(None, params)  # type: ignore[arg-type]
    assert "_pending_jump" not in params


def test_always_condition_jumps_on_success() -> None:
    """condition='always' must jump regardless of prev_success=True."""
    params: dict = {"condition": "always", "target_hexastring": "abcd", "_prev_success": True}
    JumpToStepExecutor().execute_logical(None, params)  # type: ignore[arg-type]
    assert params.get("_pending_jump") == "abcd"


def test_always_condition_jumps_on_failure() -> None:
    """condition='always' must jump regardless of prev_success=False."""
    params: dict = {"condition": "always", "target_hexastring": "abcd", "_prev_success": False}
    JumpToStepExecutor().execute_logical(None, params)  # type: ignore[arg-type]
    assert params.get("_pending_jump") == "abcd"


def test_no_jump_when_target_is_empty() -> None:
    """An empty target must never produce a _pending_jump entry."""
    params: dict = {"condition": "always", "target_hexastring": "", "_prev_success": True}
    JumpToStepExecutor().execute_logical(None, params)  # type: ignore[arg-type]
    assert "_pending_jump" not in params


def test_default_prev_success_is_true() -> None:
    """Absent _prev_success key defaults to True (success path)."""
    params: dict = {"condition": "success", "target_hexastring": "abcd"}
    JumpToStepExecutor().execute_logical(None, params)  # type: ignore[arg-type]
    assert params.get("_pending_jump") == "abcd"


# ---------------------------------------------------------------------------
# validate_model
# ---------------------------------------------------------------------------


def test_validate_valid_step_returns_no_errors() -> None:
    """A valid JUMP_TO_STEP pointing to an existing step must have no errors."""
    target = _make_step("abcd")
    source = _make_step("efgh", StepTypeEnum.E_JUMP_TO_STEP)
    source.params = {"condition": "success", "target_hexastring": "abcd"}
    source.parent_context = [source, target]
    errors = JumpToStepExecutor().validate_model(source, 0)
    assert errors == []


def test_validate_invalid_condition_returns_error() -> None:
    """An unrecognised condition value must produce a validation error."""
    target = _make_step("abcd")
    source = _make_step("efgh", StepTypeEnum.E_JUMP_TO_STEP)
    source.params = {"condition": "bad_cond", "target_hexastring": "abcd"}
    source.parent_context = [source, target]
    errors = JumpToStepExecutor().validate_model(source, 0)
    assert any("condition" in e for e in errors)


def test_validate_missing_target_returns_error() -> None:
    """An empty target_hexastring must produce a validation error."""
    source = _make_step("efgh", StepTypeEnum.E_JUMP_TO_STEP)
    source.params = {"condition": "success", "target_hexastring": ""}
    source.parent_context = [source]
    errors = JumpToStepExecutor().validate_model(source, 0)
    assert errors


def test_validate_self_referencing_jump_returns_error() -> None:
    """A step pointing to itself must produce a validation error."""
    source = _make_step("efgh", StepTypeEnum.E_JUMP_TO_STEP)
    source.params = {"condition": "success", "target_hexastring": "efgh"}
    source.parent_context = [source]
    errors = JumpToStepExecutor().validate_model(source, 0)
    assert any("elle-même" in e for e in errors)


def test_validate_target_not_found_returns_error() -> None:
    """A target_hexastring absent from parent_context must be flagged."""
    source = _make_step("efgh", StepTypeEnum.E_JUMP_TO_STEP)
    source.params = {"condition": "success", "target_hexastring": "zzzz"}
    source.parent_context = [source]
    errors = JumpToStepExecutor().validate_model(source, 0)
    assert any("introuvable" in e for e in errors)


def test_validate_step_index_appears_in_error_messages() -> None:
    """Error messages must include the 1-based step index, zero-padded."""
    source = _make_step("efgh", StepTypeEnum.E_JUMP_TO_STEP)
    source.params = {"condition": "success", "target_hexastring": ""}
    source.parent_context = [source]
    # Step at index 2 → displayed as "03."
    errors = JumpToStepExecutor().validate_model(source, 2)
    assert any("03" in e for e in errors)
