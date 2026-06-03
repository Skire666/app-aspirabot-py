"""Regression tests — model-to-presenter formatter integration.

Freezes the contract between step params `to_dict()` output and the
`format_step_label()` display formatter.  These are integration tests:
they build a typed params instance, serialise it, and verify that the
formatter produces output containing the expected values.

If a field is renamed in a params model, these tests break *before* the
real UI breaks — catching the regression at the boundary between layers.

Scope:
- Does NOT duplicate the unit_testing formatter tests (which pass raw dicts).
- Tests the full path: params instance → to_dict() → format_step_label().
"""

from __future__ import annotations

from presenters.step_label_formatters import format_step_label
from shared.enums import StepTypeEnum


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _label(step_type: StepTypeEnum, params_instance) -> str:
    return format_step_label(step_type, params_instance.to_dict(), 0, {})


# ---------------------------------------------------------------------------
# CLICK_FOR_DOWNLOAD
# ---------------------------------------------------------------------------


class TestClickForDownloadIntegration:
    def test_selector_appears_in_label(self) -> None:
        from models.steps.click_for_download_params import ClickForDownloadParams

        p = ClickForDownloadParams(selector=".download-me", click_mode="left", index_clicked=1, comment="")
        label = _label(StepTypeEnum.E_CLICK_FOR_DOWNLOAD, p)
        assert ".download-me" in label
        assert "Index 1" in label

    def test_empty_selector_shows_vide(self) -> None:
        from models.steps.click_for_download_params import ClickForDownloadParams

        p = ClickForDownloadParams(selector="", click_mode="left", index_clicked=0, comment="")
        assert "<vide>" in _label(StepTypeEnum.E_CLICK_FOR_DOWNLOAD, p)


# ---------------------------------------------------------------------------
# CLICK_ON_ELEMENT
# ---------------------------------------------------------------------------


class TestClickOnElementIntegration:
    def test_selector_appears_in_label(self) -> None:
        from models.steps.click_on_element_params import ClickOnElementParams

        p = ClickOnElementParams(selector="#accept-btn", click_mode="left", index_clicked=0, comment="")
        label = _label(StepTypeEnum.E_CLICK_ON_ELEMENT, p)
        assert "#accept-btn" in label

    def test_index_appears_in_label(self) -> None:
        from models.steps.click_on_element_params import ClickOnElementParams

        p = ClickOnElementParams(selector=".nav", click_mode="left", index_clicked=3, comment="")
        assert "Index 3" in _label(StepTypeEnum.E_CLICK_ON_ELEMENT, p)


# ---------------------------------------------------------------------------
# CLOSE_TABS
# ---------------------------------------------------------------------------


class TestCloseTabsIntegration:
    def test_max_tabs_appears_in_label(self) -> None:
        from models.steps.close_tabs_params import CloseTabsParams

        p = CloseTabsParams(filter_mode="<<SOURCE>>", filter_custom="", max_tabs=7, comment="")
        assert "7" in _label(StepTypeEnum.E_CLOSE_TABS, p)

    def test_custom_filter_appears_in_label(self) -> None:
        from models.steps.close_tabs_params import CloseTabsParams

        p = CloseTabsParams(filter_mode="<<CUSTOM>>", filter_custom="example.com", max_tabs=1, comment="")
        assert "example.com" in _label(StepTypeEnum.E_CLOSE_TABS, p)


# ---------------------------------------------------------------------------
# COUNT_HTML_ELEMENTS
# ---------------------------------------------------------------------------


class TestCountHtmlElementsIntegration:
    def test_selector_and_operator_in_label(self) -> None:
        from models.steps.count_html_elements_params import CountHtmlElementsParams

        p = CountHtmlElementsParams(selector=".result", success_if="success", operator="greater_than", value=10, comment="")
        label = _label(StepTypeEnum.E_COUNT_HTML_ELEMENTS, p)
        assert ".result" in label
        assert ">" in label
        assert "10" in label


# ---------------------------------------------------------------------------
# COUNT_HTML_IMAGES
# ---------------------------------------------------------------------------


