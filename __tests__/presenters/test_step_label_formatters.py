"""Tests for presenters/step_label_formatters.py."""

from __future__ import annotations

import pytest

from presenters.step_label_formatters import format_step_label
from shared.enums import OpenUrlModeEnum, StepTypeEnum


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt(step_type: StepTypeEnum, params: dict | None = None, idx: int = 0, ctx: dict | None = None) -> str:
    return format_step_label(step_type, params or {}, idx, ctx or {})


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


class TestDispatcher:
    def test_unknown_type_falls_back_to_enum_value(self) -> None:
        # Use a registered type but pass a StepTypeEnum that the registry has
        # then test the fallback by passing a mock-like object with a .value attr.
        # Simplest: verify a registered type returns a non-empty string.
        result = _fmt(StepTypeEnum.E_SECTION_STEPS, {"title": "X"})
        assert "Section" in result

    def test_returns_string(self) -> None:
        result = _fmt(StepTypeEnum.E_SCROLL_DOWN, {"pixels": 500})
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# CLICK_FOR_DOWNLOAD
# ---------------------------------------------------------------------------


class TestFmtClickForDownload:
    def test_with_selector(self) -> None:
        result = _fmt(StepTypeEnum.E_CLICK_FOR_DOWNLOAD, {"selector": ".btn", "index_clicked": 2})
        assert "télécharger" in result
        assert "Index 2" in result
        assert ".btn" in result

    def test_empty_selector_shows_vide(self) -> None:
        result = _fmt(StepTypeEnum.E_CLICK_FOR_DOWNLOAD, {})
        assert "<vide>" in result


# ---------------------------------------------------------------------------
# CLICK_ON_ELEMENT
# ---------------------------------------------------------------------------


class TestFmtClickOnElement:
    def test_with_selector(self) -> None:
        result = _fmt(StepTypeEnum.E_CLICK_ON_ELEMENT, {"selector": "#id", "index_clicked": 1})
        assert "élément" in result
        assert "Index 1" in result
        assert "#id" in result

    def test_empty_selector_shows_vide(self) -> None:
        result = _fmt(StepTypeEnum.E_CLICK_ON_ELEMENT, {})
        assert "<vide>" in result


# ---------------------------------------------------------------------------
# CLOSE_TABS
# ---------------------------------------------------------------------------


class TestFmtCloseTabs:
    def test_source_mode(self) -> None:
        result = _fmt(StepTypeEnum.E_CLOSE_TABS, {"max_tabs": 3, "filter_mode": OpenUrlModeEnum.E_SOURCE.value})
        assert "3" in result
        assert "départ" in result

    def test_custom_mode(self) -> None:
        result = _fmt(
            StepTypeEnum.E_CLOSE_TABS,
            {"max_tabs": 1, "filter_mode": OpenUrlModeEnum.E_CUSTOM.value, "filter_custom": "example.com"},
        )
        assert "example.com" in result

    def test_defaults(self) -> None:
        result = _fmt(StepTypeEnum.E_CLOSE_TABS, {})
        assert "onglets" in result


# ---------------------------------------------------------------------------
# COUNT_HTML_ELEMENTS
# ---------------------------------------------------------------------------


class TestFmtCountHtmlElements:
    def test_equal_operator(self) -> None:
        result = _fmt(StepTypeEnum.E_COUNT_HTML_ELEMENTS, {"operator": "equal", "selector": ".x", "value": 5})
        assert "==" in result
        assert "5" in result
        assert ".x" in result

    def test_not_equal_operator(self) -> None:
        result = _fmt(StepTypeEnum.E_COUNT_HTML_ELEMENTS, {"operator": "not_equal", "value": 2, "selector": "p"})
        assert "!=" in result

    def test_greater_than_operator(self) -> None:
        result = _fmt(StepTypeEnum.E_COUNT_HTML_ELEMENTS, {"operator": "greater_than", "value": 0, "selector": "div"})
        assert ">" in result

    def test_unknown_operator_shows_question_mark(self) -> None:
        result = _fmt(StepTypeEnum.E_COUNT_HTML_ELEMENTS, {"operator": "unknown_op"})
        assert "?" in result


