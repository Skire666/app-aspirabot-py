"""Tests for services/browser_playwright_service.py — crash and freeze detection."""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest
from playwright.sync_api import Page
from services.browser_playwright_service import BrowserPlaywrightService
from shared.enums import SeverityEnum
from shared.errors.browser_playwright_error import ErrorCodeBRP
from shared.validation_result import ValidationResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service() -> BrowserPlaywrightService:
    return BrowserPlaywrightService(chromium_persistant_dir="C:/tmp/profile", chromium_extensions_dir="C:/tmp/ext")


def _make_page(url: str = "https://example.test/") -> MagicMock:
    page = MagicMock(spec=Page)
    page.url = url
    return page


# ---------------------------------------------------------------------------
# launch() — crash listener wiring
# ---------------------------------------------------------------------------


class TestLaunchWiresCrashListener:
    def test_registers_page_event_and_wires_existing_pages(self) -> None:
        svc = _make_service()
        existing_page = _make_page()
        cdp_context = MagicMock()
        cdp_context.pages = [existing_page]
        cdp_browser = MagicMock()
        cdp_browser.contexts = [cdp_context]
        pw = MagicMock()
        pw.chromium.connect_over_cdp.return_value = cdp_browser

        with patch("services.browser_playwright_service.sync_playwright") as mock_sync_pw:
            mock_sync_pw.return_value.start.return_value = pw
            svc.launch()

        cdp_context.on.assert_called_once_with("page", svc._wire_page_crash_listener)
        existing_page.on.assert_called_once_with("crash", svc._on_page_crash)


# ---------------------------------------------------------------------------
# _on_page_crash
# ---------------------------------------------------------------------------


class TestOnPageCrash:
    def test_logs_immediately_and_sets_crash_signal(self) -> None:
        svc = _make_service()
        page = _make_page("https://crash.test/")

        with patch.object(svc._logger, "error") as mock_error:
            svc._on_page_crash(page)

        assert svc._crash_event.is_set()
        assert svc._crash_count == 1
        mock_error.assert_called_once()
        logged_args = mock_error.call_args.args
        assert "https://crash.test/" in logged_args
        assert 1 in logged_args

    def test_occurrence_counter_increments_and_appears_in_log(self) -> None:
        svc = _make_service()
        page = _make_page()

        with patch.object(svc._logger, "error") as mock_error:
            svc._on_page_crash(page)
            svc._on_page_crash(page)

        assert svc._crash_count == 2
        assert mock_error.call_args_list[-1].args[-1] == 2

    def test_survives_page_url_access_failure(self) -> None:
        svc = _make_service()
        page = MagicMock(spec=Page)
        type(page).url = property(lambda _self: (_ for _ in ()).throw(RuntimeError("gone")))

        svc._on_page_crash(page)  # must not raise

        assert svc._crash_event.is_set()


# ---------------------------------------------------------------------------
# _apply_goto_error_recovery — crash branch
# ---------------------------------------------------------------------------


class TestApplyGotoErrorRecoveryCrashBranch:
    def test_recovers_by_opening_a_new_page_and_appends_warning(self) -> None:
        svc = _make_service()
        svc._workflow_page = _make_page()
        svc._last_error = ValidationResult()
        svc._crash_event.set()

        with patch.object(svc, "get_workflow_page") as mock_get_page:
            svc._apply_goto_error_recovery("some unrelated message", wait_dns_solver_sec=5)

        mock_get_page.assert_called_once_with(forced_new_page=True)
        assert not svc._crash_event.is_set()
        assert svc._last_error.count_severities_by_code(ErrorCodeBRP.BRP_1007) == 1
        assert svc._last_error.count_severities(SeverityEnum.E_WARNING) == 1

    def test_no_recovery_action_when_no_crash_signaled(self) -> None:
        svc = _make_service()
        svc._workflow_page = _make_page()
        svc._last_error = ValidationResult()

        with patch.object(svc, "get_workflow_page") as mock_get_page:
            svc._apply_goto_error_recovery("unrelated", wait_dns_solver_sec=5)

        mock_get_page.assert_not_called()
        assert svc._last_error.count_issues() == 0


# ---------------------------------------------------------------------------
# _freeze_watchdog / has_pending_freeze_signal
# ---------------------------------------------------------------------------


class TestFreezeWatchdog:
    def test_flags_and_logs_when_block_exceeds_timeout(self) -> None:
        svc = _make_service()

        with (
            patch("services.browser_playwright_service._FREEZE_TIMEOUT_SEC", 0.05),
            patch.object(svc._logger, "error") as mock_error,
            svc._freeze_watchdog("op-under-test"),
        ):
            svc._freeze_event.wait(timeout=1)

        assert svc.has_pending_freeze_signal()
        assert mock_error.call_args is not None
        assert "op-under-test" in mock_error.call_args.args

    def test_does_not_flag_when_block_completes_quickly(self) -> None:
        svc = _make_service()

        with patch("services.browser_playwright_service._FREEZE_TIMEOUT_SEC", 5), svc._freeze_watchdog("fast-op"):
            pass

        assert not svc.has_pending_freeze_signal()

    def test_clear_freeze_signal_resets_flag(self) -> None:
        svc = _make_service()
        svc._freeze_event.set()

        svc.clear_freeze_signal()

        assert not svc.has_pending_freeze_signal()


# ---------------------------------------------------------------------------
# evaluate_script_with_safe_retry — crash recovery mid-retry
# ---------------------------------------------------------------------------


class TestEvaluateScriptWithSafeRetryCrashRecovery:
    def test_opens_new_page_and_retries_after_crash(self) -> None:
        svc = _make_service()
        crashed_page = _make_page("https://before-crash.test/")
        fresh_page = _make_page("https://after-crash.test/")

        def _evaluate_side_effect(_script: str) -> object:
            svc._crash_event.set()
            raise RuntimeError("Page crashed")

        crashed_page.evaluate.side_effect = _evaluate_side_effect
        fresh_page.evaluate.return_value = "ok"

        with (
            patch.object(svc, "get_workflow_page", side_effect=[crashed_page, fresh_page]) as mock_get_page,
            patch("services.browser_playwright_service._FREEZE_TIMEOUT_SEC", 5),
        ):
            is_success, result = svc.evaluate_script_with_safe_retry("1+1", retries=2, delay=0)

        assert is_success is True
        assert result == "ok"
        assert mock_get_page.call_args_list[-1] == call(forced_new_page=True)
        assert not svc._crash_event.is_set()
        fresh_page.evaluate.assert_called_once_with("1+1")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