class TestCountHtmlImagesIntegration:
    def test_operator_and_value_in_label(self) -> None:
        from models.steps.count_html_images_params import CountHtmlImagesParams

        p = CountHtmlImagesParams(
            width_min=200, width_max=1920, height_min=200, height_max=1080,
            success_if="success", operator="equal", value=4, comment="",
        )
        label = _label(StepTypeEnum.E_COUNT_HTML_IMAGES, p)
        assert "==" in label
        assert "4" in label


# ---------------------------------------------------------------------------
# DOWNLOAD_IMAGE
# ---------------------------------------------------------------------------


class TestDownloadImageIntegration:
    def test_unique_only_true_label(self) -> None:
        from models.steps.download_image_params import DownloadImageParams

        p = DownloadImageParams(mode="all", unique_only=True, width_min=250, width_max=99999, height_min=250, height_max=99999, comment="")
        assert "doublons refusés" in _label(StepTypeEnum.E_DOWNLOAD_IMAGE, p)

    def test_unique_only_false_label(self) -> None:
        from models.steps.download_image_params import DownloadImageParams

        p = DownloadImageParams(mode="selected", unique_only=False, width_min=100, width_max=800, height_min=100, height_max=600, comment="")
        assert "doublons autorisés" in _label(StepTypeEnum.E_DOWNLOAD_IMAGE, p)

    def test_size_range_in_label(self) -> None:
        from models.steps.download_image_params import DownloadImageParams

        p = DownloadImageParams(mode="all", unique_only=True, width_min=300, width_max=1920, height_min=200, height_max=1080, comment="")
        label = _label(StepTypeEnum.E_DOWNLOAD_IMAGE, p)
        assert "300" in label
        assert "200" in label


# ---------------------------------------------------------------------------
# EXPORT_DATA_TO_JS
# ---------------------------------------------------------------------------


class TestExportDataToJsIntegration:
    def test_prefix_in_label(self) -> None:
        from models.steps.export_data_to_js_params import ExportDataToJsParams

        p = ExportDataToJsParams(prefix_file="output_", comment="")
        assert "output_" in _label(StepTypeEnum.E_EXPORT_DATA_TO_JS, p)

    def test_empty_prefix_shows_vide(self) -> None:
        from models.steps.export_data_to_js_params import ExportDataToJsParams

        p = ExportDataToJsParams(prefix_file="", comment="")
        assert "<vide>" in _label(StepTypeEnum.E_EXPORT_DATA_TO_JS, p)


# ---------------------------------------------------------------------------
# EXTRACT_LINKS
# ---------------------------------------------------------------------------


class TestExtractLinksIntegration:
    def test_selector_and_mapping_in_label(self) -> None:
        from models.steps.extract_links_params import ExtractLinksParams

        p = ExtractLinksParams(selector="a.nav", target="all", mapping="nav_links", comment="")
        label = _label(StepTypeEnum.E_EXTRACT_LINKS, p)
        assert "a.nav" in label
        assert "nav_links" in label


# ---------------------------------------------------------------------------
# EXTRACT_TEXTS
# ---------------------------------------------------------------------------


class TestExtractTextsIntegration:
    def test_selector_and_mode_in_label(self) -> None:
        from models.steps.extract_texts_params import ExtractTextsParams

        p = ExtractTextsParams(selector=".headline", extract_mode="innerText", target="first", mapping="headlines", comment="")
        label = _label(StepTypeEnum.E_EXTRACT_TEXTS, p)
        assert ".headline" in label
        assert "headlines" in label


# ---------------------------------------------------------------------------
# EXTRACT_VARIABLE
# ---------------------------------------------------------------------------


class TestExtractVariableIntegration:
    def test_variable_name_in_label(self) -> None:
        from models.steps.extract_variable_params import ExtractVariableParams

        p = ExtractVariableParams(variable="last_url", mapping="url_key", comment="")
        assert "last_url" in _label(StepTypeEnum.E_EXTRACT_VARIABLE, p)


# ---------------------------------------------------------------------------
# JUMP_TO_STEP
# ---------------------------------------------------------------------------