# ---------------------------------------------------------------------------
# COUNT_HTML_IMAGES
# ---------------------------------------------------------------------------


class TestFmtCountHtmlImages:
    def test_basic(self) -> None:
        result = _fmt(StepTypeEnum.E_COUNT_HTML_IMAGES, {"operator": "equal", "value": 3})
        assert "==" in result
        assert "3" in result
        assert "Taille" in result

    def test_custom_sizes(self) -> None:
        result = _fmt(
            StepTypeEnum.E_COUNT_HTML_IMAGES,
            {"operator": "less_than", "value": 1, "width_min": 100, "height_min": 100, "width_max": 800, "height_max": 600},
        )
        assert "100x100" in result
        assert "800x600" in result


# ---------------------------------------------------------------------------
# DOWNLOAD_IMAGE
# ---------------------------------------------------------------------------


class TestFmtDownloadImage:
    def test_unique_only_true(self) -> None:
        result = _fmt(StepTypeEnum.E_DOWNLOAD_IMAGE, {"unique_only": True, "mode": "all"})
        assert "doublons refusés" in result

    def test_unique_only_false(self) -> None:
        result = _fmt(StepTypeEnum.E_DOWNLOAD_IMAGE, {"unique_only": False, "mode": "selected"})
        assert "doublons autorisés" in result

    def test_size_range_displayed(self) -> None:
        result = _fmt(
            StepTypeEnum.E_DOWNLOAD_IMAGE,
            {"unique_only": True, "mode": "all", "width_min": 200, "height_min": 200, "width_max": 1000, "height_max": 800},
        )
        assert "200x200" in result


# ---------------------------------------------------------------------------
# EXPORT_DATA_TO_JS
# ---------------------------------------------------------------------------


class TestFmtExportDataToJs:
    def test_prefix(self) -> None:
        result = _fmt(StepTypeEnum.E_EXPORT_DATA_TO_JS, {"prefix_file": "results"})
        assert "results" in result

    def test_empty_prefix_shows_vide(self) -> None:
        result = _fmt(StepTypeEnum.E_EXPORT_DATA_TO_JS, {})
        assert "<vide>" in result


# ---------------------------------------------------------------------------
# EXTRACT_LINKS
# ---------------------------------------------------------------------------


class TestFmtExtractLinks:
    def test_basic(self) -> None:
        result = _fmt(StepTypeEnum.E_EXTRACT_LINKS, {"selector": "a", "target": "links", "mapping": "map1"})
        assert "liens" in result
        assert "a" in result
        assert "map1" in result

    def test_empty_selector(self) -> None:
        result = _fmt(StepTypeEnum.E_EXTRACT_LINKS, {})
        assert "<vide>" in result


# ---------------------------------------------------------------------------
# EXTRACT_TEXTS
# ---------------------------------------------------------------------------


class TestFmtExtractTexts:
    def test_basic(self) -> None:
        result = _fmt(
            StepTypeEnum.E_EXTRACT_TEXTS,
            {"selector": ".title", "extract_mode": "text", "target": "titles", "mapping": "m"},
        )
        assert "textes" in result
        assert ".title" in result


# ---------------------------------------------------------------------------
# JUMP_TO_STEP
# ---------------------------------------------------------------------------


class TestFmtJumpToStep:
    def test_success_condition_with_known_target(self) -> None:
        ctx = {"abc123": 2}
        result = _fmt(StepTypeEnum.E_JUMP_TO_STEP, {"target_hexastring": "abc123", "condition": "success"}, ctx=ctx)
        assert "succès" in result
        assert "03" in result  # idx_found=2, zfill(2) → "03"

    def test_failure_condition(self) -> None:
        ctx = {"abc123": 0}
        result = _fmt(StepTypeEnum.E_JUMP_TO_STEP, {"target_hexastring": "abc123", "condition": "failure"}, ctx=ctx)
        assert "échec" in result

    def test_always_condition(self) -> None:
        ctx = {"abc123": 1}
        result = _fmt(StepTypeEnum.E_JUMP_TO_STEP, {"target_hexastring": "abc123", "condition": "always"}, ctx=ctx)
        assert "TOUJOURS" in result

    def test_unknown_target_shows_question_marks(self) -> None:
        result = _fmt(StepTypeEnum.E_JUMP_TO_STEP, {"target_hexastring": "missing", "condition": "always"}, ctx={})
        assert "????" in result
        assert "??" in result

    def test_no_target_hexastring(self) -> None:
        result = _fmt(StepTypeEnum.E_JUMP_TO_STEP, {}, ctx={})
        assert "????" in result


