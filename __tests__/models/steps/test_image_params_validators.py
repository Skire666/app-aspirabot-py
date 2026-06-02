"""Validator tests for image-dimension step params.

Covers WaitHtmlImagesParams, CountHtmlImagesParams and DownloadImageParams.
All validators gate on context — without context, any value is accepted.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

_CTX = {"step_index": 0}


def _v(cls: type, data: dict, ctx: dict | None = _CTX):
    return cls.model_validate(data, context=ctx)


# ---------------------------------------------------------------------------
# WaitHtmlImagesParams
# ---------------------------------------------------------------------------


class TestWaitHtmlImagesParams:
    from models.steps.wait_html_images_params import WaitHtmlImagesParams

    _BASE = {
        "height_min": 0, "height_max": 9999,
        "width_min": 0, "width_max": 9999,
        "operator": "equal", "quantity": 1,
        "retry_delay": 1, "retry_unit": "s", "retry_max": 5,
        "comment": "",
    }

    def test_valid_base_passes(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams
        p = _v(WaitHtmlImagesParams, self._BASE)
        assert p.height_min == 0
        assert p.operator == "equal"

    def test_negative_height_min_raises(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(WaitHtmlImagesParams, {**self._BASE, "height_min": -1})

    def test_negative_height_max_raises(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(WaitHtmlImagesParams, {**self._BASE, "height_max": -1})

    def test_negative_width_min_raises(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(WaitHtmlImagesParams, {**self._BASE, "width_min": -1})

    def test_negative_width_max_raises(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(WaitHtmlImagesParams, {**self._BASE, "width_max": -1})

    def test_invalid_operator_raises(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(WaitHtmlImagesParams, {**self._BASE, "operator": ">="})

    def test_all_valid_operators(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams
        for op in ("equal", "not_equal", "greater_than", "less_than", "greater_or_equal", "less_or_equal"):
            p = _v(WaitHtmlImagesParams, {**self._BASE, "operator": op})
            assert p.operator == op

    def test_negative_quantity_raises(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(WaitHtmlImagesParams, {**self._BASE, "quantity": -1})

    def test_zero_retry_delay_raises(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(WaitHtmlImagesParams, {**self._BASE, "retry_delay": 0})

    def test_negative_retry_delay_raises(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(WaitHtmlImagesParams, {**self._BASE, "retry_delay": -1})

    def test_invalid_retry_unit_raises(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(WaitHtmlImagesParams, {**self._BASE, "retry_unit": "hours"})

    def test_valid_retry_units(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams
        for unit in ("m", "s", "ms"):
            p = _v(WaitHtmlImagesParams, {**self._BASE, "retry_unit": unit})
            assert p.retry_unit == unit

    def test_zero_retry_max_raises(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(WaitHtmlImagesParams, {**self._BASE, "retry_max": 0})

    def test_height_min_greater_than_max_raises(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(WaitHtmlImagesParams, {**self._BASE, "height_min": 500, "height_max": 100})

    def test_width_min_greater_than_max_raises(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(WaitHtmlImagesParams, {**self._BASE, "width_min": 500, "width_max": 100})

    def test_height_min_equal_max_valid(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams
        p = _v(WaitHtmlImagesParams, {**self._BASE, "height_min": 100, "height_max": 100})
        assert p.height_min == 100

    def test_no_context_accepts_anything(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams
        p = WaitHtmlImagesParams(
            height_min=-1, height_max=-2, width_min=-1, width_max=-2,
            operator=">=", quantity=-1, retry_delay=-1, retry_unit="bad", retry_max=-1,
        )
        assert p.height_min == -1

    def test_to_dict_round_trip(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams
        p = WaitHtmlImagesParams(**self._BASE)
        d = p.to_dict()
        p2 = WaitHtmlImagesParams(**d)
        assert p2 == p


# ---------------------------------------------------------------------------
# CountHtmlImagesParams
# ---------------------------------------------------------------------------


class TestCountHtmlImagesParams:
    _BASE = {
        "width_min": 0, "width_max": 9999,
        "height_min": 0, "height_max": 9999,
        "success_if": "success", "operator": "equal", "value": 0,
        "comment": "",
    }

    def test_valid_passes(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams
        p = _v(CountHtmlImagesParams, self._BASE)
        assert p.success_if == "success"

    def test_negative_height_min_raises(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(CountHtmlImagesParams, {**self._BASE, "height_min": -1})

    def test_negative_width_min_raises(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(CountHtmlImagesParams, {**self._BASE, "width_min": -1})

    def test_negative_height_max_raises(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(CountHtmlImagesParams, {**self._BASE, "height_max": -1})

    def test_zero_height_max_raises(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(CountHtmlImagesParams, {**self._BASE, "height_max": 0})

    def test_negative_width_max_raises(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(CountHtmlImagesParams, {**self._BASE, "width_max": -1})

    def test_zero_width_max_raises(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(CountHtmlImagesParams, {**self._BASE, "width_max": 0})

    def test_negative_value_raises(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(CountHtmlImagesParams, {**self._BASE, "value": -1})

    def test_invalid_success_if_raises(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(CountHtmlImagesParams, {**self._BASE, "success_if": "maybe"})

    def test_failure_success_if_valid(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams
        p = _v(CountHtmlImagesParams, {**self._BASE, "success_if": "failure"})
        assert p.success_if == "failure"

    def test_invalid_operator_raises(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(CountHtmlImagesParams, {**self._BASE, "operator": ">="})

    def test_all_valid_operators(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams
        for op in ("equal", "not_equal", "greater_than", "less_than", "greater_or_equal", "less_or_equal"):
            p = _v(CountHtmlImagesParams, {**self._BASE, "operator": op})
            assert p.operator == op

    def test_height_range_invalid_raises(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(CountHtmlImagesParams, {**self._BASE, "height_min": 500, "height_max": 100})

    def test_width_range_invalid_raises(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams
        with pytest.raises(ValidationError):
            _v(CountHtmlImagesParams, {**self._BASE, "width_min": 500, "width_max": 100})

    def test_equal_min_max_valid(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams
        p = _v(CountHtmlImagesParams, {**self._BASE, "height_min": 100, "height_max": 100})
        assert p.height_min == 100

    def test_no_context_accepts_anything(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams
        p = CountHtmlImagesParams(
            width_min=-1, width_max=-1, height_min=-1, height_max=-1,
            success_if="bad", operator=">=", value=-1, comment=""
        )
        assert p.value == -1


# ---------------------------------------------------------------------------
# DownloadImageParams
# ---------------------------------------------------------------------------


class TestDownloadImageParams:
    _BASE = {
        "mode": "first",
        "unique_only": True,
        "width_min": 0, "width_max": 9999,
        "height_min": 0, "height_max": 9999,
        "comment": "",
    }

    def test_valid_passes(self) -> None:
        from models.steps.download_image_params import DownloadImageParams
        p = _v(DownloadImageParams, self._BASE)
        assert p.mode == "first"

    def test_to_dict_preserves_key_order(self) -> None:
        from models.steps.download_image_params import DownloadImageParams
        p = DownloadImageParams(**self._BASE)
        d = p.to_dict()
        keys = list(d.keys())
        assert keys[0] == "mode"
        assert "height_min" in keys
        assert "width_min" in keys

    def test_negative_height_min_raises(self) -> None:
        from models.steps.download_image_params import DownloadImageParams
        with pytest.raises(ValidationError):
            _v(DownloadImageParams, {**self._BASE, "height_min": -1})

    def test_negative_width_min_raises(self) -> None:
        from models.steps.download_image_params import DownloadImageParams
        with pytest.raises(ValidationError):
            _v(DownloadImageParams, {**self._BASE, "width_min": -1})

    def test_negative_height_max_raises(self) -> None:
        from models.steps.download_image_params import DownloadImageParams
        with pytest.raises(ValidationError):
            _v(DownloadImageParams, {**self._BASE, "height_max": -1})

    def test_zero_height_max_raises(self) -> None:
        from models.steps.download_image_params import DownloadImageParams
        with pytest.raises(ValidationError):
            _v(DownloadImageParams, {**self._BASE, "height_max": 0})

    def test_negative_width_max_raises(self) -> None:
        from models.steps.download_image_params import DownloadImageParams
        with pytest.raises(ValidationError):
            _v(DownloadImageParams, {**self._BASE, "width_max": -1})

    def test_zero_width_max_raises(self) -> None:
        from models.steps.download_image_params import DownloadImageParams
        with pytest.raises(ValidationError):
            _v(DownloadImageParams, {**self._BASE, "width_max": 0})

    def test_height_range_invalid_raises(self) -> None:
        from models.steps.download_image_params import DownloadImageParams
        with pytest.raises(ValidationError):
            _v(DownloadImageParams, {**self._BASE, "height_min": 500, "height_max": 100})

    def test_width_range_invalid_raises(self) -> None:
        from models.steps.download_image_params import DownloadImageParams
        with pytest.raises(ValidationError):
            _v(DownloadImageParams, {**self._BASE, "width_min": 500, "width_max": 100})

    def test_equal_range_valid(self) -> None:
        from models.steps.download_image_params import DownloadImageParams
        p = _v(DownloadImageParams, {**self._BASE, "height_min": 100, "height_max": 100})
        assert p.height_min == 100

    def test_no_context_accepts_anything(self) -> None:
        from models.steps.download_image_params import DownloadImageParams
        p = DownloadImageParams(mode="x", unique_only=False, width_min=-1, width_max=-1,
                                height_min=-1, height_max=-1, comment="")
        assert p.width_min == -1


# ---------------------------------------------------------------------------
# JumpToStepParams
# ---------------------------------------------------------------------------


class TestJumpToStepParams:
    _BASE = {"condition": "always", "target_hexastring": "abcd", "comment": ""}

    def test_valid_passes(self) -> None:
        from models.steps.jump_to_step_params import JumpToStepParams
        p = _v(JumpToStepParams, self._BASE)
        assert p.condition == "always"

    def test_all_valid_conditions(self) -> None:
        from models.steps.jump_to_step_params import JumpToStepParams
        for cond in ("always", "success", "failure"):
            p = _v(JumpToStepParams, {**self._BASE, "condition": cond})
            assert p.condition == cond

    def test_invalid_condition_raises(self) -> None:
        from models.steps.jump_to_step_params import JumpToStepParams
        with pytest.raises(ValidationError):
            _v(JumpToStepParams, {**self._BASE, "condition": "never"})

    def test_empty_target_raises(self) -> None:
        from models.steps.jump_to_step_params import JumpToStepParams
        with pytest.raises(ValidationError):
            _v(JumpToStepParams, {**self._BASE, "target_hexastring": ""})

    def test_self_reference_raises(self) -> None:
        from models.steps.jump_to_step_params import JumpToStepParams
        ctx = {"step_index": 0, "step_id": "abcd"}
        with pytest.raises(ValidationError):
            JumpToStepParams.model_validate(
                {**self._BASE, "target_hexastring": "abcd"},
                context=ctx,
            )

    def test_target_not_self_with_steps_context_none(self) -> None:
        from models.steps.jump_to_step_params import JumpToStepParams
        ctx = {"step_index": 0, "step_id": "other_id", "steps_context": None}
        p = JumpToStepParams.model_validate(self._BASE, context=ctx)
        assert p.target_hexastring == "abcd"

    def test_empty_target_skips_cross_step_check(self) -> None:
        from models.steps.jump_to_step_params import JumpToStepParams
        # empty target returns early in cross-step, then field validator catches it
        with pytest.raises(ValidationError):
            _v(JumpToStepParams, {**self._BASE, "target_hexastring": ""})

    def test_no_context_accepts_any_values(self) -> None:
        from models.steps.jump_to_step_params import JumpToStepParams
        p = JumpToStepParams(condition="never", target_hexastring="", comment="")
        assert p.condition == "never"

    def test_target_not_found_in_steps_context_raises(self) -> None:
        from models.steps.jump_to_step_params import JumpToStepParams
        mock_ctx = MagicMock()
        mock_ctx.find_by_id.return_value = None
        ctx = {"step_index": 0, "step_id": "other", "steps_context": mock_ctx}
        with pytest.raises(ValidationError):
            JumpToStepParams.model_validate(self._BASE, context=ctx)

    def test_target_found_in_steps_context_passes(self) -> None:
        from models.steps.jump_to_step_params import JumpToStepParams
        mock_ctx = MagicMock()
        mock_ctx.find_by_id.return_value = object()  # non-None = found
        ctx = {"step_index": 0, "step_id": "other", "steps_context": mock_ctx}
        p = JumpToStepParams.model_validate(self._BASE, context=ctx)
        assert p.target_hexastring == "abcd"


from unittest.mock import MagicMock  # noqa: E402 (placed after tests for readability)