class TestJumpToStepIntegration:
    def test_success_condition_with_known_target(self) -> None:
        from models.steps.jump_to_step_params import JumpToStepParams

        p = JumpToStepParams(condition="success", target_hexastring="ab12", comment="")
        label = format_step_label(StepTypeEnum.E_JUMP_TO_STEP, p.to_dict(), 0, {"ab12": 2})
        assert "succès" in label
        assert "03" in label  # idx=2 → 2+1=3 → zfill(2) = "03"

    def test_always_condition_without_context(self) -> None:
        from models.steps.jump_to_step_params import JumpToStepParams

        p = JumpToStepParams(condition="always", target_hexastring="xxxx", comment="")
        label = format_step_label(StepTypeEnum.E_JUMP_TO_STEP, p.to_dict(), 0, {})
        assert "TOUJOURS" in label
        assert "????" in label  # target not in ctx → unknown


# ---------------------------------------------------------------------------
# KILL_BROWSER
# ---------------------------------------------------------------------------


class TestKillBrowserIntegration:
    def test_duration_and_unit_in_label(self) -> None:
        from models.steps.kill_browser_params import KillBrowserParams

        p = KillBrowserParams(wait_duration=5, wait_unit="s", comment="")
        label = _label(StepTypeEnum.E_KILL_BROWSER, p)
        assert "5" in label
        assert "sec" in label


# ---------------------------------------------------------------------------
# OPEN_URL
# ---------------------------------------------------------------------------


class TestOpenUrlIntegration:
    def test_source_mode_label(self) -> None:
        from models.steps.open_url_params import OpenUrlParams

        p = OpenUrlParams(url_mode="<<SOURCE>>", url_custom="", wait_state="load", wait_dns_solver=5, timeout_duration=10, timeout_unit="s", comment="")
        label = _label(StepTypeEnum.E_OPEN_URL, p)
        assert "10" in label
        assert "sec" in label
        assert "source" in label.lower()

    def test_custom_mode_label(self) -> None:
        from models.steps.open_url_params import OpenUrlParams

        p = OpenUrlParams(url_mode="<<CUSTOM>>", url_custom="https://test.com", wait_state="load", wait_dns_solver=5, timeout_duration=15, timeout_unit="m", comment="")
        label = _label(StepTypeEnum.E_OPEN_URL, p)
        assert "https://test.com" in label
        assert "min" in label


# ---------------------------------------------------------------------------
# REFRESH_PAGE
# ---------------------------------------------------------------------------


class TestRefreshPageIntegration:
    def test_clear_cache_true_shows_ctrl_f5(self) -> None:
        from models.steps.refresh_page_params import RefreshPageParams

        p = RefreshPageParams(clear_cache=True, wait_state="networkidle", timeout_duration=8, timeout_unit="s", comment="")
        assert "F5" in _label(StepTypeEnum.E_REFRESH_PAGE, p)

    def test_wait_state_in_label(self) -> None:
        from models.steps.refresh_page_params import RefreshPageParams

        p = RefreshPageParams(clear_cache=False, wait_state="networkidle", timeout_duration=8, timeout_unit="s", comment="")
        assert "networkidle" in _label(StepTypeEnum.E_REFRESH_PAGE, p)


# ---------------------------------------------------------------------------
# SCROLL_DOWN
# ---------------------------------------------------------------------------


class TestScrollDownIntegration:
    def test_pixels_in_label(self) -> None:
        from models.steps.scroll_down_params import ScrollDownParams

        p = ScrollDownParams(pixels=1200, comment="")
        assert "1200" in _label(StepTypeEnum.E_SCROLL_DOWN, p)


# ---------------------------------------------------------------------------
# SECTION_STEPS
# ---------------------------------------------------------------------------


class TestSectionIntegration:
    def test_title_in_label(self) -> None:
        from models.steps.section_params import SectionParams

        p = SectionParams(title="Authentication Flow", comment="")
        label = _label(StepTypeEnum.E_SECTION_STEPS, p)
        assert "Authentication Flow" in label
        assert "Section" in label