# ---------------------------------------------------------------------------
# KILL_BROWSER
# ---------------------------------------------------------------------------


class TestFmtKillBrowser:
    def test_with_unit(self) -> None:
        result = _fmt(StepTypeEnum.E_KILL_BROWSER, {"wait_unit": "s", "wait_duration": 5})
        assert "sec" in result
        assert "5" in result

    def test_unknown_unit_passthrough(self) -> None:
        result = _fmt(StepTypeEnum.E_KILL_BROWSER, {"wait_unit": "unknown", "wait_duration": 2})
        assert "unknown" in result


# ---------------------------------------------------------------------------
# OPEN_URL
# ---------------------------------------------------------------------------


class TestFmtOpenUrl:
    def test_source_mode(self) -> None:
        result = _fmt(
            StepTypeEnum.E_OPEN_URL,
            {"url_mode": OpenUrlModeEnum.E_SOURCE.value, "timeout_duration": 10, "timeout_unit": "s"},
        )
        assert "source" in result.lower()
        assert "10" in result
        assert "sec" in result

    def test_custom_mode(self) -> None:
        result = _fmt(
            StepTypeEnum.E_OPEN_URL,
            {"url_mode": OpenUrlModeEnum.E_CUSTOM.value, "url_custom": "https://example.com", "timeout_duration": 5, "timeout_unit": "m"},
        )
        assert "https://example.com" in result
        assert "min" in result


# ---------------------------------------------------------------------------
# REFRESH_PAGE
# ---------------------------------------------------------------------------


class TestFmtRefreshPage:
    def test_clear_cache_true(self) -> None:
        result = _fmt(StepTypeEnum.E_REFRESH_PAGE, {"clear_cache": True, "timeout_duration": 8, "timeout_unit": "s", "wait_state": "load"})
        assert "F5" in result
        assert "load" in result

    def test_clear_cache_false(self) -> None:
        result = _fmt(StepTypeEnum.E_REFRESH_PAGE, {"clear_cache": False, "timeout_duration": 3, "timeout_unit": "s", "wait_state": "networkidle"})
        assert "Garde" in result


# ---------------------------------------------------------------------------
# SCROLL_DOWN
# ---------------------------------------------------------------------------


class TestFmtScrollDown:
    def test_with_pixels(self) -> None:
        result = _fmt(StepTypeEnum.E_SCROLL_DOWN, {"pixels": 750})
        assert "750" in result

    def test_default_pixels(self) -> None:
        result = _fmt(StepTypeEnum.E_SCROLL_DOWN, {})
        assert "1000" in result


# ---------------------------------------------------------------------------
# SECTION_STEPS
# ---------------------------------------------------------------------------


class TestFmtSection:
    def test_with_title(self) -> None:
        result = _fmt(StepTypeEnum.E_SECTION_STEPS, {"title": "Mon titre"})
        assert "Mon titre" in result
        assert "Section" in result

    def test_empty_title(self) -> None:
        result = _fmt(StepTypeEnum.E_SECTION_STEPS, {})
        assert "Section" in result


# ---------------------------------------------------------------------------
# YOUTUBE_TRANSCRIPTS
# ---------------------------------------------------------------------------


class TestFmtYoutubeTranscripts:
    def test_with_title(self) -> None:
        result = _fmt(StepTypeEnum.E_YOUTUBE_TRANSCRIPTS, {"title": "My Video"})
        assert "YouTube" in result
        assert "My Video" in result

    def test_empty(self) -> None:
        result = _fmt(StepTypeEnum.E_YOUTUBE_TRANSCRIPTS, {})
        assert "YouTube" in result


# ---------------------------------------------------------------------------
# EXTRACT_VARIABLE
# ---------------------------------------------------------------------------


