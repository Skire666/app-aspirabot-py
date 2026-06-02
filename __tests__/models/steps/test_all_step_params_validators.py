"""Validator-focused tests for all remaining step parameter models.

Validators only fire when ``context`` is supplied. Without context, any value
is accepted (safe for JSON deserialization). Tests cover:
  - valid data passes with context
  - each invalid combination raises ValidationError with context
  - construction without context never raises
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CTX = {"step_index": 0}


def _validate(cls: type, data: dict, ctx: dict | None = _CTX):
    return cls.model_validate(data, context=ctx)


# ---------------------------------------------------------------------------
# ClickOnElementParams / ClickForDownloadParams
# (identical validator logic — test both)
# ---------------------------------------------------------------------------


class TestClickOnElementParams:
    from models.steps.click_on_element_params import ClickOnElementParams as _Cls

    _BASE = {"selector": ".btn", "click_mode": "normal", "index_clicked": 0, "comment": ""}

    def test_valid_passes(self) -> None:
        from models.steps.click_on_element_params import ClickOnElementParams
        p = _validate(ClickOnElementParams, self._BASE)
        assert p.selector == ".btn"

    def test_empty_selector_raises(self) -> None:
        from models.steps.click_on_element_params import ClickOnElementParams
        data = {**self._BASE, "selector": ""}
        with pytest.raises(ValidationError):
            _validate(ClickOnElementParams, data)

    def test_negative_index_raises(self) -> None:
        from models.steps.click_on_element_params import ClickOnElementParams
        data = {**self._BASE, "index_clicked": -1}
        with pytest.raises(ValidationError):
            _validate(ClickOnElementParams, data)

    def test_zero_index_valid(self) -> None:
        from models.steps.click_on_element_params import ClickOnElementParams
        data = {**self._BASE, "index_clicked": 0}
        p = _validate(ClickOnElementParams, data)
        assert p.index_clicked == 0

    def test_no_context_accepts_invalid(self) -> None:
        from models.steps.click_on_element_params import ClickOnElementParams
        p = ClickOnElementParams(selector="", click_mode="normal", index_clicked=-9, comment="")
        assert p.selector == ""


class TestClickForDownloadParams:
    _BASE = {"selector": ".dl-btn", "click_mode": "normal", "index_clicked": 0, "comment": ""}

    def test_valid_passes(self) -> None:
        from models.steps.click_for_download_params import ClickForDownloadParams
        p = _validate(ClickForDownloadParams, self._BASE)
        assert p.selector == ".dl-btn"

    def test_empty_selector_raises(self) -> None:
        from models.steps.click_for_download_params import ClickForDownloadParams
        with pytest.raises(ValidationError):
            _validate(ClickForDownloadParams, {**self._BASE, "selector": ""})

    def test_negative_index_raises(self) -> None:
        from models.steps.click_for_download_params import ClickForDownloadParams
        with pytest.raises(ValidationError):
            _validate(ClickForDownloadParams, {**self._BASE, "index_clicked": -1})


# ---------------------------------------------------------------------------
# CloseTabsParams
# ---------------------------------------------------------------------------


class TestCloseTabsParams:
    _BASE = {"filter_mode": "url_source", "filter_custom": "", "max_tabs": 5, "comment": ""}

    def test_valid_passes(self) -> None:
        from models.steps.close_tabs_params import CloseTabsParams
        p = _validate(CloseTabsParams, self._BASE)
        assert p.max_tabs == 5

    def test_zero_max_tabs_raises(self) -> None:
        from models.steps.close_tabs_params import CloseTabsParams
        with pytest.raises(ValidationError):
            _validate(CloseTabsParams, {**self._BASE, "max_tabs": 0})

    def test_negative_max_tabs_raises(self) -> None:
        from models.steps.close_tabs_params import CloseTabsParams
        with pytest.raises(ValidationError):
            _validate(CloseTabsParams, {**self._BASE, "max_tabs": -1})

    def test_no_context_no_raise(self) -> None:
        from models.steps.close_tabs_params import CloseTabsParams
        p = CloseTabsParams(filter_mode="url_source", filter_custom="", max_tabs=-5, comment="")
        assert p.max_tabs == -5


# ---------------------------------------------------------------------------
# CountHtmlElementsParams
# ---------------------------------------------------------------------------


class TestCountHtmlElementsParams:
    _BASE = {"selector": ".item", "success_if": "success", "operator": "equal", "value": 1, "comment": ""}

    def test_valid_passes(self) -> None:
        from models.steps.count_html_elements_params import CountHtmlElementsParams
        p = _validate(CountHtmlElementsParams, self._BASE)
        assert p.selector == ".item"

    def test_empty_selector_raises(self) -> None:
        from models.steps.count_html_elements_params import CountHtmlElementsParams
        with pytest.raises(ValidationError):
            _validate(CountHtmlElementsParams, {**self._BASE, "selector": ""})

    def test_negative_value_raises(self) -> None:
        from models.steps.count_html_elements_params import CountHtmlElementsParams
        with pytest.raises(ValidationError):
            _validate(CountHtmlElementsParams, {**self._BASE, "value": -1})

    def test_no_context_no_raise(self) -> None:
        from models.steps.count_html_elements_params import CountHtmlElementsParams
        p = CountHtmlElementsParams(selector="", success_if="bad", operator=">=", value=-1, comment="")
        assert p.value == -1


# ---------------------------------------------------------------------------
# ExportDataToJsParams
# ---------------------------------------------------------------------------


class TestExportDataToJsParams:
    _BASE = {"prefix_file": "export_", "comment": ""}

    def test_valid_passes(self) -> None:
        from models.steps.export_data_to_js_params import ExportDataToJsParams
        p = _validate(ExportDataToJsParams, self._BASE)
        assert p.prefix_file == "export_"

    def test_empty_prefix_raises(self) -> None:
        from models.steps.export_data_to_js_params import ExportDataToJsParams
        with pytest.raises(ValidationError):
            _validate(ExportDataToJsParams, {"prefix_file": "", "comment": ""})

    def test_no_context_accepts_empty(self) -> None:
        from models.steps.export_data_to_js_params import ExportDataToJsParams
        p = ExportDataToJsParams(prefix_file="", comment="")
        assert p.prefix_file == ""


# ---------------------------------------------------------------------------
# ExtractLinksParams
# ---------------------------------------------------------------------------


class TestExtractLinksParams:
    _BASE = {"selector": "a", "target": "all", "mapping": "links", "comment": ""}

    def test_valid_passes(self) -> None:
        from models.steps.extract_links_params import ExtractLinksParams
        p = _validate(ExtractLinksParams, self._BASE)
        assert p.selector == "a"

    def test_empty_selector_raises(self) -> None:
        from models.steps.extract_links_params import ExtractLinksParams
        with pytest.raises(ValidationError):
            _validate(ExtractLinksParams, {**self._BASE, "selector": ""})

    def test_empty_mapping_raises(self) -> None:
        from models.steps.extract_links_params import ExtractLinksParams
        with pytest.raises(ValidationError):
            _validate(ExtractLinksParams, {**self._BASE, "mapping": ""})

    def test_no_context_no_raise(self) -> None:
        from models.steps.extract_links_params import ExtractLinksParams
        p = ExtractLinksParams(selector="", target="all", mapping="", comment="")
        assert p.selector == ""


# ---------------------------------------------------------------------------
# ExtractTextsParams
# ---------------------------------------------------------------------------


class TestExtractTextsParams:
    _BASE = {"selector": ".title", "extract_mode": "innerText", "target": "first", "mapping": "titles", "comment": ""}

    def test_valid_passes(self) -> None:
        from models.steps.extract_texts_params import ExtractTextsParams
        p = _validate(ExtractTextsParams, self._BASE)
        assert p.selector == ".title"

    def test_empty_selector_raises(self) -> None:
        from models.steps.extract_texts_params import ExtractTextsParams
        with pytest.raises(ValidationError):
            _validate(ExtractTextsParams, {**self._BASE, "selector": ""})

    def test_empty_mapping_raises(self) -> None:
        from models.steps.extract_texts_params import ExtractTextsParams
        with pytest.raises(ValidationError):
            _validate(ExtractTextsParams, {**self._BASE, "mapping": ""})

    def test_no_context_no_raise(self) -> None:
        from models.steps.extract_texts_params import ExtractTextsParams
        p = ExtractTextsParams(selector="", extract_mode="innerText", target="first", mapping="", comment="")
        assert p.selector == ""


# ---------------------------------------------------------------------------
# ExtractVariableParams
# ---------------------------------------------------------------------------


class TestExtractVariableParams:
    _BASE = {"variable": "last_url", "mapping": "data_key", "comment": ""}

    def test_valid_passes(self) -> None:
        from models.steps.extract_variable_params import ExtractVariableParams
        p = _validate(ExtractVariableParams, self._BASE)
        assert p.variable == "last_url"

    def test_empty_variable_raises(self) -> None:
        from models.steps.extract_variable_params import ExtractVariableParams
        with pytest.raises(ValidationError):
            _validate(ExtractVariableParams, {"variable": "", "mapping": "k", "comment": ""})

    def test_empty_mapping_raises(self) -> None:
        from models.steps.extract_variable_params import ExtractVariableParams
        with pytest.raises(ValidationError):
            _validate(ExtractVariableParams, {"variable": "v", "mapping": "", "comment": ""})

    def test_no_context_no_raise(self) -> None:
        from models.steps.extract_variable_params import ExtractVariableParams
        p = ExtractVariableParams(variable="", mapping="", comment="")
        assert p.variable == ""


# ---------------------------------------------------------------------------
# KillBrowserParams
# ---------------------------------------------------------------------------


class TestKillBrowserParams:
    _BASE = {"wait_duration": 5, "wait_unit": "s", "comment": ""}

    def test_valid_passes(self) -> None:
        from models.steps.kill_browser_params import KillBrowserParams
        p = _validate(KillBrowserParams, self._BASE)
        assert p.wait_duration == 5

    def test_negative_duration_raises(self) -> None:
        from models.steps.kill_browser_params import KillBrowserParams
        with pytest.raises(ValidationError):
            _validate(KillBrowserParams, {**self._BASE, "wait_duration": -1})

    def test_invalid_unit_raises(self) -> None:
        from models.steps.kill_browser_params import KillBrowserParams
        with pytest.raises(ValidationError):
            _validate(KillBrowserParams, {**self._BASE, "wait_unit": "hours"})

    def test_no_context_no_raise(self) -> None:
        from models.steps.kill_browser_params import KillBrowserParams
        p = KillBrowserParams(wait_duration=-1, wait_unit="invalid", comment="")
        assert p.wait_duration == -1


# ---------------------------------------------------------------------------
# RefreshPageParams
# ---------------------------------------------------------------------------


class TestRefreshPageParams:
    _BASE = {"clear_cache": False, "wait_state": "load", "timeout_duration": 30, "timeout_unit": "s", "comment": ""}

    def test_valid_passes(self) -> None:
        from models.steps.refresh_page_params import RefreshPageParams
        p = _validate(RefreshPageParams, self._BASE)
        assert p.timeout_duration == 30

    def test_zero_timeout_raises(self) -> None:
        from models.steps.refresh_page_params import RefreshPageParams
        with pytest.raises(ValidationError):
            _validate(RefreshPageParams, {**self._BASE, "timeout_duration": 0})

    def test_invalid_unit_raises(self) -> None:
        from models.steps.refresh_page_params import RefreshPageParams
        with pytest.raises(ValidationError):
            _validate(RefreshPageParams, {**self._BASE, "timeout_unit": "days"})

    def test_no_context_no_raise(self) -> None:
        from models.steps.refresh_page_params import RefreshPageParams
        p = RefreshPageParams(clear_cache=False, wait_state="load", timeout_duration=0, timeout_unit="days", comment="")
        assert p.timeout_duration == 0


# ---------------------------------------------------------------------------
# ScrollDownParams
# ---------------------------------------------------------------------------


class TestScrollDownParams:
    def test_valid_passes(self) -> None:
        from models.steps.scroll_down_params import ScrollDownParams
        p = _validate(ScrollDownParams, {"pixels": 100, "comment": ""})
        assert p.pixels == 100

    def test_negative_pixels_raises(self) -> None:
        from models.steps.scroll_down_params import ScrollDownParams
        with pytest.raises(ValidationError):
            _validate(ScrollDownParams, {"pixels": -1, "comment": ""})

    def test_no_context_no_raise(self) -> None:
        from models.steps.scroll_down_params import ScrollDownParams
        p = ScrollDownParams(pixels=-100, comment="")
        assert p.pixels == -100


# ---------------------------------------------------------------------------
# WaitPageStateParams
# ---------------------------------------------------------------------------


class TestWaitPageStateParams:
    _BASE = {"wait_state": "load", "timeout_duration": 30, "timeout_unit": "s", "comment": ""}

    def test_valid_passes(self) -> None:
        from models.steps.wait_page_state_params import WaitPageStateParams
        p = _validate(WaitPageStateParams, self._BASE)
        assert p.timeout_duration == 30

    def test_zero_timeout_raises(self) -> None:
        from models.steps.wait_page_state_params import WaitPageStateParams
        with pytest.raises(ValidationError):
            _validate(WaitPageStateParams, {**self._BASE, "timeout_duration": 0})

    def test_invalid_unit_raises(self) -> None:
        from models.steps.wait_page_state_params import WaitPageStateParams
        with pytest.raises(ValidationError):
            _validate(WaitPageStateParams, {**self._BASE, "timeout_unit": "hours"})

    def test_no_context_no_raise(self) -> None:
        from models.steps.wait_page_state_params import WaitPageStateParams
        p = WaitPageStateParams(wait_state="load", timeout_duration=0, timeout_unit="bad", comment="")
        assert p.timeout_duration == 0


# ---------------------------------------------------------------------------
# YoutubeTranscriptsParams
# ---------------------------------------------------------------------------


class TestYoutubeTranscriptsParams:
    _BASE = {"title": "Video Title", "comment": "", "basic_info": False, "ddl_srt": False}

    def test_valid_passes(self) -> None:
        from models.steps.youtube_transcripts_params import YoutubeTranscriptsParams
        p = _validate(YoutubeTranscriptsParams, self._BASE)
        assert p.title == "Video Title"

    def test_empty_title_raises(self) -> None:
        from models.steps.youtube_transcripts_params import YoutubeTranscriptsParams
        with pytest.raises(ValidationError):
            _validate(YoutubeTranscriptsParams, {**self._BASE, "title": ""})

    def test_no_context_accepts_empty_title(self) -> None:
        from models.steps.youtube_transcripts_params import YoutubeTranscriptsParams
        p = YoutubeTranscriptsParams(title="", comment="", basic_info=False, ddl_srt=False)
        assert p.title == ""


# ---------------------------------------------------------------------------
# WaitHtmlElementsParams
# ---------------------------------------------------------------------------


class TestWaitHtmlElementsParams:
    _BASE = {
        "selector": ".item", "operator": "equal", "quantity": 1,
        "retry_delay": 1, "retry_unit": "s", "retry_max": 10, "comment": ""
    }

    def test_valid_passes(self) -> None:
        from models.steps.wait_html_elements_params import WaitHtmlElementsParams
        p = _validate(WaitHtmlElementsParams, self._BASE)
        assert p.selector == ".item"

    def test_empty_selector_raises(self) -> None:
        from models.steps.wait_html_elements_params import WaitHtmlElementsParams
        with pytest.raises(ValidationError):
            _validate(WaitHtmlElementsParams, {**self._BASE, "selector": ""})

    def test_negative_quantity_raises(self) -> None:
        from models.steps.wait_html_elements_params import WaitHtmlElementsParams
        with pytest.raises(ValidationError):
            _validate(WaitHtmlElementsParams, {**self._BASE, "quantity": -1})

    def test_negative_retry_delay_raises(self) -> None:
        from models.steps.wait_html_elements_params import WaitHtmlElementsParams
        with pytest.raises(ValidationError):
            _validate(WaitHtmlElementsParams, {**self._BASE, "retry_delay": -1})

    def test_invalid_retry_unit_raises(self) -> None:
        from models.steps.wait_html_elements_params import WaitHtmlElementsParams
        with pytest.raises(ValidationError):
            _validate(WaitHtmlElementsParams, {**self._BASE, "retry_unit": "years"})

    def test_no_context_no_raise(self) -> None:
        from models.steps.wait_html_elements_params import WaitHtmlElementsParams
        p = WaitHtmlElementsParams(
            selector="", operator=">=", quantity=-1,
            retry_delay=-1, retry_unit="bad", retry_max=0, comment=""
        )
        assert p.selector == ""


# ---------------------------------------------------------------------------
# WaitUserActionParams
# ---------------------------------------------------------------------------


class TestWaitUserActionParams:
    _BASE = {"condition": "always", "wait_duration": 30, "wait_unit": "s", "comment": ""}

    def test_valid_passes(self) -> None:
        from models.steps.wait_user_action_params import WaitUserActionParams
        p = _validate(WaitUserActionParams, self._BASE)
        assert p.wait_duration == 30

    def test_negative_duration_raises(self) -> None:
        from models.steps.wait_user_action_params import WaitUserActionParams
        with pytest.raises(ValidationError):
            _validate(WaitUserActionParams, {**self._BASE, "wait_duration": -1})

    def test_invalid_unit_raises(self) -> None:
        from models.steps.wait_user_action_params import WaitUserActionParams
        with pytest.raises(ValidationError):
            _validate(WaitUserActionParams, {**self._BASE, "wait_unit": "days"})

    def test_no_context_no_raise(self) -> None:
        from models.steps.wait_user_action_params import WaitUserActionParams
        p = WaitUserActionParams(condition="continue", wait_duration=-1, wait_unit="days", comment="")
        assert p.wait_duration == -1