# ---------------------------------------------------------------------------
# WAIT_FIXED_TIME
# ---------------------------------------------------------------------------


class TestWaitFixedTimeIntegration:
    def test_duration_and_unit_in_label(self) -> None:
        from models.steps.wait_fixed_time_params import WaitFixedTimeParams

        p = WaitFixedTimeParams(duration=3, unit="s", comment="")
        label = _label(StepTypeEnum.E_WAIT_FIXED_TIME, p)
        assert "3" in label
        assert "sec" in label

    def test_milliseconds_unit_in_label(self) -> None:
        from models.steps.wait_fixed_time_params import WaitFixedTimeParams

        p = WaitFixedTimeParams(duration=500, unit="ms", comment="")
        assert "millisec" in _label(StepTypeEnum.E_WAIT_FIXED_TIME, p)


# ---------------------------------------------------------------------------
# WAIT_HTML_ELEMENTS
# ---------------------------------------------------------------------------


class TestWaitHtmlElementsIntegration:
    def test_selector_and_operator_in_label(self) -> None:
        from models.steps.wait_html_elements_params import WaitHtmlElementsParams

        p = WaitHtmlElementsParams(
            selector=".card", operator="greater_or_equal", quantity=5,
            retry_delay=500, retry_unit="ms", retry_max=10, comment="",
        )
        label = _label(StepTypeEnum.E_WAIT_HTML_ELEMENTS, p)
        assert ".card" in label
        assert ">=" in label
        assert "5" in label


# ---------------------------------------------------------------------------
# WAIT_HTML_IMAGES
# ---------------------------------------------------------------------------


class TestWaitHtmlImagesIntegration:
    def test_retry_delay_and_size_in_label(self) -> None:
        from models.steps.wait_html_images_params import WaitHtmlImagesParams

        p = WaitHtmlImagesParams(
            height_min=300, height_max=99999, width_min=400, width_max=99999,
            operator="equal", quantity=1, retry_delay=250, retry_unit="ms", retry_max=5, comment="",
        )
        label = _label(StepTypeEnum.E_WAIT_HTML_IMAGES, p)
        assert "250" in label
        assert "millisec" in label


# ---------------------------------------------------------------------------
# WAIT_PAGE_STATE
# ---------------------------------------------------------------------------


class TestWaitPageStateIntegration:
    def test_wait_state_and_timeout_in_label(self) -> None:
        from models.steps.wait_page_state_params import WaitPageStateParams

        p = WaitPageStateParams(wait_state="domcontentloaded", timeout_duration=20, timeout_unit="s", comment="")
        label = _label(StepTypeEnum.E_WAIT_PAGE_STATE, p)
        assert "domcontentloaded" in label
        assert "20" in label
        assert "sec" in label


# ---------------------------------------------------------------------------
# WAIT_USER_ACTION
# ---------------------------------------------------------------------------


class TestWaitUserActionIntegration:
    def test_success_condition_in_label(self) -> None:
        from models.steps.wait_user_action_params import WaitUserActionParams

        p = WaitUserActionParams(condition="success", wait_duration=3, wait_unit="s", comment="")
        assert "succès" in _label(StepTypeEnum.E_WAIT_USER_ACTION, p)

    def test_zero_duration_no_delay_string(self) -> None:
        from models.steps.wait_user_action_params import WaitUserActionParams

        p = WaitUserActionParams(condition="always", wait_duration=0, wait_unit="s", comment="")
        assert "patienter" not in _label(StepTypeEnum.E_WAIT_USER_ACTION, p)


# ---------------------------------------------------------------------------
# YOUTUBE_TRANSCRIPTS
# ---------------------------------------------------------------------------


class TestYoutubeTranscriptsIntegration:
    def test_title_in_label(self) -> None:
        from models.steps.youtube_transcripts_params import YoutubeTranscriptsParams

        p = YoutubeTranscriptsParams(title="Python Tutorial", comment="", basic_info=True, ddl_srt=False)
        label = _label(StepTypeEnum.E_YOUTUBE_TRANSCRIPTS, p)
        assert "Python Tutorial" in label
        assert "YouTube" in label
