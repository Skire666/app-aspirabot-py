"""Tests for concrete step parameter models.

Each model is Pydantic-frozen. Validators fire only when a ``context`` dict is
supplied — construction without context never raises (safe for deserialization).
"""

from __future__ import annotations

import pytest
from models.steps.open_url_params import OpenUrlParams
from models.steps.section_params import SectionParams
from models.steps.wait_fixed_time_params import WaitFixedTimeParams
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# SectionParams
# ---------------------------------------------------------------------------


class TestSectionParams:
    def test_construction_without_context(self) -> None:
        p = SectionParams(title="My Section", comment="some comment")
        assert p.title == "My Section"

    def test_empty_title_without_context_allowed(self) -> None:
        p = SectionParams(title="", comment="")
        assert p.title == ""

    def test_to_dict(self) -> None:
        p = SectionParams(title="Sec A", comment="")
        d = p.to_dict()
        assert d["title"] == "Sec A"

    def test_with_context_rejects_empty_title(self) -> None:
        with pytest.raises(ValidationError):
            SectionParams.model_validate({"title": "", "comment": ""}, context={"step_index": 0})

    def test_with_context_rejects_whitespace_title(self) -> None:
        with pytest.raises(ValidationError):
            SectionParams.model_validate({"title": "   ", "comment": ""}, context={"step_index": 0})

    def test_with_context_accepts_valid_title(self) -> None:
        p = SectionParams.model_validate({"title": "Valid Title", "comment": ""}, context={"step_index": 2})
        assert p.title == "Valid Title"

    def test_frozen_rejects_mutation(self) -> None:
        p = SectionParams(title="X", comment="")
        with pytest.raises((ValidationError, TypeError)):
            p.title = "Y"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# WaitFixedTimeParams
# ---------------------------------------------------------------------------


class TestWaitFixedTimeParams:
    def test_construction_without_context(self) -> None:
        p = WaitFixedTimeParams(duration=5, unit="s")
        assert p.duration == 5
        assert p.unit == "s"

    def test_negative_duration_without_context_allowed(self) -> None:
        p = WaitFixedTimeParams(duration=-1, unit="s")
        assert p.duration == -1

    def test_with_context_rejects_negative_duration(self) -> None:
        with pytest.raises(ValidationError):
            WaitFixedTimeParams.model_validate({"duration": -1, "unit": "s"}, context={"step_index": 0})

    def test_with_context_zero_duration_allowed(self) -> None:
        p = WaitFixedTimeParams.model_validate({"duration": 0, "unit": "s"}, context={"step_index": 0})
        assert p.duration == 0

    def test_to_dict(self) -> None:
        p = WaitFixedTimeParams(duration=10, unit="ms")
        d = p.to_dict()
        assert d["duration"] == 10
        assert d["unit"] == "ms"


# ---------------------------------------------------------------------------
# OpenUrlParams
# ---------------------------------------------------------------------------


class TestOpenUrlParams:
    _BASE = {"wait_until": "load", "wait_dns_solver": 5, "timeout_duration": 30, "timeout_unit": "s", "comment": ""}

    def test_to_dict_round_trip(self) -> None:
        p = OpenUrlParams(**self._BASE)
        d = p.to_dict()
        p2 = OpenUrlParams(**d)
        assert p2 == p

    def test_with_context_accepts_valid_data(self) -> None:
        p = OpenUrlParams.model_validate(self._BASE, context={"step_index": 0})
        assert p.timeout_duration == 30

    def test_with_context_rejects_zero_dns_solver(self) -> None:
        data = {**self._BASE, "wait_dns_solver": 0}
        with pytest.raises(ValidationError):
            OpenUrlParams.model_validate(data, context={"step_index": 0})

    def test_with_context_rejects_too_large_dns_solver(self) -> None:
        data = {**self._BASE, "wait_dns_solver": 31}
        with pytest.raises(ValidationError):
            OpenUrlParams.model_validate(data, context={"step_index": 0})

    def test_with_context_rejects_zero_timeout(self) -> None:
        data = {**self._BASE, "timeout_duration": 0}
        with pytest.raises(ValidationError):
            OpenUrlParams.model_validate(data, context={"step_index": 0})

    def test_with_context_rejects_invalid_timeout_unit(self) -> None:
        data = {**self._BASE, "timeout_unit": "hours"}
        with pytest.raises(ValidationError):
            OpenUrlParams.model_validate(data, context={"step_index": 0})
