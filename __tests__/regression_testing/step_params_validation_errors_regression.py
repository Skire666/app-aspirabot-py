"""Regression tests — step params validation error branches.

Each step params model has @field_validator methods that only fire when a
validation context dict is supplied.  The error-raising branches are the
most likely paths to break during a refactor (renamed fields, changed rules).

These tests cover:
- Each validator's error branch (invalid value + context → ValidationError).
- Each validator's no-context branch (same invalid value, no context → accepted).

Only models with uncovered error branches (< 100% in regression runs) are
included here.  Happy-path round-trips are already covered by
step_params_serialization_regression.py.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

# Minimal context dict for single-step scenarios
_CTX = {"step_index": 0, "step_id": "aaa1", "steps_context": None}


# ===========================================================================
# SectionParams
# ===========================================================================


class TestSectionParamsValidation:
    def test_empty_title_with_context_raises(self) -> None:
        from models.steps.section_params import SectionParams

        with pytest.raises(ValidationError):
            SectionParams.model_validate({"title": "", "comment": ""}, context=_CTX)

    def test_blank_title_with_context_raises(self) -> None:
        from models.steps.section_params import SectionParams

        with pytest.raises(ValidationError):
            SectionParams.model_validate({"title": "   ", "comment": ""}, context=_CTX)

    def test_empty_title_no_context_accepted(self) -> None:
        from models.steps.section_params import SectionParams

        p = SectionParams(title="", comment="")
        assert p.title == ""


# ===========================================================================
# ClickForDownloadParams
# ===========================================================================


class TestClickForDownloadParamsValidation:
    def test_negative_index_with_context_raises(self) -> None:
        from models.steps.click_for_download_params import ClickForDownloadParams

        with pytest.raises(ValidationError):
            ClickForDownloadParams.model_validate(
                {"selector": ".btn", "click_mode": "left", "index_clicked": -1, "comment": ""}, context=_CTX
            )

    def test_empty_selector_with_context_raises(self) -> None:
        from models.steps.click_for_download_params import ClickForDownloadParams

        with pytest.raises(ValidationError):
            ClickForDownloadParams.model_validate(
                {"selector": "", "click_mode": "left", "index_clicked": 0, "comment": ""}, context=_CTX
            )

    def test_invalid_values_no_context_accepted(self) -> None:
        from models.steps.click_for_download_params import ClickForDownloadParams

        p = ClickForDownloadParams(selector="", click_mode="left", index_clicked=-1, comment="")
        assert p.index_clicked == -1
        assert p.selector == ""


# ===========================================================================
# ClickOnElementParams
# ===========================================================================


class TestClickOnElementParamsValidation:
    def test_negative_index_with_context_raises(self) -> None:
        from models.steps.click_on_element_params import ClickOnElementParams

        with pytest.raises(ValidationError):
            ClickOnElementParams.model_validate(
                {"selector": ".btn", "click_mode": "left", "index_clicked": -3, "comment": ""}, context=_CTX
            )

    def test_empty_selector_with_context_raises(self) -> None:
        from models.steps.click_on_element_params import ClickOnElementParams

        with pytest.raises(ValidationError):
            ClickOnElementParams.model_validate(
                {"selector": "  ", "click_mode": "left", "index_clicked": 0, "comment": ""}, context=_CTX
            )


# ===========================================================================
# CloseTabsParams
# ===========================================================================


class TestCloseTabsParamsValidation:
    def test_zero_max_tabs_with_context_raises(self) -> None:
        from models.steps.close_tabs_params import CloseTabsParams

        with pytest.raises(ValidationError):
            CloseTabsParams.model_validate(
                {"filter_mode": "all", "filter_custom": "", "max_tabs": 0, "comment": ""}, context=_CTX
            )

    def test_negative_max_tabs_with_context_raises(self) -> None:
        from models.steps.close_tabs_params import CloseTabsParams

        with pytest.raises(ValidationError):
            CloseTabsParams.model_validate(
                {"filter_mode": "all", "filter_custom": "", "max_tabs": -1, "comment": ""}, context=_CTX
            )

    def test_no_context_zero_max_tabs_accepted(self) -> None:
        from models.steps.close_tabs_params import CloseTabsParams

        p = CloseTabsParams(filter_mode="all", filter_custom="", max_tabs=0, comment="")
        assert p.max_tabs == 0


# ===========================================================================
# CountHtmlElementsParams
# ===========================================================================


class TestCountHtmlElementsParamsValidation:
    def test_empty_selector_with_context_raises(self) -> None:
        from models.steps.count_html_elements_params import CountHtmlElementsParams

        with pytest.raises(ValidationError):
            CountHtmlElementsParams.model_validate(
                {"selector": "", "success_if": "success", "operator": "equal", "value": 1, "comment": ""}, context=_CTX
            )

    def test_negative_value_with_context_raises(self) -> None:
        from models.steps.count_html_elements_params import CountHtmlElementsParams

        with pytest.raises(ValidationError):
            CountHtmlElementsParams.model_validate(
                {"selector": ".div", "success_if": "success", "operator": "equal", "value": -1, "comment": ""},
                context=_CTX,
            )

    def test_invalid_success_if_with_context_raises(self) -> None:
        from models.steps.count_html_elements_params import CountHtmlElementsParams

        with pytest.raises(ValidationError):
            CountHtmlElementsParams.model_validate(
                {"selector": ".x", "success_if": "maybe", "operator": "equal", "value": 0, "comment": ""}, context=_CTX
            )

    def test_invalid_operator_with_context_raises(self) -> None:
        from models.steps.count_html_elements_params import CountHtmlElementsParams

        with pytest.raises(ValidationError):
            CountHtmlElementsParams.model_validate(
                {"selector": ".x", "success_if": "success", "operator": "??", "value": 0, "comment": ""}, context=_CTX
            )


# ===========================================================================
# ExtractTextsParams
# ===========================================================================


class TestExtractTextsParamsValidation:
    def test_empty_selector_with_context_raises(self) -> None:
        from models.steps.extract_texts_params import ExtractTextsParams

        with pytest.raises(ValidationError):
            ExtractTextsParams.model_validate(
                {"selector": "", "extract_mode": "e_inner_text", "target": "e_first", "mapping": "key", "comment": ""},
                context=_CTX,
            )

    def test_invalid_extract_mode_with_context_raises(self) -> None:
        from models.steps.extract_texts_params import ExtractTextsParams

        with pytest.raises(ValidationError):
            ExtractTextsParams.model_validate(
                {"selector": ".x", "extract_mode": "bad_mode", "target": "e_first", "mapping": "key", "comment": ""},
                context=_CTX,
            )

    def test_invalid_target_with_context_raises(self) -> None:
        from models.steps.extract_texts_params import ExtractTextsParams

        with pytest.raises(ValidationError):
            ExtractTextsParams.model_validate(
                {
                    "selector": ".x",
                    "extract_mode": "e_inner_text",
                    "target": "bad_target",
                    "mapping": "key",
                    "comment": "",
                },
                context=_CTX,
            )

    def test_empty_mapping_with_context_raises(self) -> None:
        from models.steps.extract_texts_params import ExtractTextsParams

        with pytest.raises(ValidationError):
            ExtractTextsParams.model_validate(
                {"selector": ".x", "extract_mode": "e_inner_text", "target": "e_first", "mapping": "", "comment": ""},
                context=_CTX,
            )


# ===========================================================================
# ExtractLinksParams
# ===========================================================================


class TestExtractLinksParamsValidation:
    def test_empty_selector_with_context_raises(self) -> None:
        from models.steps.extract_links_params import ExtractLinksParams

        with pytest.raises(ValidationError):
            ExtractLinksParams.model_validate(
                {"selector": "", "target": "e_first", "mapping": "key", "comment": ""}, context=_CTX
            )

    def test_invalid_target_with_context_raises(self) -> None:
        from models.steps.extract_links_params import ExtractLinksParams

        with pytest.raises(ValidationError):
            ExtractLinksParams.model_validate(
                {"selector": ".a", "target": "wrong", "mapping": "key", "comment": ""}, context=_CTX
            )

    def test_empty_mapping_with_context_raises(self) -> None:
        from models.steps.extract_links_params import ExtractLinksParams

        with pytest.raises(ValidationError):
            ExtractLinksParams.model_validate(
                {"selector": ".a", "target": "e_first", "mapping": "", "comment": ""}, context=_CTX
            )


# ===========================================================================
# ExtractVariableParams
# ===========================================================================


class TestExtractVariableParamsValidation:
    def test_empty_variable_name_with_context_raises(self) -> None:
        from models.steps.extract_variable_params import ExtractVariableParams

        with pytest.raises(ValidationError):
            ExtractVariableParams.model_validate(
                {"variable_name": "", "script": "return 1", "comment": ""}, context=_CTX
            )

    def test_empty_script_with_context_raises(self) -> None:
        from models.steps.extract_variable_params import ExtractVariableParams

        with pytest.raises(ValidationError):
            ExtractVariableParams.model_validate({"variable_name": "myVar", "script": "", "comment": ""}, context=_CTX)


# ===========================================================================
# KillBrowserParams
# ===========================================================================


class TestKillBrowserParamsValidation:
    def test_negative_wait_duration_with_context_raises(self) -> None:
        from models.steps.kill_browser_params import KillBrowserParams

        with pytest.raises(ValidationError):
            KillBrowserParams.model_validate({"wait_duration": -1, "wait_unit": "s", "comment": ""}, context=_CTX)

    def test_invalid_wait_unit_with_context_raises(self) -> None:
        from models.steps.kill_browser_params import KillBrowserParams

        with pytest.raises(ValidationError):
            KillBrowserParams.model_validate({"wait_duration": 1, "wait_unit": "years", "comment": ""}, context=_CTX)

    def test_no_context_negative_duration_accepted(self) -> None:
        from models.steps.kill_browser_params import KillBrowserParams

        p = KillBrowserParams(wait_duration=-1, wait_unit="s", comment="")
        assert p.wait_duration == -1


# ===========================================================================
# OpenUrlParams
# ===========================================================================


class TestOpenUrlParamsValidation:
    def test_invalid_open_mode_with_context_raises(self) -> None:
        from models.steps.open_url_params import OpenUrlParams

        with pytest.raises(ValidationError):
            OpenUrlParams.model_validate({"url": "https://x.com", "open_mode": "bad_mode", "comment": ""}, context=_CTX)


# ===========================================================================
# RefreshPageParams
# ===========================================================================


class TestRefreshPageParamsValidation:
    def test_invalid_wait_until_with_context_raises(self) -> None:
        from models.steps.refresh_page_params import RefreshPageParams

        with pytest.raises(ValidationError):
            RefreshPageParams.model_validate(
                {
                    "clear_cache": False,
                    "wait_until": "bad_state",
                    "timeout_duration": 30,
                    "timeout_unit": "s",
                    "comment": "",
                },
                context=_CTX,
            )

    def test_negative_timeout_with_context_raises(self) -> None:
        from models.steps.refresh_page_params import RefreshPageParams

        with pytest.raises(ValidationError):
            RefreshPageParams.model_validate(
                {
                    "clear_cache": False,
                    "wait_until": "load",
                    "timeout_duration": -1,
                    "timeout_unit": "s",
                    "comment": "",
                },
                context=_CTX,
            )


# ===========================================================================
# WaitFixedTimeParams
# ===========================================================================


class TestWaitFixedTimeParamsValidation:
    def test_negative_duration_with_context_raises(self) -> None:
        from models.steps.wait_fixed_time_params import WaitFixedTimeParams

        with pytest.raises(ValidationError):
            WaitFixedTimeParams.model_validate({"duration": -1, "unit": "s", "comment": ""}, context=_CTX)

    def test_no_context_negative_duration_accepted(self) -> None:
        from models.steps.wait_fixed_time_params import WaitFixedTimeParams

        p = WaitFixedTimeParams(duration=-5, unit="s", comment="")
        assert p.duration == -5


# ===========================================================================
# WaitUserActionParams
# ===========================================================================


class TestWaitUserActionParamsValidation:
    def test_empty_message_with_context_raises(self) -> None:
        from models.steps.wait_user_action_params import WaitUserActionParams

        with pytest.raises(ValidationError):
            WaitUserActionParams.model_validate({"message": "", "comment": ""}, context=_CTX)


# ===========================================================================
# WaitHtmlElementsParams
# ===========================================================================


class TestWaitHtmlElementsParamsValidation:
    def test_empty_selector_with_context_raises(self) -> None:
        from models.steps.wait_html_elements_params import WaitHtmlElementsParams

        with pytest.raises(ValidationError):
            WaitHtmlElementsParams.model_validate(
                {
                    "selector": "",
                    "wait_mode": "visible",
                    "timeout_ms": 5000,
                    "count_min": 1,
                    "count_max": 10,
                    "comment": "",
                },
                context=_CTX,
            )

    def test_negative_timeout_with_context_raises(self) -> None:
        from models.steps.wait_html_elements_params import WaitHtmlElementsParams

        with pytest.raises(ValidationError):
            WaitHtmlElementsParams.model_validate(
                {
                    "selector": ".x",
                    "wait_mode": "visible",
                    "timeout_ms": -1,
                    "count_min": 1,
                    "count_max": 10,
                    "comment": "",
                },
                context=_CTX,
            )


# ===========================================================================
# ScrollDownParams
# ===========================================================================


class TestScrollDownParamsValidation:
    def test_negative_pixels_with_context_raises(self) -> None:
        from models.steps.scroll_down_params import ScrollDownParams

        with pytest.raises(ValidationError):
            ScrollDownParams.model_validate({"pixels": -10, "comment": ""}, context=_CTX)

    def test_no_context_negative_pixels_accepted(self) -> None:
        from models.steps.scroll_down_params import ScrollDownParams

        p = ScrollDownParams(pixels=-10, comment="")
        assert p.pixels == -10
