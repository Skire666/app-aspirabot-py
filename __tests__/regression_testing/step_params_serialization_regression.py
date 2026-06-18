"""Regression tests — step params serialization contracts.

Freezes the to_dict() key structure and round-trip behaviour for every
concrete step params class.  These tests capture the JSON persistence
contract: if a field is renamed or a key changes, downstream deserialisers
(StepScrapingModel.import_from_data_json) and formatters will silently break.

Scope:
- Not duplicating validator logic already in unit_testing.
- Not testing SectionParams/WaitFixedTimeParams/OpenUrlParams round-trips
  (already covered in unit_testing/models/steps/test_step_params.py).
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _round_trip(cls: type, data: dict) -> dict:
    """Build instance, serialize, rebuild, and return the second dict."""
    instance = cls(**data)
    d = instance.to_dict()
    rebuilt = cls(**d)
    return rebuilt.to_dict()


# ---------------------------------------------------------------------------
# ClickOnElementParams
# ---------------------------------------------------------------------------


class TestClickOnElementParamsSerialization:
    _DATA = {"selector": "#submit-btn", "click_mode": "left", "index_clicked": 2, "comment": "ok"}

    def test_to_dict_expected_keys(self) -> None:
        from models.steps.click_on_element_params import ClickOnElementParams

        d = ClickOnElementParams(**self._DATA).to_dict()
        assert set(d.keys()) == {"selector", "click_mode", "index_clicked", "comment"}, (
            "to_dict() must expose exactly the four contract keys"
        )

    def test_to_dict_values_preserved(self) -> None:
        from models.steps.click_on_element_params import ClickOnElementParams

        d = ClickOnElementParams(**self._DATA).to_dict()
        assert d["selector"] == "#submit-btn"
        assert d["index_clicked"] == 2
        assert d["click_mode"] == "left"

    def test_round_trip(self) -> None:
        from models.steps.click_on_element_params import ClickOnElementParams

        assert _round_trip(ClickOnElementParams, self._DATA) == ClickOnElementParams(**self._DATA).to_dict()


# ---------------------------------------------------------------------------
# ClickForDownloadParams
# ---------------------------------------------------------------------------


class TestClickForDownloadParamsSerialization:
    _DATA = {"selector": ".dl-link", "click_mode": "left", "index_clicked": 0, "comment": ""}

    def test_to_dict_expected_keys(self) -> None:
        from models.steps.click_for_download_params import ClickForDownloadParams

        d = ClickForDownloadParams(**self._DATA).to_dict()
        assert set(d.keys()) == {"selector", "click_mode", "index_clicked", "comment"}

    def test_round_trip(self) -> None:
        from models.steps.click_for_download_params import ClickForDownloadParams

        assert _round_trip(ClickForDownloadParams, self._DATA) == ClickForDownloadParams(**self._DATA).to_dict()


# ---------------------------------------------------------------------------
# CountHtmlElementsParams
# ---------------------------------------------------------------------------


class TestCountHtmlElementsParamsSerialization:
    _DATA = {"selector": ".item", "success_if": "success", "operator": "greater_than", "value": 3, "comment": ""}

    def test_to_dict_expected_keys(self) -> None:
        from models.steps.count_html_elements_params import CountHtmlElementsParams

        d = CountHtmlElementsParams(**self._DATA).to_dict()
        assert set(d.keys()) == {"selector", "success_if", "operator", "value", "comment"}

    def test_round_trip(self) -> None:
        from models.steps.count_html_elements_params import CountHtmlElementsParams

        assert _round_trip(CountHtmlElementsParams, self._DATA) == CountHtmlElementsParams(**self._DATA).to_dict()


# ---------------------------------------------------------------------------
# CountHtmlImagesParams
# ---------------------------------------------------------------------------


class TestCountHtmlImagesParamsSerialization:
    _DATA = {
        "width_min": 100,
        "width_max": 800,
        "height_min": 100,
        "height_max": 600,
        "success_if": "success",
        "operator": "equal",
        "value": 5,
        "comment": "",
    }

    def test_to_dict_expected_keys(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams

        d = CountHtmlImagesParams(**self._DATA).to_dict()
        assert set(d.keys()) == {
            "width_min",
            "width_max",
            "height_min",
            "height_max",
            "success_if",
            "operator",
            "value",
            "comment",
        }

    def test_round_trip(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams

        assert _round_trip(CountHtmlImagesParams, self._DATA) == CountHtmlImagesParams(**self._DATA).to_dict()


# ---------------------------------------------------------------------------
# DownloadImageParams — has a custom to_dict() with a specific key order
# ---------------------------------------------------------------------------


class TestDownloadImageParamsSerialization:
    _DATA = {
        "mode": "all",
        "unique_only": True,
        "width_min": 200,
        "width_max": 1920,
        "height_min": 200,
        "height_max": 1080,
        "comment": "",
    }

    def test_to_dict_expected_keys(self) -> None:
        from models.steps.download_image_params import DownloadImageParams

        d = DownloadImageParams(**self._DATA).to_dict()
        assert set(d.keys()) == {"mode", "unique_only", "width_min", "width_max", "height_min", "height_max", "comment"}

    def test_to_dict_key_order_contract(self) -> None:
        from models.steps.download_image_params import DownloadImageParams

        d = DownloadImageParams(**self._DATA).to_dict()
        # The custom to_dict() defines a specific key order; freeze it.
        expected_order = ["mode", "unique_only", "height_min", "height_max", "width_min", "width_max", "comment"]
        assert list(d.keys()) == expected_order, (
            "DownloadImageParams.to_dict() has a documented key order used by formatters and serialisers"
        )

    def test_unique_only_bool_type_preserved(self) -> None:
        from models.steps.download_image_params import DownloadImageParams

        d = DownloadImageParams(**self._DATA).to_dict()
        assert isinstance(d["unique_only"], bool), "unique_only must stay a bool after serialisation"

    def test_round_trip(self) -> None:
        from models.steps.download_image_params import DownloadImageParams

        assert _round_trip(DownloadImageParams, self._DATA) == DownloadImageParams(**self._DATA).to_dict()


# ---------------------------------------------------------------------------
# ExportDataToJsParams
# ---------------------------------------------------------------------------


class TestExportDataToJsParamsSerialization:
    _DATA = {"prefix_file": "results_", "comment": "export step"}

    def test_to_dict_expected_keys(self) -> None:
        from models.steps.export_data_to_js_params import ExportDataToJsParams

        d = ExportDataToJsParams(**self._DATA).to_dict()
        assert set(d.keys()) == {"prefix_file", "comment"}

    def test_round_trip(self) -> None:
        from models.steps.export_data_to_js_params import ExportDataToJsParams

        assert _round_trip(ExportDataToJsParams, self._DATA) == ExportDataToJsParams(**self._DATA).to_dict()


# ---------------------------------------------------------------------------
# ExtractLinksParams
# ---------------------------------------------------------------------------


class TestExtractLinksParamsSerialization:
    _DATA = {"selector": "a.nav", "target": "all", "mapping": "nav_links", "cutted_ampersand": False, "comment": ""}

    def test_to_dict_expected_keys(self) -> None:
        from models.steps.extract_links_params import ExtractLinksParams

        d = ExtractLinksParams(**self._DATA).to_dict()
        assert set(d.keys()) == {"selector", "target", "mapping", "cutted_ampersand", "comment"}

    def test_round_trip(self) -> None:
        from models.steps.extract_links_params import ExtractLinksParams

        assert _round_trip(ExtractLinksParams, self._DATA) == ExtractLinksParams(**self._DATA).to_dict()


# ---------------------------------------------------------------------------
# ExtractTextsParams
# ---------------------------------------------------------------------------


class TestExtractTextsParamsSerialization:
    _DATA = {"selector": "h1", "extract_mode": "innerText", "target": "first", "mapping": "title", "comment": ""}

    def test_to_dict_expected_keys(self) -> None:
        from models.steps.extract_texts_params import ExtractTextsParams

        d = ExtractTextsParams(**self._DATA).to_dict()
        assert set(d.keys()) == {"selector", "extract_mode", "target", "mapping", "comment"}

    def test_round_trip(self) -> None:
        from models.steps.extract_texts_params import ExtractTextsParams

        assert _round_trip(ExtractTextsParams, self._DATA) == ExtractTextsParams(**self._DATA).to_dict()


# ---------------------------------------------------------------------------
# ExtractVariableParams
# ---------------------------------------------------------------------------


class TestExtractVariableParamsSerialization:
    _DATA = {"variable": "last_url", "mapping": "current_url", "comment": ""}

    def test_to_dict_expected_keys(self) -> None:
        from models.steps.extract_variable_params import ExtractVariableParams

        d = ExtractVariableParams(**self._DATA).to_dict()
        assert set(d.keys()) == {"variable", "mapping", "comment"}

    def test_round_trip(self) -> None:
        from models.steps.extract_variable_params import ExtractVariableParams

        assert _round_trip(ExtractVariableParams, self._DATA) == ExtractVariableParams(**self._DATA).to_dict()


# ---------------------------------------------------------------------------
# JumpToStepParams
# ---------------------------------------------------------------------------


class TestJumpToStepParamsSerialization:
    _DATA = {"condition": "success", "target_hexastring": "ab12", "comment": "jump on success"}

    def test_to_dict_expected_keys(self) -> None:
        from models.steps.jump_to_step_params import JumpToStepParams

        d = JumpToStepParams(**self._DATA).to_dict()
        assert set(d.keys()) == {"condition", "target_hexastring", "comment"}

    def test_all_conditions_serializable(self) -> None:
        from models.steps.jump_to_step_params import JumpToStepParams

        for cond in ("success", "failure", "always"):
            d = JumpToStepParams(condition=cond, target_hexastring="1234", comment="").to_dict()
            assert d["condition"] == cond

    def test_round_trip(self) -> None:
        from models.steps.jump_to_step_params import JumpToStepParams

        assert _round_trip(JumpToStepParams, self._DATA) == JumpToStepParams(**self._DATA).to_dict()


# ---------------------------------------------------------------------------
# KillBrowserParams
# ---------------------------------------------------------------------------


class TestKillBrowserParamsSerialization:
    _DATA = {"wait_duration": 3, "wait_unit": "s", "comment": ""}

    def test_to_dict_expected_keys(self) -> None:
        from models.steps.kill_browser_params import KillBrowserParams

        d = KillBrowserParams(**self._DATA).to_dict()
        assert set(d.keys()) == {"wait_duration", "wait_unit", "comment"}

    def test_round_trip(self) -> None:
        from models.steps.kill_browser_params import KillBrowserParams

        assert _round_trip(KillBrowserParams, self._DATA) == KillBrowserParams(**self._DATA).to_dict()


# ---------------------------------------------------------------------------
# RefreshPageParams
# ---------------------------------------------------------------------------


class TestRefreshPageParamsSerialization:
    _DATA = {
        "clear_cache": True,
        "wait_until": "networkidle",
        "timeout_duration": 15,
        "timeout_unit": "s",
        "comment": "",
    }

    def test_to_dict_expected_keys(self) -> None:
        from models.steps.refresh_page_params import RefreshPageParams

        d = RefreshPageParams(**self._DATA).to_dict()
        assert set(d.keys()) == {"clear_cache", "wait_until", "timeout_duration", "timeout_unit", "comment"}

    def test_clear_cache_bool_preserved(self) -> None:
        from models.steps.refresh_page_params import RefreshPageParams

        d = RefreshPageParams(**self._DATA).to_dict()
        assert isinstance(d["clear_cache"], bool)
        assert d["clear_cache"] is True

    def test_round_trip(self) -> None:
        from models.steps.refresh_page_params import RefreshPageParams

        assert _round_trip(RefreshPageParams, self._DATA) == RefreshPageParams(**self._DATA).to_dict()


# ---------------------------------------------------------------------------
# ScrollDownParams
# ---------------------------------------------------------------------------


class TestScrollDownParamsSerialization:
    _DATA = {"pixels": 750, "nbr_loops": 3, "delay_pause": 500, "comment": "scroll half page"}

    def test_to_dict_expected_keys(self) -> None:
        from models.steps.scroll_down_params import ScrollDownParams

        d = ScrollDownParams(**self._DATA).to_dict()
        assert set(d.keys()) == {"pixels", "nbr_loops", "delay_pause", "comment"}

    def test_round_trip(self) -> None:
        from models.steps.scroll_down_params import ScrollDownParams

        assert _round_trip(ScrollDownParams, self._DATA) == ScrollDownParams(**self._DATA).to_dict()


# ---------------------------------------------------------------------------
# WaitHtmlElementsParams
# ---------------------------------------------------------------------------


class TestWaitHtmlElementsParamsSerialization:
    _DATA = {
        "selector": ".result-item",
        "operator": "greater_or_equal",
        "quantity": 5,
        "retry_delay": 500,
        "retry_unit": "ms",
        "retry_max": 20,
        "comment": "",
    }

    def test_to_dict_expected_keys(self) -> None:
        from models.steps.wait_html_elements_params import WaitHtmlElementsParams

        d = WaitHtmlElementsParams(**self._DATA).to_dict()
        assert set(d.keys()) == {
            "selector",
            "operator",
            "quantity",
            "retry_delay",
            "retry_unit",
            "retry_max",
            "comment",
        }

    def test_round_trip(self) -> None:
        from models.steps.wait_html_elements_params import WaitHtmlElementsParams

        assert _round_trip(WaitHtmlElementsParams, self._DATA) == WaitHtmlElementsParams(**self._DATA).to_dict()


# ---------------------------------------------------------------------------
# WaitHtmlImagesParams
# ---------------------------------------------------------------------------


class TestWaitHtmlImagesParamsSerialization:
    _DATA = {
        "height_min": 250,
        "height_max": 99999,
        "width_min": 250,
        "width_max": 99999,
        "operator": "equal",
        "quantity": 3,
        "retry_delay": 400,
        "retry_unit": "ms",
        "retry_max": 10,
        "comment": "",
    }

    def test_to_dict_expected_keys(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams

        d = WaitHtmlImagesParams(**self._DATA).to_dict()
        assert "height_min" in d
        assert "width_min" in d
        assert "operator" in d
        assert "retry_delay" in d
        assert "retry_unit" in d
        assert "retry_max" in d

    def test_round_trip(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams

        assert _round_trip(WaitHtmlImagesParams, self._DATA) == WaitHtmlImagesParams(**self._DATA).to_dict()


# ---------------------------------------------------------------------------
# WaitPageStateParams
# ---------------------------------------------------------------------------


class TestWaitPageStateParamsSerialization:
    _DATA = {"wait_until": "load", "timeout_duration": 30, "timeout_unit": "s", "comment": ""}

    def test_to_dict_expected_keys(self) -> None:
        from models.steps.wait_page_state_params import WaitPageStateParams

        d = WaitPageStateParams(**self._DATA).to_dict()
        assert set(d.keys()) == {"wait_until", "timeout_duration", "timeout_unit", "comment"}

    def test_round_trip(self) -> None:
        from models.steps.wait_page_state_params import WaitPageStateParams

        assert _round_trip(WaitPageStateParams, self._DATA) == WaitPageStateParams(**self._DATA).to_dict()


# ---------------------------------------------------------------------------
# WaitUserActionParams
# ---------------------------------------------------------------------------


class TestWaitUserActionParamsSerialization:
    _DATA = {"condition": "always", "wait_duration": 5, "wait_unit": "s", "comment": "pause here"}

    def test_to_dict_expected_keys(self) -> None:
        from models.steps.wait_user_action_params import WaitUserActionParams

        d = WaitUserActionParams(**self._DATA).to_dict()
        assert set(d.keys()) == {"condition", "wait_duration", "wait_unit", "comment"}

    def test_round_trip(self) -> None:
        from models.steps.wait_user_action_params import WaitUserActionParams

        assert _round_trip(WaitUserActionParams, self._DATA) == WaitUserActionParams(**self._DATA).to_dict()


# ---------------------------------------------------------------------------
# YoutubeTranscriptsParams
# ---------------------------------------------------------------------------


class TestYoutubeTranscriptsParamsSerialization:
    _DATA = {"title": "My Channel", "comment": "", "basic_info": True, "ddl_srt": False}

    def test_to_dict_expected_keys(self) -> None:
        from models.steps.youtube_transcripts_params import YoutubeTranscriptsParams

        d = YoutubeTranscriptsParams(**self._DATA).to_dict()
        assert set(d.keys()) == {"title", "comment", "basic_info", "ddl_srt"}

    def test_bool_fields_preserved(self) -> None:
        from models.steps.youtube_transcripts_params import YoutubeTranscriptsParams

        d = YoutubeTranscriptsParams(**self._DATA).to_dict()
        assert d["basic_info"] is True
        assert d["ddl_srt"] is False

    def test_round_trip(self) -> None:
        from models.steps.youtube_transcripts_params import YoutubeTranscriptsParams

        assert _round_trip(YoutubeTranscriptsParams, self._DATA) == YoutubeTranscriptsParams(**self._DATA).to_dict()


# ---------------------------------------------------------------------------
# Parametrized smoke test — all step param classes produce string-keyed dicts
# ---------------------------------------------------------------------------

_ALL_PARAMS_INSTANCES = [
    pytest.param(
        lambda: __import__(
            "models.steps.click_on_element_params", fromlist=["ClickOnElementParams"]
        ).ClickOnElementParams(selector=".btn", click_mode="left", index_clicked=0, comment=""),
        id="ClickOnElement",
    ),
    pytest.param(
        lambda: __import__(
            "models.steps.click_for_download_params", fromlist=["ClickForDownloadParams"]
        ).ClickForDownloadParams(selector=".dl", click_mode="left", index_clicked=0, comment=""),
        id="ClickForDownload",
    ),
    pytest.param(
        lambda: __import__("models.steps.close_tabs_params", fromlist=["CloseTabsParams"]).CloseTabsParams(
            filter_mode="<<SOURCE>>", filter_custom="", max_tabs=1, comment=""
        ),
        id="CloseTabs",
    ),
    pytest.param(
        lambda: __import__(
            "models.steps.count_html_elements_params", fromlist=["CountHtmlElementsParams"]
        ).CountHtmlElementsParams(selector=".item", success_if="success", operator="equal", value=1, comment=""),
        id="CountHtmlElements",
    ),
    pytest.param(
        lambda: __import__(
            "models.steps.count_html_images_params", fromlist=["CountHtmlImagesParams"]
        ).CountHtmlImagesParams(
            width_min=100,
            width_max=1000,
            height_min=100,
            height_max=1000,
            success_if="success",
            operator="equal",
            value=2,
            comment="",
        ),
        id="CountHtmlImages",
    ),
    pytest.param(
        lambda: __import__("models.steps.download_image_params", fromlist=["DownloadImageParams"]).DownloadImageParams(
            mode="all", unique_only=True, width_min=200, width_max=1920, height_min=200, height_max=1080, comment=""
        ),
        id="DownloadImage",
    ),
    pytest.param(
        lambda: __import__(
            "models.steps.export_data_to_js_params", fromlist=["ExportDataToJsParams"]
        ).ExportDataToJsParams(prefix_file="out_", comment=""),
        id="ExportDataToJs",
    ),
    pytest.param(
        lambda: __import__("models.steps.extract_links_params", fromlist=["ExtractLinksParams"]).ExtractLinksParams(
            selector="a", target="all", mapping="links", cutted_ampersand=False, comment=""
        ),
        id="ExtractLinks",
    ),
    pytest.param(
        lambda: __import__("models.steps.extract_texts_params", fromlist=["ExtractTextsParams"]).ExtractTextsParams(
            selector="p", extract_mode="innerText", target="all", mapping="texts", comment=""
        ),
        id="ExtractTexts",
    ),
    pytest.param(
        lambda: __import__(
            "models.steps.extract_variable_params", fromlist=["ExtractVariableParams"]
        ).ExtractVariableParams(variable="last_url", mapping="url", comment=""),
        id="ExtractVariable",
    ),
    pytest.param(
        lambda: __import__("models.steps.jump_to_step_params", fromlist=["JumpToStepParams"]).JumpToStepParams(
            condition="always", target_hexastring="ab12", comment=""
        ),
        id="JumpToStep",
    ),
    pytest.param(
        lambda: __import__("models.steps.kill_browser_params", fromlist=["KillBrowserParams"]).KillBrowserParams(
            wait_duration=2, wait_unit="s", comment=""
        ),
        id="KillBrowser",
    ),
    pytest.param(
        lambda: __import__("models.steps.refresh_page_params", fromlist=["RefreshPageParams"]).RefreshPageParams(
            clear_cache=False, wait_until="load", timeout_duration=10, timeout_unit="s", comment=""
        ),
        id="RefreshPage",
    ),
    pytest.param(
        lambda: __import__("models.steps.scroll_down_params", fromlist=["ScrollDownParams"]).ScrollDownParams(
            pixels=500, comment=""
        ),
        id="ScrollDown",
    ),
    pytest.param(
        lambda: __import__("models.steps.section_params", fromlist=["SectionParams"]).SectionParams(
            title="Phase 1", comment=""
        ),
        id="Section",
    ),
    pytest.param(
        lambda: __import__("models.steps.wait_fixed_time_params", fromlist=["WaitFixedTimeParams"]).WaitFixedTimeParams(
            duration=3, unit="s", comment=""
        ),
        id="WaitFixedTime",
    ),
    pytest.param(
        lambda: __import__(
            "models.steps.wait_html_elements_params", fromlist=["WaitHtmlElementsParams"]
        ).WaitHtmlElementsParams(
            selector=".row", operator="equal", quantity=10, retry_delay=500, retry_unit="ms", retry_max=10, comment=""
        ),
        id="WaitHtmlElements",
    ),
    pytest.param(
        lambda: __import__(
            "models.steps.wait_html_images_params", fromlist=["WaitHtmlImagesParams"]
        ).WaitHtmlImagesParams(
            height_min=250,
            height_max=99999,
            width_min=250,
            width_max=99999,
            operator="equal",
            quantity=1,
            retry_delay=400,
            retry_unit="ms",
            retry_max=10,
            comment="",
        ),
        id="WaitHtmlImages",
    ),
    pytest.param(
        lambda: __import__("models.steps.wait_page_state_params", fromlist=["WaitPageStateParams"]).WaitPageStateParams(
            wait_until="networkidle", timeout_duration=10, timeout_unit="s", comment=""
        ),
        id="WaitPageState",
    ),
    pytest.param(
        lambda: __import__(
            "models.steps.wait_user_action_params", fromlist=["WaitUserActionParams"]
        ).WaitUserActionParams(condition="always", wait_duration=5, wait_unit="s", comment=""),
        id="WaitUserAction",
    ),
    pytest.param(
        lambda: __import__(
            "models.steps.youtube_transcripts_params", fromlist=["YoutubeTranscriptsParams"]
        ).YoutubeTranscriptsParams(title="Tutorial", comment="", basic_info=True, ddl_srt=True),
        id="YoutubeTranscripts",
    ),
]


@pytest.mark.parametrize("factory", _ALL_PARAMS_INSTANCES)
def test_to_dict_returns_string_keyed_dict(factory) -> None:
    instance = factory()
    d = instance.to_dict()
    assert isinstance(d, dict), "to_dict() must return a dict"
    assert all(isinstance(k, str) for k in d), "All dict keys must be strings (JSON-serialisable)"


@pytest.mark.parametrize("factory", _ALL_PARAMS_INSTANCES)
def test_to_dict_contains_no_none_values(factory) -> None:
    instance = factory()
    d = instance.to_dict()
    assert all(v is not None for v in d.values()), (
        "to_dict() must not produce None values — None cannot be round-tripped through JSON cleanly"
    )
