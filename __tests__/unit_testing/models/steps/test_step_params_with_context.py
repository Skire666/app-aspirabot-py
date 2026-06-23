"""Tests for validate_with_context across all concrete step parameter models.

Each param model has a validate_with_context method that calls model_validate
with a context dict. These tests exercise both the valid path (returns []) and
the invalid path (returns error strings), covering the validator bodies that
only run when a context is provided.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from models.steps.check_url_page_params import CheckUrlPageParams
from models.steps.click_for_download_params import ClickForDownloadParams
from models.steps.click_on_element_params import ClickOnElementParams
from models.steps.close_tabs_params import CloseTabsParams
from models.steps.count_html_elements_params import CountHtmlElementsParams
from models.steps.count_html_images_params import CountHtmlImagesParams
from models.steps.download_image_params import DownloadImageParams
from models.steps.export_data_to_js_params import ExportDataToJsParams
from models.steps.extract_links_params import ExtractLinksParams
from models.steps.extract_texts_params import ExtractTextsParams
from models.steps.extract_variable_params import ExtractVariableParams
from models.steps.jump_to_step_params import JumpToStepParams
from models.steps.kill_browser_params import KillBrowserParams
from models.steps.open_url_params import OpenUrlParams
from models.steps.refresh_page_params import RefreshPageParams
from models.steps.restart_to_beginning_params import RestartToBeginningParams
from models.steps.scroll_down_params import ScrollDownParams
from models.steps.section_params import SectionParams
from models.steps.wait_fixed_time_params import WaitFixedTimeParams
from models.steps.wait_html_elements_params import WaitHtmlElementsParams
from models.steps.wait_html_images_params import WaitHtmlImagesParams
from models.steps.wait_page_state_params import WaitPageStateParams
from models.steps.wait_user_action_params import WaitUserActionParams
from models.steps.youtube_infos_video_params import YoutubeInfosVideoParams
from models.steps.youtube_subtitles_params import YoutubeSubtitlesParams
from models.steps_collections_model import StepsCollections
from shared.enums import WaitUntilEnum


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------


def _ctx() -> MagicMock:
    """Return a StepsCollections mock that satisfies cross-step queries."""
    mock = MagicMock(spec=StepsCollections)
    mock.find_by_id.return_value = MagicMock()
    mock.count_mapping_key.return_value = 1
    return mock


# ---------------------------------------------------------------------------
# SectionParams
# ---------------------------------------------------------------------------


class TestSectionParamsWithContext:
    def test_valid_title_returns_empty(self) -> None:
        p = SectionParams(title="My Section", comment="")
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_empty_title_returns_errors(self) -> None:
        p = SectionParams(title="", comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_whitespace_title_returns_errors(self) -> None:
        p = SectionParams(title="   ", comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# WaitFixedTimeParams
# ---------------------------------------------------------------------------


class TestWaitFixedTimeParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        p = WaitFixedTimeParams(duration=5, unit="s")
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_negative_duration_returns_errors(self) -> None:
        p = WaitFixedTimeParams(duration=-1, unit="s")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# OpenUrlParams
# ---------------------------------------------------------------------------


class TestOpenUrlParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        p = OpenUrlParams(wait_until=WaitUntilEnum.E_LOAD, wait_dns_solver=5, timeout_duration=10, timeout_unit="s", comment="")
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_zero_dns_solver_returns_errors(self) -> None:
        p = OpenUrlParams(wait_until=WaitUntilEnum.E_LOAD, wait_dns_solver=0, timeout_duration=10, timeout_unit="s", comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_invalid_timeout_unit_returns_errors(self) -> None:
        p = OpenUrlParams(wait_until=WaitUntilEnum.E_LOAD, wait_dns_solver=5, timeout_duration=10, timeout_unit="INVALID", comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_zero_timeout_duration_returns_errors(self) -> None:
        p = OpenUrlParams(wait_until=WaitUntilEnum.E_LOAD, wait_dns_solver=5, timeout_duration=0, timeout_unit="s", comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# CheckUrlPageParams
# ---------------------------------------------------------------------------


class TestCheckUrlPageParamsWithContext:
    def test_valid_both_true_returns_empty(self) -> None:
        p = CheckUrlPageParams(check_domain=True, check_path=True)
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_valid_one_true_returns_empty(self) -> None:
        p = CheckUrlPageParams(check_domain=True, check_path=False)
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_both_false_returns_errors(self) -> None:
        p = CheckUrlPageParams(check_domain=False, check_path=False)
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# ClickOnElementParams
# ---------------------------------------------------------------------------


class TestClickOnElementParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        p = ClickOnElementParams(selector=".btn", click_mode="left", index_clicked=0)
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_empty_selector_returns_errors(self) -> None:
        p = ClickOnElementParams(selector="", click_mode="left", index_clicked=0)
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_negative_index_returns_errors(self) -> None:
        p = ClickOnElementParams(selector=".btn", click_mode="left", index_clicked=-1)
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# ClickForDownloadParams
# ---------------------------------------------------------------------------


class TestClickForDownloadParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        p = ClickForDownloadParams(selector=".dl", click_mode="left", index_clicked=0)
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_empty_selector_returns_errors(self) -> None:
        p = ClickForDownloadParams(selector="", click_mode="left", index_clicked=0)
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_negative_index_returns_errors(self) -> None:
        p = ClickForDownloadParams(selector=".dl", click_mode="left", index_clicked=-2)
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# CloseTabsParams
# ---------------------------------------------------------------------------


class TestCloseTabsParamsWithContext:
    def test_valid_source_mode_returns_empty(self) -> None:
        p = CloseTabsParams(filter_mode="<<SOURCE>>", filter_custom="", max_tabs=5)
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_invalid_max_tabs_returns_errors(self) -> None:
        p = CloseTabsParams(filter_mode="<<SOURCE>>", filter_custom="", max_tabs=0)
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_custom_mode_without_filter_returns_errors(self) -> None:
        p = CloseTabsParams(filter_mode="<<CUSTOM>>", filter_custom="", max_tabs=5)
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_custom_mode_with_filter_returns_empty(self) -> None:
        p = CloseTabsParams(filter_mode="<<CUSTOM>>", filter_custom="pattern", max_tabs=5)
        assert p.validate_with_context(0, _ctx(), "s1") == []


# ---------------------------------------------------------------------------
# CountHtmlElementsParams
# ---------------------------------------------------------------------------


class TestCountHtmlElementsParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        p = CountHtmlElementsParams(selector=".el", success_if="success", operator="equal", value=5, comment="a")
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_empty_selector_returns_errors(self) -> None:
        p = CountHtmlElementsParams(selector="", success_if="success", operator="equal", value=5, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_negative_value_returns_errors(self) -> None:
        p = CountHtmlElementsParams(selector=".el", success_if="success", operator="equal", value=-1, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_invalid_success_if_returns_errors(self) -> None:
        p = CountHtmlElementsParams(selector=".el", success_if="bad", operator="equal", value=5, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_invalid_operator_returns_errors(self) -> None:
        p = CountHtmlElementsParams(selector=".el", success_if="success", operator="bad_op", value=5, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_empty_comment_returns_errors(self) -> None:
        p = CountHtmlElementsParams(selector=".el", success_if="success", operator="equal", value=5, comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# ScrollDownParams
# ---------------------------------------------------------------------------


class TestScrollDownParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        p = ScrollDownParams(pixels=100, nbr_loops=1, delay_pause=1)
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_zero_pixels_returns_errors(self) -> None:
        p = ScrollDownParams(pixels=0, nbr_loops=1, delay_pause=1)
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_zero_loops_returns_errors(self) -> None:
        p = ScrollDownParams(pixels=100, nbr_loops=0, delay_pause=1)
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# ExtractTextsParams
# ---------------------------------------------------------------------------


class TestExtractTextsParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        ctx = _ctx()
        ctx.count_mapping_key.return_value = 1
        p = ExtractTextsParams(selector=".el", extract_mode="innerText", target="all", mapping="mykey", comment="a comment")
        assert p.validate_with_context(0, ctx, "s1") == []

    def test_empty_selector_returns_errors(self) -> None:
        p = ExtractTextsParams(selector="", extract_mode="innerText", target="all", mapping="mykey", comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_empty_comment_returns_errors(self) -> None:
        p = ExtractTextsParams(selector=".el", extract_mode="innerText", target="all", mapping="mykey", comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_invalid_extract_mode_returns_errors(self) -> None:
        p = ExtractTextsParams(selector=".el", extract_mode="INVALID_MODE", target="all", mapping="mykey", comment="x")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_invalid_target_returns_errors(self) -> None:
        p = ExtractTextsParams(selector=".el", extract_mode="innerText", target="INVALID_TARGET", mapping="mykey", comment="x")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_duplicate_mapping_returns_errors(self) -> None:
        ctx = _ctx()
        ctx.count_mapping_key.return_value = 2
        p = ExtractTextsParams(selector=".el", extract_mode="innerText", target="all", mapping="mykey", comment="x")
        assert len(p.validate_with_context(0, ctx, "s1")) > 0


# ---------------------------------------------------------------------------
# JumpToStepParams
# ---------------------------------------------------------------------------


class TestJumpToStepParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        ctx = _ctx()
        ctx.find_by_id.return_value = MagicMock()
        p = JumpToStepParams(condition="success", target_hexastring="target_id", comment="a comment")
        assert p.validate_with_context(0, ctx, "source_id") == []

    def test_invalid_condition_returns_errors(self) -> None:
        ctx = _ctx()
        p = JumpToStepParams(condition="bad_cond", target_hexastring="target_id", comment="a")
        assert len(p.validate_with_context(0, ctx, "source_id")) > 0

    def test_empty_target_returns_errors(self) -> None:
        ctx = _ctx()
        p = JumpToStepParams(condition="success", target_hexastring="", comment="a")
        assert len(p.validate_with_context(0, ctx, "source_id")) > 0

    def test_self_reference_returns_errors(self) -> None:
        ctx = _ctx()
        p = JumpToStepParams(condition="success", target_hexastring="same_id", comment="a")
        assert len(p.validate_with_context(0, ctx, "same_id")) > 0

    def test_target_not_found_returns_errors(self) -> None:
        ctx = _ctx()
        ctx.find_by_id.return_value = None
        p = JumpToStepParams(condition="success", target_hexastring="missing_id", comment="a")
        assert len(p.validate_with_context(0, ctx, "source_id")) > 0

    def test_empty_comment_returns_errors(self) -> None:
        ctx = _ctx()
        ctx.find_by_id.return_value = MagicMock()
        p = JumpToStepParams(condition="success", target_hexastring="target_id", comment="")
        assert len(p.validate_with_context(0, ctx, "source_id")) > 0


# ---------------------------------------------------------------------------
# WaitHtmlElementsParams
# ---------------------------------------------------------------------------


class TestWaitHtmlElementsParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        p = WaitHtmlElementsParams(selector=".el", operator="equal", quantity=1, retry_delay=2, retry_unit="s", retry_max=3, comment="a")
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_empty_selector_returns_errors(self) -> None:
        p = WaitHtmlElementsParams(selector="", operator="equal", quantity=1, retry_delay=2, retry_unit="s", retry_max=3, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_invalid_operator_returns_errors(self) -> None:
        p = WaitHtmlElementsParams(selector=".el", operator="INVALID", quantity=1, retry_delay=2, retry_unit="s", retry_max=3, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_negative_quantity_returns_errors(self) -> None:
        p = WaitHtmlElementsParams(selector=".el", operator="equal", quantity=-1, retry_delay=2, retry_unit="s", retry_max=3, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_zero_retry_delay_returns_errors(self) -> None:
        p = WaitHtmlElementsParams(selector=".el", operator="equal", quantity=1, retry_delay=0, retry_unit="s", retry_max=3, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_invalid_retry_unit_returns_errors(self) -> None:
        p = WaitHtmlElementsParams(selector=".el", operator="equal", quantity=1, retry_delay=2, retry_unit="INVALID", retry_max=3, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_zero_retry_max_returns_errors(self) -> None:
        p = WaitHtmlElementsParams(selector=".el", operator="equal", quantity=1, retry_delay=2, retry_unit="s", retry_max=0, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_empty_comment_returns_errors(self) -> None:
        p = WaitHtmlElementsParams(selector=".el", operator="equal", quantity=1, retry_delay=2, retry_unit="s", retry_max=3, comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# RefreshPageParams
# ---------------------------------------------------------------------------


class TestRefreshPageParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        p = RefreshPageParams(clear_cache=False, wait_until=WaitUntilEnum.E_LOAD, timeout_duration=10, timeout_unit="s", comment="")
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_zero_timeout_returns_errors(self) -> None:
        p = RefreshPageParams(clear_cache=False, wait_until=WaitUntilEnum.E_LOAD, timeout_duration=0, timeout_unit="s", comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_invalid_timeout_unit_returns_errors(self) -> None:
        p = RefreshPageParams(clear_cache=False, wait_until=WaitUntilEnum.E_LOAD, timeout_duration=10, timeout_unit="INVALID", comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# RestartToBeginningParams
# ---------------------------------------------------------------------------


class TestRestartToBeginningParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        p = RestartToBeginningParams(jump_only_if_urls_remaining=True, comment="a comment")
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_empty_comment_returns_empty(self) -> None:
        p = RestartToBeginningParams(jump_only_if_urls_remaining=False, comment="")
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_valid_no_urls_remaining_flag_returns_empty(self) -> None:
        p = RestartToBeginningParams(jump_only_if_urls_remaining=False, comment="")
        assert p.validate_with_context(0, _ctx(), "s1") == []


# ---------------------------------------------------------------------------
# KillBrowserParams
# ---------------------------------------------------------------------------


class TestKillBrowserParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        p = KillBrowserParams(wait_duration=5, wait_unit="s")
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_negative_wait_duration_returns_errors(self) -> None:
        p = KillBrowserParams(wait_duration=-1, wait_unit="s")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_invalid_wait_unit_returns_errors(self) -> None:
        p = KillBrowserParams(wait_duration=5, wait_unit="INVALID")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# WaitPageStateParams
# ---------------------------------------------------------------------------


class TestWaitPageStateParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        p = WaitPageStateParams(wait_until=WaitUntilEnum.E_LOAD, timeout_duration=10, timeout_unit="s", comment="")
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_zero_timeout_returns_errors(self) -> None:
        p = WaitPageStateParams(wait_until=WaitUntilEnum.E_LOAD, timeout_duration=0, timeout_unit="s", comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_invalid_timeout_unit_returns_errors(self) -> None:
        p = WaitPageStateParams(wait_until=WaitUntilEnum.E_LOAD, timeout_duration=10, timeout_unit="INVALID", comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# ExportDataToJsParams
# ---------------------------------------------------------------------------


class TestExportDataToJsParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        p = ExportDataToJsParams(prefix_file="output")
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_empty_prefix_file_returns_errors(self) -> None:
        p = ExportDataToJsParams(prefix_file="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_whitespace_prefix_file_returns_errors(self) -> None:
        p = ExportDataToJsParams(prefix_file="   ")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# ExtractLinksParams
# ---------------------------------------------------------------------------


class TestExtractLinksParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        ctx = _ctx()
        ctx.count_mapping_key.return_value = 1
        p = ExtractLinksParams(selector=".link", target="all", mapping="mykey", cutted_ampersand=False, comment="a comment")
        assert p.validate_with_context(0, ctx, "s1") == []

    def test_empty_selector_returns_errors(self) -> None:
        p = ExtractLinksParams(selector="", target="all", mapping="mykey", cutted_ampersand=False, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_empty_comment_returns_errors(self) -> None:
        p = ExtractLinksParams(selector=".link", target="all", mapping="mykey", cutted_ampersand=False, comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_invalid_target_returns_errors(self) -> None:
        p = ExtractLinksParams(selector=".link", target="INVALID", mapping="mykey", cutted_ampersand=False, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# ExtractVariableParams
# ---------------------------------------------------------------------------


class TestExtractVariableParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        ctx = _ctx()
        ctx.count_mapping_key.return_value = 1
        p = ExtractVariableParams(variable="datetime_now", mapping="mykey")
        assert p.validate_with_context(0, ctx, "s1") == []

    def test_invalid_variable_returns_errors(self) -> None:
        p = ExtractVariableParams(variable="invalid_var", mapping="mykey")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_empty_mapping_returns_errors(self) -> None:
        p = ExtractVariableParams(variable="datetime_now", mapping="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# WaitUserActionParams
# ---------------------------------------------------------------------------


class TestWaitUserActionParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        p = WaitUserActionParams(condition="always", wait_duration=5, wait_unit="s")
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_invalid_condition_returns_errors(self) -> None:
        p = WaitUserActionParams(condition="INVALID", wait_duration=5, wait_unit="s")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_zero_wait_duration_returns_errors(self) -> None:
        p = WaitUserActionParams(condition="always", wait_duration=0, wait_unit="s")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_invalid_wait_unit_returns_errors(self) -> None:
        p = WaitUserActionParams(condition="always", wait_duration=5, wait_unit="INVALID")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# YoutubeInfosVideoParams
# ---------------------------------------------------------------------------


class TestYoutubeInfosVideoParamsWithContext:
    def test_valid_empty_comment_returns_empty(self) -> None:
        p = YoutubeInfosVideoParams(comment="")
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_valid_short_comment_returns_empty(self) -> None:
        p = YoutubeInfosVideoParams(comment="short")
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_too_long_comment_returns_errors(self) -> None:
        p = YoutubeInfosVideoParams(comment="x" * 51)
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# YoutubeSubtitlesParams
# ---------------------------------------------------------------------------


class TestYoutubeSubtitlesParamsWithContext:
    def test_valid_empty_comment_returns_empty(self) -> None:
        p = YoutubeSubtitlesParams(comment="")
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_too_long_comment_returns_errors(self) -> None:
        p = YoutubeSubtitlesParams(comment="x" * 51)
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# WaitHtmlImagesParams
# ---------------------------------------------------------------------------


class TestWaitHtmlImagesParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        p = WaitHtmlImagesParams(height_min=0, height_max=100, width_min=0, width_max=200, operator="equal", quantity=1, retry_delay=2, retry_unit="s", retry_max=3, comment="a")
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_negative_height_min_returns_errors(self) -> None:
        p = WaitHtmlImagesParams(height_min=-1, height_max=100, width_min=0, width_max=100, operator="equal", quantity=1, retry_delay=2, retry_unit="s", retry_max=3, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_invalid_operator_returns_errors(self) -> None:
        p = WaitHtmlImagesParams(height_min=0, height_max=100, width_min=0, width_max=100, operator="INVALID", quantity=1, retry_delay=2, retry_unit="s", retry_max=3, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_negative_quantity_returns_errors(self) -> None:
        p = WaitHtmlImagesParams(height_min=0, height_max=100, width_min=0, width_max=100, operator="equal", quantity=-1, retry_delay=2, retry_unit="s", retry_max=3, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_zero_retry_delay_returns_errors(self) -> None:
        p = WaitHtmlImagesParams(height_min=0, height_max=100, width_min=0, width_max=100, operator="equal", quantity=1, retry_delay=0, retry_unit="s", retry_max=3, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_invalid_retry_unit_returns_errors(self) -> None:
        p = WaitHtmlImagesParams(height_min=0, height_max=100, width_min=0, width_max=100, operator="equal", quantity=1, retry_delay=2, retry_unit="INVALID", retry_max=3, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_zero_retry_max_returns_errors(self) -> None:
        p = WaitHtmlImagesParams(height_min=0, height_max=100, width_min=0, width_max=100, operator="equal", quantity=1, retry_delay=2, retry_unit="s", retry_max=0, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_height_range_invalid_returns_errors(self) -> None:
        p = WaitHtmlImagesParams(height_min=100, height_max=50, width_min=0, width_max=100, operator="equal", quantity=1, retry_delay=2, retry_unit="s", retry_max=3, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_width_range_invalid_returns_errors(self) -> None:
        p = WaitHtmlImagesParams(height_min=0, height_max=100, width_min=100, width_max=50, operator="equal", quantity=1, retry_delay=2, retry_unit="s", retry_max=3, comment="a")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_empty_comment_returns_errors(self) -> None:
        p = WaitHtmlImagesParams(height_min=0, height_max=100, width_min=0, width_max=100, operator="equal", quantity=1, retry_delay=2, retry_unit="s", retry_max=3, comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# CountHtmlImagesParams
# ---------------------------------------------------------------------------


class TestCountHtmlImagesParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        p = CountHtmlImagesParams(width_min=0, width_max=100, height_min=0, height_max=100, success_if="success", operator="equal", value=5, comment="")
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_negative_height_min_returns_errors(self) -> None:
        p = CountHtmlImagesParams(width_min=0, width_max=100, height_min=-1, height_max=100, success_if="success", operator="equal", value=5, comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_zero_height_max_returns_errors(self) -> None:
        p = CountHtmlImagesParams(width_min=0, width_max=100, height_min=0, height_max=0, success_if="success", operator="equal", value=5, comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_invalid_success_if_returns_errors(self) -> None:
        p = CountHtmlImagesParams(width_min=0, width_max=100, height_min=0, height_max=100, success_if="bad", operator="equal", value=5, comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_invalid_operator_returns_errors(self) -> None:
        p = CountHtmlImagesParams(width_min=0, width_max=100, height_min=0, height_max=100, success_if="success", operator="bad_op", value=5, comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_negative_value_returns_errors(self) -> None:
        p = CountHtmlImagesParams(width_min=0, width_max=100, height_min=0, height_max=100, success_if="success", operator="equal", value=-1, comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_height_range_invalid_returns_errors(self) -> None:
        p = CountHtmlImagesParams(width_min=0, width_max=100, height_min=100, height_max=50, success_if="success", operator="equal", value=5, comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_width_range_invalid_returns_errors(self) -> None:
        p = CountHtmlImagesParams(width_min=100, width_max=50, height_min=0, height_max=100, success_if="success", operator="equal", value=5, comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0


# ---------------------------------------------------------------------------
# DownloadImageParams
# ---------------------------------------------------------------------------


class TestDownloadImageParamsWithContext:
    def test_valid_returns_empty(self) -> None:
        p = DownloadImageParams(mode="all", unique_only=True, width_min=0, width_max=100, height_min=0, height_max=100, comment="")
        assert p.validate_with_context(0, _ctx(), "s1") == []

    def test_negative_height_min_returns_errors(self) -> None:
        p = DownloadImageParams(mode="all", unique_only=True, width_min=0, width_max=100, height_min=-1, height_max=100, comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_zero_height_max_returns_errors(self) -> None:
        p = DownloadImageParams(mode="all", unique_only=True, width_min=0, width_max=100, height_min=0, height_max=0, comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_height_range_invalid_returns_errors(self) -> None:
        p = DownloadImageParams(mode="all", unique_only=True, width_min=0, width_max=100, height_min=100, height_max=50, comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0

    def test_width_range_invalid_returns_errors(self) -> None:
        p = DownloadImageParams(mode="all", unique_only=True, width_min=100, width_max=50, height_min=0, height_max=100, comment="")
        assert len(p.validate_with_context(0, _ctx(), "s1")) > 0
