"""Tests for CountHtmlImagesParams and WaitHtmlImagesParams validators."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from models.steps.count_html_images_params import CountHtmlImagesParams
from models.steps.wait_html_images_params import WaitHtmlImagesParams


_CTX = {"step_index": 0, "step_id": "abc"}


def _make_steps_context() -> MagicMock:
    ctx = MagicMock()
    ctx.find_by_id.return_value = MagicMock()
    ctx.count_mapping_key.return_value = 1
    return ctx


# ---------------------------------------------------------------------------
# CountHtmlImagesParams
# ---------------------------------------------------------------------------


class TestCountHtmlImagesParams:
    _BASE = {
        "width_min": 0,
        "width_max": 100,
        "height_min": 0,
        "height_max": 100,
        "success_if": "success",
        "operator": "equal",
        "value": 1,
        "comment": "",
    }

    def test_construction_without_context(self) -> None:
        p = CountHtmlImagesParams(**self._BASE)
        assert p.value == 1

    def test_to_dict(self) -> None:
        p = CountHtmlImagesParams(**self._BASE)
        d = p.to_dict()
        assert d["width_max"] == 100

    def test_negative_height_min_raises(self) -> None:
        data = {**self._BASE, "height_min": -1}
        with pytest.raises(ValidationError):
            CountHtmlImagesParams.model_validate(data, context=_CTX)

    def test_negative_height_max_raises(self) -> None:
        data = {**self._BASE, "height_max": -1}
        with pytest.raises(ValidationError):
            CountHtmlImagesParams.model_validate(data, context=_CTX)

    def test_height_max_zero_raises(self) -> None:
        data = {**self._BASE, "height_max": 0}
        with pytest.raises(ValidationError):
            CountHtmlImagesParams.model_validate(data, context=_CTX)

    def test_height_range_invalid_raises(self) -> None:
        data = {**self._BASE, "height_min": 200, "height_max": 100}
        with pytest.raises(ValidationError):
            CountHtmlImagesParams.model_validate(data, context=_CTX)

    def test_width_range_invalid_raises(self) -> None:
        data = {**self._BASE, "width_min": 200, "width_max": 100}
        with pytest.raises(ValidationError):
            CountHtmlImagesParams.model_validate(data, context=_CTX)

    def test_negative_value_raises(self) -> None:
        data = {**self._BASE, "value": -1}
        with pytest.raises(ValidationError):
            CountHtmlImagesParams.model_validate(data, context=_CTX)

    def test_invalid_success_if_raises(self) -> None:
        data = {**self._BASE, "success_if": "invalid"}
        with pytest.raises(ValidationError):
            CountHtmlImagesParams.model_validate(data, context=_CTX)

    def test_invalid_operator_raises(self) -> None:
        data = {**self._BASE, "operator": "bad_op"}
        with pytest.raises(ValidationError):
            CountHtmlImagesParams.model_validate(data, context=_CTX)

    def test_validate_with_context_no_errors(self) -> None:
        p = CountHtmlImagesParams(**self._BASE)
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert errors == []

    def test_validate_with_context_returns_errors(self) -> None:
        data = {**self._BASE, "value": -1}
        p = CountHtmlImagesParams(**data)
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert len(errors) >= 1


# ---------------------------------------------------------------------------
# WaitHtmlImagesParams
# ---------------------------------------------------------------------------


class TestWaitHtmlImagesParams:
    _BASE = {
        "height_min": 0,
        "height_max": 100,
        "width_min": 0,
        "width_max": 100,
        "operator": "equal",
        "quantity": 1,
        "retry_delay": 1,
        "retry_unit": "s",
        "retry_max": 3,
        "comment": "note",
    }

    def test_construction_without_context(self) -> None:
        p = WaitHtmlImagesParams(**self._BASE)
        assert p.quantity == 1

    def test_to_dict(self) -> None:
        p = WaitHtmlImagesParams(**self._BASE)
        d = p.to_dict()
        assert d["height_max"] == 100

    def test_negative_dimension_raises(self) -> None:
        data = {**self._BASE, "height_min": -1}
        with pytest.raises(ValidationError):
            WaitHtmlImagesParams.model_validate(data, context=_CTX)

    def test_height_range_invalid_raises(self) -> None:
        data = {**self._BASE, "height_min": 200, "height_max": 100}
        with pytest.raises(ValidationError):
            WaitHtmlImagesParams.model_validate(data, context=_CTX)

    def test_width_range_invalid_raises(self) -> None:
        data = {**self._BASE, "width_min": 200, "width_max": 100}
        with pytest.raises(ValidationError):
            WaitHtmlImagesParams.model_validate(data, context=_CTX)

    def test_invalid_operator_raises(self) -> None:
        data = {**self._BASE, "operator": "bad_op"}
        with pytest.raises(ValidationError):
            WaitHtmlImagesParams.model_validate(data, context=_CTX)

    def test_negative_quantity_raises(self) -> None:
        data = {**self._BASE, "quantity": -1}
        with pytest.raises(ValidationError):
            WaitHtmlImagesParams.model_validate(data, context=_CTX)

    def test_zero_retry_delay_raises(self) -> None:
        data = {**self._BASE, "retry_delay": 0}
        with pytest.raises(ValidationError):
            WaitHtmlImagesParams.model_validate(data, context=_CTX)

    def test_invalid_retry_unit_raises(self) -> None:
        data = {**self._BASE, "retry_unit": "hours"}
        with pytest.raises(ValidationError):
            WaitHtmlImagesParams.model_validate(data, context=_CTX)

    def test_zero_retry_max_raises(self) -> None:
        data = {**self._BASE, "retry_max": 0}
        with pytest.raises(ValidationError):
            WaitHtmlImagesParams.model_validate(data, context=_CTX)

    def test_empty_comment_raises(self) -> None:
        data = {**self._BASE, "comment": ""}
        with pytest.raises(ValidationError):
            WaitHtmlImagesParams.model_validate(data, context=_CTX)

    def test_validate_with_context_no_errors(self) -> None:
        p = WaitHtmlImagesParams(**self._BASE)
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert errors == []