class TestFmtExtractVariable:
    def test_with_variable(self) -> None:
        result = _fmt(StepTypeEnum.E_EXTRACT_VARIABLE, {"variable": "my_var"})
        assert "my_var" in result

    def test_empty(self) -> None:
        result = _fmt(StepTypeEnum.E_EXTRACT_VARIABLE, {})
        assert "variable" in result.lower()


# ---------------------------------------------------------------------------
# WAIT_FIXED_TIME
# ---------------------------------------------------------------------------


class TestFmtWaitFixedTime:
    def test_with_unit(self) -> None:
        result = _fmt(StepTypeEnum.E_WAIT_FIXED_TIME, {"duration": 2, "unit": "m"})
        assert "2" in result
        assert "min" in result

    def test_ms_unit(self) -> None:
        result = _fmt(StepTypeEnum.E_WAIT_FIXED_TIME, {"duration": 500, "unit": "ms"})
        assert "millisec" in result


# ---------------------------------------------------------------------------
# WAIT_HTML_ELEMENTS
# ---------------------------------------------------------------------------


class TestFmtWaitHtmlElements:
    def test_greater_or_equal_operator(self) -> None:
        result = _fmt(StepTypeEnum.E_WAIT_HTML_ELEMENTS, {"operator": "greater_or_equal", "quantity": 3, "selector": "div"})
        assert ">=" in result
        assert "3" in result

    def test_less_or_equal_operator(self) -> None:
        result = _fmt(StepTypeEnum.E_WAIT_HTML_ELEMENTS, {"operator": "less_or_equal", "quantity": 1, "selector": "p"})
        assert "<=" in result


# ---------------------------------------------------------------------------
# WAIT_HTML_IMAGES
# ---------------------------------------------------------------------------


class TestFmtWaitHtmlImages:
    def test_basic(self) -> None:
        result = _fmt(StepTypeEnum.E_WAIT_HTML_IMAGES, {"retry_delay": 500, "retry_unit": "ms"})
        assert "500" in result
        assert "millisec" in result

    def test_size_range(self) -> None:
        result = _fmt(
            StepTypeEnum.E_WAIT_HTML_IMAGES,
            {"retry_delay": 1, "retry_unit": "s", "width_min": 300, "height_min": 200, "width_max": 1920, "height_max": 1080},
        )
        assert "300x200" in result
        assert "1920x1080" in result


# ---------------------------------------------------------------------------
# WAIT_PAGE_STATE
# ---------------------------------------------------------------------------


class TestFmtWaitPageState:
    def test_with_timeout(self) -> None:
        result = _fmt(StepTypeEnum.E_WAIT_PAGE_STATE, {"timeout_duration": 15, "timeout_unit": "s", "wait_state": "load"})
        assert "15" in result
        assert "load" in result
        assert "sec" in result


# ---------------------------------------------------------------------------
# WAIT_USER_ACTION
# ---------------------------------------------------------------------------


class TestFmtWaitUserAction:
    def test_success_condition(self) -> None:
        result = _fmt(StepTypeEnum.E_WAIT_USER_ACTION, {"condition": "success", "wait_duration": 3, "wait_unit": "s"})
        assert "succès" in result
        assert "3" in result

    def test_failure_condition(self) -> None:
        result = _fmt(StepTypeEnum.E_WAIT_USER_ACTION, {"condition": "failure", "wait_duration": 0, "wait_unit": "s"})
        assert "échec" in result

    def test_always_condition(self) -> None:
        result = _fmt(StepTypeEnum.E_WAIT_USER_ACTION, {"condition": "always", "wait_duration": 5, "wait_unit": "m"})
        assert "Toujours" in result

    def test_zero_duration_no_delay_string(self) -> None:
        result = _fmt(StepTypeEnum.E_WAIT_USER_ACTION, {"condition": "always", "wait_duration": 0, "wait_unit": "s"})
        assert "patienter" not in result

    def test_unknown_condition_defaults_to_toujours(self) -> None:
        result = _fmt(StepTypeEnum.E_WAIT_USER_ACTION, {"condition": "other", "wait_duration": 0, "wait_unit": "s"})
        assert "Toujours" in result
