"""Tests for step parameter validators (context-dependent validation)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from models.steps.check_url_page_params import CheckUrlPageParams
from models.steps.click_for_download_params import ClickForDownloadParams
from models.steps.click_on_element_params import ClickOnElementParams
from models.steps.close_tabs_params import CloseTabsParams
from models.steps.count_html_elements_params import CountHtmlElementsParams
from models.steps.count_html_images_params import CountHtmlImagesParams
from models.steps.download_image_params import DownloadImageParams
from models.steps.export_data_to_js_params import ExportDataToJsParams
from models.steps.extract_variable_params import ExtractVariableParams
from models.steps.jump_to_step_params import JumpToStepParams
from models.steps.kill_browser_params import KillBrowserParams
from models.steps.refresh_page_params import RefreshPageParams
from models.steps.restart_to_beginning_params import RestartToBeginningParams
from models.steps.scroll_down_params import ScrollDownParams
from models.steps.wait_html_elements_params import WaitHtmlElementsParams
from models.steps.wait_html_images_params import WaitHtmlImagesParams
from models.steps.wait_page_state_params import WaitPageStateParams
from models.steps.wait_user_action_params import WaitUserActionParams


_CTX = {"step_index": 0, "step_id": "abc"}


def _make_steps_context(**kwargs) -> MagicMock:
    ctx = MagicMock()
    ctx.find_by_id.return_value = MagicMock()
    ctx.count_mapping_key.return_value = 1
    return ctx


# ---------------------------------------------------------------------------
# CheckUrlPageParams
# ---------------------------------------------------------------------------


class TestCheckUrlPageParams:
    def test_construction_without_context(self) -> None:
        p = CheckUrlPageParams(check_domain=True, check_path=False)
        assert p.check_domain is True

    def test_to_dict(self) -> None:
        p = CheckUrlPageParams(check_domain=True, check_path=True)
        d = p.to_dict()
        assert d["check_domain"] is True

    def test_with_context_raises_when_nothing_checked(self) -> None:
        with pytest.raises(ValidationError):
            CheckUrlPageParams.model_validate(
                {"check_domain": False, "check_path": False}, context=_CTX
            )

    def test_with_context_passes_when_at_least_one(self) -> None:
        p = CheckUrlPageParams.model_validate(
            {"check_domain": True, "check_path": False}, context=_CTX
        )
        assert p.check_domain is True

    def test_validate_with_context_no_errors(self) -> None:
        p = CheckUrlPageParams(check_domain=True, check_path=False)
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert errors == []

    def test_validate_with_context_returns_errors(self) -> None:
        p = CheckUrlPageParams(check_domain=False, check_path=False)
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert len(errors) >= 1


# ---------------------------------------------------------------------------
# ClickOnElementParams
# ---------------------------------------------------------------------------


class TestClickOnElementParams:
    def test_construction_without_context(self) -> None:
        p = ClickOnElementParams(selector=".btn", click_mode="single")
        assert p.selector == ".btn"

    def test_to_dict(self) -> None:
        p = ClickOnElementParams(selector=".btn", click_mode="single")
        d = p.to_dict()
        assert d["selector"] == ".btn"

    def test_with_context_empty_selector_raises(self) -> None:
        with pytest.raises(ValidationError):
            ClickOnElementParams.model_validate(
                {"selector": "", "click_mode": "single", "index_clicked": 0}, context=_CTX
            )

    def test_with_context_negative_index_raises(self) -> None:
        with pytest.raises(ValidationError):
            ClickOnElementParams.model_validate(
                {"selector": ".btn", "click_mode": "single", "index_clicked": -1}, context=_CTX
            )

    def test_validate_with_context_no_errors(self) -> None:
        p = ClickOnElementParams(selector=".btn", click_mode="single", index_clicked=0)
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert errors == []


# ---------------------------------------------------------------------------
# CloseTabsParams
# ---------------------------------------------------------------------------


class TestCloseTabsParams:
    def test_construction_without_context(self) -> None:
        p = CloseTabsParams(filter_mode="all", filter_custom="", max_tabs=5)
        assert p.max_tabs == 5

    def test_to_dict(self) -> None:
        p = CloseTabsParams(filter_mode="all", filter_custom="", max_tabs=5)
        d = p.to_dict()
        assert d["max_tabs"] == 5

    def test_with_context_zero_max_tabs_raises(self) -> None:
        with pytest.raises(ValidationError):
            CloseTabsParams.model_validate(
                {"filter_mode": "all", "filter_custom": "", "max_tabs": 0}, context=_CTX
            )

    def test_with_context_custom_mode_no_filter_raises(self) -> None:
        from shared.enums import FilterClosedEnum
        with pytest.raises(ValidationError):
            CloseTabsParams.model_validate(
                {"filter_mode": FilterClosedEnum.E_CUSTOM.value, "filter_custom": "", "max_tabs": 1}, context=_CTX
            )

    def test_validate_with_context_no_errors(self) -> None:
        p = CloseTabsParams(filter_mode="all", filter_custom="", max_tabs=5)
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert errors == []


# ---------------------------------------------------------------------------
# CountHtmlElementsParams
# ---------------------------------------------------------------------------


class TestCountHtmlElementsParams:
    def test_construction_without_context(self) -> None:
        p = CountHtmlElementsParams(selector=".el", success_if="success", operator="equal", value=1)
        assert p.value == 1

    def test_to_dict(self) -> None:
        p = CountHtmlElementsParams(selector=".el", success_if="success", operator="equal", value=1)
        d = p.to_dict()
        assert d["operator"] == "equal"

    def test_with_context_empty_selector_raises(self) -> None:
        with pytest.raises(ValidationError):
            CountHtmlElementsParams.model_validate(
                {"selector": "", "success_if": "success", "operator": "equal", "value": 1, "comment": "note"},
                context=_CTX
            )

    def test_with_context_negative_value_raises(self) -> None:
        with pytest.raises(ValidationError):
            CountHtmlElementsParams.model_validate(
                {"selector": ".el", "success_if": "success", "operator": "equal", "value": -1, "comment": "note"},
                context=_CTX
            )

    def test_with_context_invalid_success_if_raises(self) -> None:
        with pytest.raises(ValidationError):
            CountHtmlElementsParams.model_validate(
                {"selector": ".el", "success_if": "invalid", "operator": "equal", "value": 1, "comment": "note"},
                context=_CTX
            )

    def test_with_context_invalid_operator_raises(self) -> None:
        with pytest.raises(ValidationError):
            CountHtmlElementsParams.model_validate(
                {"selector": ".el", "success_if": "success", "operator": "bad_op", "value": 1, "comment": "note"},
                context=_CTX
            )

    def test_with_context_empty_comment_raises(self) -> None:
        with pytest.raises(ValidationError):
            CountHtmlElementsParams.model_validate(
                {"selector": ".el", "success_if": "success", "operator": "equal", "value": 1, "comment": ""},
                context=_CTX
            )

    def test_validate_with_context_returns_errors(self) -> None:
        p = CountHtmlElementsParams(selector="", success_if="success", operator="equal", value=1, comment="")
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert len(errors) >= 1


# ---------------------------------------------------------------------------
# DownloadImageParams
# ---------------------------------------------------------------------------


class TestDownloadImageParams:
    _BASE = {"mode": "all", "unique_only": True, "width_min": 0, "width_max": 100, "height_min": 0, "height_max": 100}

    def test_construction_without_context(self) -> None:
        p = DownloadImageParams(**self._BASE)
        assert p.width_max == 100

    def test_to_dict(self) -> None:
        p = DownloadImageParams(**self._BASE)
        d = p.to_dict()
        assert d["width_max"] == 100

    def test_negative_height_min_raises(self) -> None:
        data = {**self._BASE, "height_min": -1}
        with pytest.raises(ValidationError):
            DownloadImageParams.model_validate(data, context=_CTX)

    def test_height_min_exceeds_max_raises(self) -> None:
        data = {**self._BASE, "height_min": 200, "height_max": 100}
        with pytest.raises(ValidationError):
            DownloadImageParams.model_validate(data, context=_CTX)

    def test_width_min_exceeds_max_raises(self) -> None:
        data = {**self._BASE, "width_min": 200, "width_max": 100}
        with pytest.raises(ValidationError):
            DownloadImageParams.model_validate(data, context=_CTX)

    def test_validate_with_context_no_errors(self) -> None:
        p = DownloadImageParams(**self._BASE)
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert errors == []


# ---------------------------------------------------------------------------
# ExtractVariableParams
# ---------------------------------------------------------------------------


class TestExtractVariableParams:
    def test_construction_without_context(self) -> None:
        p = ExtractVariableParams(variable="datetime_now", mapping="key1")
        assert p.variable == "datetime_now"

    def test_to_dict(self) -> None:
        p = ExtractVariableParams(variable="datetime_now", mapping="key1")
        d = p.to_dict()
        assert d["variable"] == "datetime_now"

    def test_invalid_variable_raises(self) -> None:
        with pytest.raises(ValidationError):
            ExtractVariableParams.model_validate(
                {"variable": "invalid_var", "mapping": "key1"}, context=_CTX
            )

    def test_empty_mapping_raises(self) -> None:
        with pytest.raises(ValidationError):
            ExtractVariableParams.model_validate(
                {"variable": "datetime_now", "mapping": ""}, context=_CTX
            )

    def test_validate_with_context_no_errors(self) -> None:
        p = ExtractVariableParams(variable="datetime_now", mapping="key1")
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert errors == []


# ---------------------------------------------------------------------------
# JumpToStepParams
# ---------------------------------------------------------------------------


class TestJumpToStepParams:
    def test_construction_without_context(self) -> None:
        p = JumpToStepParams(condition="success", target_hexastring="abc123", comment="note")
        assert p.condition == "success"

    def test_to_dict(self) -> None:
        p = JumpToStepParams(condition="success", target_hexastring="abc123", comment="note")
        d = p.to_dict()
        assert d["condition"] == "success"

    def test_invalid_condition_raises(self) -> None:
        with pytest.raises(ValidationError):
            JumpToStepParams.model_validate(
                {"condition": "bad", "target_hexastring": "abc123", "comment": "note"}, context=_CTX
            )

    def test_empty_target_raises(self) -> None:
        with pytest.raises(ValidationError):
            JumpToStepParams.model_validate(
                {"condition": "success", "target_hexastring": "", "comment": "note"}, context=_CTX
            )

    def test_self_reference_raises(self) -> None:
        ctx = {**_CTX, "step_id": "self_id", "steps_context": _make_steps_context()}
        with pytest.raises(ValidationError):
            JumpToStepParams.model_validate(
                {"condition": "success", "target_hexastring": "self_id", "comment": "note"}, context=ctx
            )

    def test_target_not_found_raises(self) -> None:
        steps = _make_steps_context()
        steps.find_by_id.return_value = None
        ctx = {**_CTX, "step_id": "other_id", "steps_context": steps}
        with pytest.raises(ValidationError):
            JumpToStepParams.model_validate(
                {"condition": "success", "target_hexastring": "nonexistent", "comment": "note"}, context=ctx
            )

    def test_validate_with_context_no_errors(self) -> None:
        steps = _make_steps_context()
        p = JumpToStepParams(condition="success", target_hexastring="target123", comment="note")
        errors = p.validate_with_context(0, steps, "other_id")
        assert errors == []


# ---------------------------------------------------------------------------
# RestartToBeginningParams
# ---------------------------------------------------------------------------


class TestRestartToBeginningParams:
    def test_construction_without_context(self) -> None:
        p = RestartToBeginningParams(jump_only_if_urls_remaining=True)
        assert p.jump_only_if_urls_remaining is True

    def test_to_dict(self) -> None:
        p = RestartToBeginningParams(jump_only_if_urls_remaining=False)
        d = p.to_dict()
        assert d["jump_only_if_urls_remaining"] is False

    def test_comment_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            RestartToBeginningParams(jump_only_if_urls_remaining=True, comment="x" * 121)

    def test_comment_max_length_ok(self) -> None:
        p = RestartToBeginningParams(jump_only_if_urls_remaining=True, comment="x" * 120)
        assert len(p.comment) == 120

    def test_validate_with_context_no_errors(self) -> None:
        p = RestartToBeginningParams(jump_only_if_urls_remaining=True)
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert errors == []


# ---------------------------------------------------------------------------
# ScrollDownParams
# ---------------------------------------------------------------------------


class TestScrollDownParams:
    def test_construction_without_context(self) -> None:
        p = ScrollDownParams(pixels=100)
        assert p.pixels == 100

    def test_to_dict(self) -> None:
        p = ScrollDownParams(pixels=200, nbr_loops=3)
        d = p.to_dict()
        assert d["pixels"] == 200

    def test_with_context_zero_pixels_raises(self) -> None:
        with pytest.raises(ValidationError):
            ScrollDownParams.model_validate({"pixels": 0, "nbr_loops": 1, "delay_pause": 0}, context=_CTX)

    def test_with_context_nbr_loops_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            ScrollDownParams.model_validate({"pixels": 100, "nbr_loops": 0, "delay_pause": 0}, context=_CTX)

    def test_with_context_delay_pause_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            ScrollDownParams.model_validate({"pixels": 100, "nbr_loops": 1, "delay_pause": 100}, context=_CTX)

    def test_validate_with_context_no_errors(self) -> None:
        p = ScrollDownParams(pixels=100, nbr_loops=1, delay_pause=1)
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert errors == []


# ---------------------------------------------------------------------------
# WaitHtmlElementsParams
# ---------------------------------------------------------------------------


class TestWaitHtmlElementsParams:
    _BASE = {
        "selector": ".el",
        "operator": "equal",
        "quantity": 1,
        "retry_delay": 1,
        "retry_unit": "s",
        "retry_max": 3,
        "comment": "note",
    }

    def test_construction_without_context(self) -> None:
        p = WaitHtmlElementsParams(**self._BASE)
        assert p.selector == ".el"

    def test_to_dict(self) -> None:
        p = WaitHtmlElementsParams(**self._BASE)
        d = p.to_dict()
        assert d["selector"] == ".el"

    def test_empty_selector_raises(self) -> None:
        data = {**self._BASE, "selector": ""}
        with pytest.raises(ValidationError):
            WaitHtmlElementsParams.model_validate(data, context=_CTX)

    def test_invalid_operator_raises(self) -> None:
        data = {**self._BASE, "operator": "bad_op"}
        with pytest.raises(ValidationError):
            WaitHtmlElementsParams.model_validate(data, context=_CTX)

    def test_negative_quantity_raises(self) -> None:
        data = {**self._BASE, "quantity": -1}
        with pytest.raises(ValidationError):
            WaitHtmlElementsParams.model_validate(data, context=_CTX)

    def test_zero_retry_delay_raises(self) -> None:
        data = {**self._BASE, "retry_delay": 0}
        with pytest.raises(ValidationError):
            WaitHtmlElementsParams.model_validate(data, context=_CTX)

    def test_invalid_retry_unit_raises(self) -> None:
        data = {**self._BASE, "retry_unit": "hours"}
        with pytest.raises(ValidationError):
            WaitHtmlElementsParams.model_validate(data, context=_CTX)

    def test_zero_retry_max_raises(self) -> None:
        data = {**self._BASE, "retry_max": 0}
        with pytest.raises(ValidationError):
            WaitHtmlElementsParams.model_validate(data, context=_CTX)

    def test_empty_comment_raises(self) -> None:
        data = {**self._BASE, "comment": ""}
        with pytest.raises(ValidationError):
            WaitHtmlElementsParams.model_validate(data, context=_CTX)

    def test_validate_with_context_no_errors(self) -> None:
        p = WaitHtmlElementsParams(**self._BASE)
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert errors == []


# ---------------------------------------------------------------------------
# WaitPageStateParams
# ---------------------------------------------------------------------------


class TestWaitPageStateParams:
    _BASE = {"wait_until": "load", "timeout_duration": 30, "timeout_unit": "s", "comment": ""}

    def test_construction_without_context(self) -> None:
        from models.steps.wait_page_state_params import WaitPageStateParams
        p = WaitPageStateParams(**self._BASE)
        assert p.timeout_duration == 30

    def test_to_dict(self) -> None:
        from models.steps.wait_page_state_params import WaitPageStateParams
        p = WaitPageStateParams(**self._BASE)
        d = p.to_dict()
        assert d["timeout_duration"] == 30

    def test_with_context_zero_timeout_raises(self) -> None:
        from models.steps.wait_page_state_params import WaitPageStateParams
        data = {**self._BASE, "timeout_duration": 0}
        with pytest.raises(ValidationError):
            WaitPageStateParams.model_validate(data, context=_CTX)

    def test_with_context_invalid_unit_raises(self) -> None:
        from models.steps.wait_page_state_params import WaitPageStateParams
        data = {**self._BASE, "timeout_unit": "hours"}
        with pytest.raises(ValidationError):
            WaitPageStateParams.model_validate(data, context=_CTX)

    def test_validate_with_context_no_errors(self) -> None:
        from models.steps.wait_page_state_params import WaitPageStateParams
        p = WaitPageStateParams(**self._BASE)
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert errors == []


# ---------------------------------------------------------------------------
# WaitUserActionParams
# ---------------------------------------------------------------------------


class TestWaitUserActionParams:
    _BASE = {"condition": "always", "wait_duration": 1, "wait_unit": "s"}

    def test_construction_without_context(self) -> None:
        from models.steps.wait_user_action_params import WaitUserActionParams
        p = WaitUserActionParams(**self._BASE)
        assert p.condition == "always"

    def test_to_dict(self) -> None:
        from models.steps.wait_user_action_params import WaitUserActionParams
        p = WaitUserActionParams(**self._BASE)
        d = p.to_dict()
        assert d["condition"] == "always"

    def test_with_context_invalid_condition_raises(self) -> None:
        from models.steps.wait_user_action_params import WaitUserActionParams
        data = {**self._BASE, "condition": "never"}
        with pytest.raises(ValidationError):
            WaitUserActionParams.model_validate(data, context=_CTX)

    def test_with_context_zero_wait_duration_raises(self) -> None:
        from models.steps.wait_user_action_params import WaitUserActionParams
        data = {**self._BASE, "wait_duration": 0}
        with pytest.raises(ValidationError):
            WaitUserActionParams.model_validate(data, context=_CTX)

    def test_validate_with_context_no_errors(self) -> None:
        from models.steps.wait_user_action_params import WaitUserActionParams
        p = WaitUserActionParams(**self._BASE)
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert errors == []


# ---------------------------------------------------------------------------
# RefreshPageParams
# ---------------------------------------------------------------------------


class TestRefreshPageParams:
    _BASE = {"clear_cache": False, "wait_until": "load", "timeout_duration": 30, "timeout_unit": "s", "comment": ""}

    def test_construction_without_context(self) -> None:
        from models.steps.refresh_page_params import RefreshPageParams
        p = RefreshPageParams(**self._BASE)
        assert p.timeout_duration == 30

    def test_to_dict(self) -> None:
        from models.steps.refresh_page_params import RefreshPageParams
        p = RefreshPageParams(**self._BASE)
        d = p.to_dict()
        assert d["timeout_duration"] == 30

    def test_with_context_zero_timeout_raises(self) -> None:
        from models.steps.refresh_page_params import RefreshPageParams
        data = {**self._BASE, "timeout_duration": 0}
        with pytest.raises(ValidationError):
            RefreshPageParams.model_validate(data, context=_CTX)

    def test_with_context_invalid_unit_when_positive_duration_raises(self) -> None:
        from models.steps.refresh_page_params import RefreshPageParams
        data = {**self._BASE, "timeout_unit": "hours"}
        with pytest.raises(ValidationError):
            RefreshPageParams.model_validate(data, context=_CTX)

    def test_validate_with_context_no_errors(self) -> None:
        from models.steps.refresh_page_params import RefreshPageParams
        p = RefreshPageParams(**self._BASE)
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert errors == []


# ---------------------------------------------------------------------------
# KillBrowserParams
# ---------------------------------------------------------------------------


class TestKillBrowserParams:
    _BASE = {"wait_duration": 0, "wait_unit": "s"}

    def test_construction_without_context(self) -> None:
        from models.steps.kill_browser_params import KillBrowserParams
        p = KillBrowserParams(**self._BASE)
        assert p.wait_unit == "s"

    def test_to_dict(self) -> None:
        from models.steps.kill_browser_params import KillBrowserParams
        p = KillBrowserParams(**self._BASE)
        d = p.to_dict()
        assert d["wait_unit"] == "s"

    def test_with_context_negative_duration_raises(self) -> None:
        from models.steps.kill_browser_params import KillBrowserParams
        data = {**self._BASE, "wait_duration": -1}
        with pytest.raises(ValidationError):
            KillBrowserParams.model_validate(data, context=_CTX)

    def test_with_context_invalid_unit_raises(self) -> None:
        from models.steps.kill_browser_params import KillBrowserParams
        data = {**self._BASE, "wait_unit": "hours"}
        with pytest.raises(ValidationError):
            KillBrowserParams.model_validate(data, context=_CTX)

    def test_validate_with_context_no_errors(self) -> None:
        from models.steps.kill_browser_params import KillBrowserParams
        p = KillBrowserParams(**self._BASE)
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert errors == []


# ---------------------------------------------------------------------------
# ExportDataToJsParams
# ---------------------------------------------------------------------------


class TestExportDataToJsParams:
    def test_construction_without_context(self) -> None:
        from models.steps.export_data_to_js_params import ExportDataToJsParams
        p = ExportDataToJsParams(prefix_file="myfile")
        assert p.prefix_file == "myfile"

    def test_to_dict(self) -> None:
        from models.steps.export_data_to_js_params import ExportDataToJsParams
        p = ExportDataToJsParams(prefix_file="myfile")
        d = p.to_dict()
        assert d["prefix_file"] == "myfile"

    def test_with_context_empty_prefix_raises(self) -> None:
        from models.steps.export_data_to_js_params import ExportDataToJsParams
        with pytest.raises(ValidationError):
            ExportDataToJsParams.model_validate({"prefix_file": ""}, context=_CTX)

    def test_validate_with_context_no_errors(self) -> None:
        from models.steps.export_data_to_js_params import ExportDataToJsParams
        p = ExportDataToJsParams(prefix_file="myfile")
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert errors == []


# ---------------------------------------------------------------------------
# ClickForDownloadParams
# ---------------------------------------------------------------------------


class TestClickForDownloadParams:
    def test_construction_without_context(self) -> None:
        p = ClickForDownloadParams(selector=".dl", click_mode="single")
        assert p.selector == ".dl"

    def test_to_dict(self) -> None:
        p = ClickForDownloadParams(selector=".dl", click_mode="single")
        d = p.to_dict()
        assert d["selector"] == ".dl"

    def test_validate_with_context_no_errors(self) -> None:
        p = ClickForDownloadParams(selector=".dl", click_mode="single")
        steps = _make_steps_context()
        errors = p.validate_with_context(0, steps, "abc")
        assert errors == []
