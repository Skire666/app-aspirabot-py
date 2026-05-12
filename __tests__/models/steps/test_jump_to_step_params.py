"""Unit tests for JumpToStepParams."""

from __future__ import annotations

import pytest

from models.step_scraping_model import StepType
from models.steps.jump_to_step_params import JumpToStepParams


def test_default_returns_expected_values() -> None:
    """default() should produce condition='success', empty target, empty comment."""
    p = JumpToStepParams.default()
    assert p.condition == "success"
    assert p.target_hexastring == ""
    assert p.comment == ""


def test_get_step_type_returns_jump_to_step() -> None:
    """get_step_type() must return StepType.JUMP_TO_STEP."""
    assert JumpToStepParams.get_step_type() == StepType.JUMP_TO_STEP


def test_to_dict_serializes_all_fields() -> None:
    """to_dict() must include condition, target_hexastring and comment."""
    p = JumpToStepParams(condition="always", target_hexastring="abcd", comment="note")
    d = p.to_dict()
    assert d == {"condition": "always", "target_hexastring": "abcd", "comment": "note"}


def test_from_dict_deserializes_correctly() -> None:
    """from_dict() must read all three fields from the dict."""
    data = {"condition": "failure", "target_hexastring": "1234", "comment": "test"}
    p = JumpToStepParams.from_dict(data)
    assert p.condition == "failure"
    assert p.target_hexastring == "1234"
    assert p.comment == "test"


def test_from_dict_uses_defaults_for_missing_keys() -> None:
    """from_dict() must fall back to safe defaults when keys are absent."""
    p = JumpToStepParams.from_dict({})
    assert p.condition == "success"
    assert p.target_hexastring == ""
    assert p.comment == ""


def test_from_dict_handles_none_target_hexastring() -> None:
    """from_dict() must coerce None target_hexastring to an empty string."""
    p = JumpToStepParams.from_dict({"target_hexastring": None})
    assert p.target_hexastring == ""


def test_from_dict_target_int_is_coerced_to_str() -> None:
    """from_dict() must convert non-string target_hexastring to str."""
    p = JumpToStepParams.from_dict({"target_hexastring": 1234})
    assert p.target_hexastring == "1234"


def test_roundtrip_to_dict_from_dict() -> None:
    """Serialization followed by deserialization must be lossless."""
    original = JumpToStepParams(condition="always", target_hexastring="ef01", comment="c")
    restored = JumpToStepParams.from_dict(original.to_dict())
    assert restored == original


def test_frozen_dataclass_raises_on_mutation() -> None:
    """JumpToStepParams is frozen: attribute assignment must raise."""
    p = JumpToStepParams.default()
    with pytest.raises(Exception):
        p.condition = "always"  # type: ignore[misc]


def test_from_dict_all_condition_values() -> None:
    """from_dict() must accept all three valid condition strings."""
    for cond in ("success", "failure", "always"):
        p = JumpToStepParams.from_dict({"condition": cond})
        assert p.condition == cond
