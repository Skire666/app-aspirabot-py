"""Regression tests — supplemental view model and ValidationResult contracts.

Covers lines left uncovered after the initial view_models_integration_regression.py:
  - WorkflowViewModel: load_form(), clear_form(), snapshot(), remaining bind/action methods
  - ScenariosViewModel: bind_sort/sort, bind_open_folder, bind_refresh, grid_action routing
  - ProfilesViewModel: bind_sort/sort, grid_action routing
  - DebugViewModel: duplicate-bind guards, unbound action raises
  - LogViewModel: duplicate-bind guards, bound show_error/open_logs_folder
  - ValidationResult: compute_displayable_issues, has_issues, has_warnings, clear, extend
"""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest
from shared.enums import SeverityEnum
from shared.errors.launch_error import ErrorCodeLAM
from shared.errors.workflow_error import ErrorCodeWKF
from shared.exception_util import CallbackNotDefinedError
from shared.validation_result import ValidationIssue, ValidationResult
from view_models.debug_view_model import DebugViewModel
from view_models.log_view_model import LogViewModel
from view_models.profiles_view_model import ProfilesViewModel
from view_models.scenarios_view_model import ScenariosViewModel
from view_models.workflow_view_model import WorkflowFormViewState, WorkflowViewModel

# ===========================================================================
# ValidationResult — missing line coverage
# ===========================================================================


class TestValidationResultHasIssues:
    def test_has_issues_false_when_empty(self) -> None:
        vr = ValidationResult()
        assert vr.has_issues() is False

    def test_has_issues_true_after_append(self) -> None:
        vr = ValidationResult()
        vr.append(ErrorCodeLAM.LAM_1001, SeverityEnum.E_ERROR)
        assert vr.has_issues() is True


class TestValidationResultHasWarnings:
    def test_has_warnings_false_when_empty(self) -> None:
        vr = ValidationResult()
        assert vr.has_warnings() is False

    def test_has_warnings_true_after_warning(self) -> None:
        vr = ValidationResult()
        vr.append(ErrorCodeLAM.LAM_1001, SeverityEnum.E_WARNING)
        assert vr.has_warnings() is True

    def test_has_warnings_false_for_error_only(self) -> None:
        vr = ValidationResult()
        vr.append(ErrorCodeLAM.LAM_1001, SeverityEnum.E_ERROR)
        assert vr.has_warnings() is False


class TestValidationResultAppendFatal:
    def test_append_fatal_increments_count_fatals(self) -> None:
        vr = ValidationResult()
        vr.append(ErrorCodeLAM.LAM_1001, SeverityEnum.E_FATAL)
        assert vr.count_fatals == 1
        assert vr.count_errors == 0
        assert vr.count_warnings == 0

    def test_has_errors_or_fatals_true_for_fatal(self) -> None:
        vr = ValidationResult()
        vr.append(ErrorCodeLAM.LAM_1001, SeverityEnum.E_FATAL)
        assert vr.has_errors_or_fatals() is True


class TestValidationResultClear:
    def test_clear_resets_all_counters(self) -> None:
        vr = ValidationResult()
        vr.append(ErrorCodeLAM.LAM_1001, SeverityEnum.E_ERROR)
        vr.append(ErrorCodeLAM.LAM_1002, SeverityEnum.E_WARNING)
        vr.append(ErrorCodeLAM.LAM_1003, SeverityEnum.E_FATAL)
        vr.clear()
        assert vr.count_errors == 0
        assert vr.count_warnings == 0
        assert vr.count_fatals == 0
        assert vr.issues == []

    def test_clear_then_reuse(self) -> None:
        vr = ValidationResult()
        vr.append(ErrorCodeLAM.LAM_1001, SeverityEnum.E_ERROR)
        vr.clear()
        vr.append(ErrorCodeLAM.LAM_1002, SeverityEnum.E_WARNING)
        assert vr.count_errors == 0
        assert vr.count_warnings == 1


class TestValidationResultExtend:
    def test_extend_merges_issues_and_counters(self) -> None:
        vr1 = ValidationResult()
        vr1.append(ErrorCodeLAM.LAM_1001, SeverityEnum.E_ERROR)

        vr2 = ValidationResult()
        vr2.append(ErrorCodeLAM.LAM_1002, SeverityEnum.E_WARNING)

        vr1.extend(vr2)
        assert vr1.count_errors == 1
        assert vr1.count_warnings == 1
        assert len(vr1.issues) == 2

    def test_extend_empty_is_noop(self) -> None:
        vr = ValidationResult()
        vr.append(ErrorCodeLAM.LAM_1001, SeverityEnum.E_ERROR)
        vr.extend(ValidationResult())
        assert vr.count_errors == 1
        assert len(vr.issues) == 1


class TestValidationResultComputeDisplayable:
    def test_empty_returns_dash(self) -> None:
        vr = ValidationResult()
        assert vr.compute_displayable_issues() == "--"

    def test_single_error_appears_in_output(self) -> None:
        vr = ValidationResult()
        vr.append(ErrorCodeWKF.WKF_1001, SeverityEnum.E_ERROR)
        output = vr.compute_displayable_issues()
        assert "ERROR" in output

    def test_fatal_appears_before_error(self) -> None:
        vr = ValidationResult()
        vr.append(ErrorCodeWKF.WKF_1001, SeverityEnum.E_ERROR)
        vr.append(ErrorCodeWKF.WKF_1002, SeverityEnum.E_FATAL)
        output = vr.compute_displayable_issues(nbr_max=2)
        fatal_pos = output.find("FATAL")
        error_pos = output.find("ERROR")
        assert fatal_pos < error_pos, "FATAL issues must appear before ERROR issues"

    def test_warning_appears_after_errors(self) -> None:
        vr = ValidationResult()
        vr.append(ErrorCodeWKF.WKF_1001, SeverityEnum.E_WARNING)
        output = vr.compute_displayable_issues()
        assert "WARNING" in output

    def test_nbr_max_limits_output(self) -> None:
        vr = ValidationResult()
        for _ in range(5):
            vr.append(ErrorCodeWKF.WKF_1001, SeverityEnum.E_ERROR)
        output = vr.compute_displayable_issues(nbr_max=2)
        assert output.count("ERROR") == 2, "compute_displayable_issues must respect nbr_max"


class TestValidationIssueMessage:
    def test_message_formats_context(self) -> None:
        # The error code value must be a format-able string
        issue = ValidationIssue(code=ErrorCodeWKF.WKF_1001, severity=SeverityEnum.E_ERROR)
        msg = issue.message
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_message_fallback_on_missing_context(self) -> None:
        issue = ValidationIssue(code=ErrorCodeWKF.WKF_1001, severity=SeverityEnum.E_ERROR, context={"bad": "key"})
        # Should fall back to raw code.value without raising
        msg = issue.message
        assert isinstance(msg, str)


# ===========================================================================
# WorkflowViewModel — load_form, clear_form, snapshot, remaining binds
# ===========================================================================


@pytest.fixture()
def wf_vm(tk_root: tk.Tk) -> WorkflowViewModel:
    return WorkflowViewModel(master=tk_root)


class TestWorkflowViewModelLoadAndClear:
    def test_load_form_sets_all_vars(self, wf_vm: WorkflowViewModel) -> None:
        wf_vm.load_form("id_abc", "My Scenario", "My Description")
        assert wf_vm.id_file_var.get() == "id_abc"
        assert wf_vm.name_var.get() == "My Scenario"
        assert wf_vm.desc_var.get() == "My Description"

    def test_load_form_clears_dirty(self, wf_vm: WorkflowViewModel) -> None:
        wf_vm.is_dirty_var.set(True)
        wf_vm.load_form("id_abc", "Name", "Desc")
        assert wf_vm.is_dirty_var.get() is False, "load_form must clear is_dirty_var"

    def test_load_form_restores_is_loading_to_false(self, wf_vm: WorkflowViewModel) -> None:
        wf_vm.load_form("id", "n", "d")
        assert wf_vm.is_loading_var.get() is False, "load_form must reset is_loading to False after completion"

    def test_clear_form_empties_all_vars(self, wf_vm: WorkflowViewModel) -> None:
        wf_vm.load_form("id_abc", "Name", "Desc")
        wf_vm.clear_form()
        assert wf_vm.id_file_var.get() == ""
        assert wf_vm.name_var.get() == ""
        assert wf_vm.desc_var.get() == ""

    def test_clear_form_restores_is_loading_to_false(self, wf_vm: WorkflowViewModel) -> None:
        wf_vm.clear_form()
        assert wf_vm.is_loading_var.get() is False


class TestWorkflowViewModelSnapshot:
    def test_snapshot_reflects_current_vars(self, wf_vm: WorkflowViewModel) -> None:
        wf_vm.load_form("id_x", "Alpha", "Desc")
        snap = wf_vm.snapshot()
        assert isinstance(snap, WorkflowFormViewState)
        assert snap.id_file == "id_x"
        assert snap.scenario_name == "Alpha"
        assert snap.scenario_desc == "Desc"
        assert snap.is_dirty is False

    def test_snapshot_captures_dirty_true(self, wf_vm: WorkflowViewModel) -> None:
        wf_vm.is_dirty_var.set(True)
        snap = wf_vm.snapshot()
        assert snap.is_dirty is True


class TestWorkflowViewModelBindActions:
    def test_bind_show_error_and_dispatch(self, wf_vm: WorkflowViewModel) -> None:
        messages: list[str] = []
        wf_vm.bind_show_error(lambda m: messages.append(m))
        wf_vm.show_error("error message")
        assert messages == ["error message"]

    def test_bind_show_warning_and_dispatch(self, wf_vm: WorkflowViewModel) -> None:
        warnings: list[str] = []
        wf_vm.bind_show_warning(lambda m: warnings.append(m))
        wf_vm.show_warning("warning message")
        assert warnings == ["warning message"]

    def test_show_error_silent_when_unbound(self, wf_vm: WorkflowViewModel) -> None:
        wf_vm.show_error("test")  # must not raise

    def test_show_warning_silent_when_unbound(self, wf_vm: WorkflowViewModel) -> None:
        wf_vm.show_warning("test")  # must not raise

    def test_ask_overwrite_returns_false_when_unbound(self, wf_vm: WorkflowViewModel) -> None:
        assert wf_vm.ask_overwrite() is False

    def test_bind_ask_overwrite_and_dispatch(self, wf_vm: WorkflowViewModel) -> None:
        wf_vm.bind_ask_overwrite(lambda: True)
        assert wf_vm.ask_overwrite() is True

    def test_show_inline_form_silent_when_unbound(self, wf_vm: WorkflowViewModel) -> None:
        wf_vm.show_inline_form(None)  # must not raise

    def test_bind_show_inline_form_and_dispatch(self, wf_vm: WorkflowViewModel) -> None:
        received: list[object] = []
        wf_vm.bind_show_inline_form(lambda s: received.append(s))
        wf_vm.show_inline_form("step_data")
        assert received == ["step_data"]

    def test_duplicate_bind_show_error_raises(self, wf_vm: WorkflowViewModel) -> None:
        wf_vm.bind_show_error(lambda _: None)
        with pytest.raises(CallbackNotDefinedError):
            wf_vm.bind_show_error(lambda _: None)

    def test_duplicate_bind_show_warning_raises(self, wf_vm: WorkflowViewModel) -> None:
        wf_vm.bind_show_warning(lambda _: None)
        with pytest.raises(CallbackNotDefinedError):
            wf_vm.bind_show_warning(lambda _: None)

    def test_duplicate_bind_ask_overwrite_raises(self, wf_vm: WorkflowViewModel) -> None:
        wf_vm.bind_ask_overwrite(lambda: True)
        with pytest.raises(CallbackNotDefinedError):
            wf_vm.bind_ask_overwrite(lambda: True)

    def test_duplicate_bind_show_inline_form_raises(self, wf_vm: WorkflowViewModel) -> None:
        wf_vm.bind_show_inline_form(lambda _: None)
        with pytest.raises(CallbackNotDefinedError):
            wf_vm.bind_show_inline_form(lambda _: None)


# ===========================================================================
# ScenariosViewModel — remaining bind/action and grid_action
# ===========================================================================


@pytest.fixture()
def sc_vm(tk_root: tk.Tk) -> ScenariosViewModel:
    return ScenariosViewModel(master=tk_root)


class TestScenariosViewModelRemainingBinds:
    def test_bind_open_folder_and_dispatch(self, sc_vm: ScenariosViewModel) -> None:
        calls: list[bool] = []
        sc_vm.bind_open_folder(lambda: calls.append(True))
        sc_vm.open_folder()
        assert calls == [True]

    def test_bind_refresh_and_dispatch(self, sc_vm: ScenariosViewModel) -> None:
        calls: list[bool] = []
        sc_vm.bind_refresh(lambda: calls.append(True))
        sc_vm.refresh()
        assert calls == [True]

    def test_bind_sort_and_dispatch(self, sc_vm: ScenariosViewModel) -> None:
        received: list[tuple[str, bool]] = []
        sc_vm.bind_sort(lambda col, asc: received.append((col, asc)))
        sc_vm.sort("name", True)
        assert received == [("name", True)]

    def test_show_warning_dispatches_when_bound(self, sc_vm: ScenariosViewModel) -> None:
        warnings: list[str] = []
        sc_vm.bind_show_warning(lambda m: warnings.append(m))
        sc_vm.show_warning("oops")
        assert warnings == ["oops"]

    def test_show_error_dispatches_when_bound(self, sc_vm: ScenariosViewModel) -> None:
        errors: list[str] = []
        sc_vm.bind_show_error(lambda m: errors.append(m))
        sc_vm.show_error("fail")
        assert errors == ["fail"]

    def test_duplicate_bind_refresh_raises(self, sc_vm: ScenariosViewModel) -> None:
        sc_vm.bind_refresh(lambda: None)
        with pytest.raises(CallbackNotDefinedError):
            sc_vm.bind_refresh(lambda: None)

    def test_duplicate_bind_sort_raises(self, sc_vm: ScenariosViewModel) -> None:
        sc_vm.bind_sort(lambda c, a: None)
        with pytest.raises(CallbackNotDefinedError):
            sc_vm.bind_sort(lambda c, a: None)

    def test_duplicate_bind_open_folder_raises(self, sc_vm: ScenariosViewModel) -> None:
        sc_vm.bind_open_folder(lambda: None)
        with pytest.raises(CallbackNotDefinedError):
            sc_vm.bind_open_folder(lambda: None)

    def test_duplicate_bind_show_warning_raises(self, sc_vm: ScenariosViewModel) -> None:
        sc_vm.bind_show_warning(lambda _: None)
        with pytest.raises(CallbackNotDefinedError):
            sc_vm.bind_show_warning(lambda _: None)

    def test_duplicate_bind_show_error_raises(self, sc_vm: ScenariosViewModel) -> None:
        sc_vm.bind_show_error(lambda _: None)
        with pytest.raises(CallbackNotDefinedError):
            sc_vm.bind_show_error(lambda _: None)

    def test_unbound_open_folder_raises(self, sc_vm: ScenariosViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            sc_vm.open_folder()

    def test_unbound_refresh_raises(self, sc_vm: ScenariosViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            sc_vm.refresh()

    def test_unbound_sort_raises(self, sc_vm: ScenariosViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            sc_vm.sort("name", True)


class TestScenariosViewModelGridAction:
    def test_grid_action_launch_routes_to_launch(self, sc_vm: ScenariosViewModel) -> None:
        received: list[str] = []
        sc_vm.bind_launch(lambda s: received.append(s))
        sc_vm.grid_action("action_launch", "sc_abc")
        assert received == ["sc_abc"]

    def test_grid_action_edit_routes_to_edit(self, sc_vm: ScenariosViewModel) -> None:
        received: list[str] = []
        sc_vm.bind_edit(lambda s: received.append(s))
        sc_vm.grid_action("action_edit", "sc_abc")
        assert received == ["sc_abc"]

    def test_grid_action_duplicate_routes_to_duplicate(self, sc_vm: ScenariosViewModel) -> None:
        received: list[str] = []
        sc_vm.bind_duplicate(lambda s: received.append(s))
        sc_vm.grid_action("action_duplicate", "sc_abc")
        assert received == ["sc_abc"]

    def test_grid_action_delete_routes_to_delete(self, sc_vm: ScenariosViewModel) -> None:
        received: list[str] = []
        sc_vm.bind_delete(lambda s: received.append(s))
        sc_vm.grid_action("action_delete", "sc_abc")
        assert received == ["sc_abc"]

    def test_grid_action_unknown_does_nothing(self, sc_vm: ScenariosViewModel) -> None:
        sc_vm.grid_action("unknown_action", "sc_abc")  # must not raise


# ===========================================================================
# ProfilesViewModel — bind_sort, sort, grid_action routing
# ===========================================================================


@pytest.fixture()
def pr_vm(tk_root: tk.Tk) -> ProfilesViewModel:
    return ProfilesViewModel(master=tk_root)


class TestProfilesViewModelRemainingBinds:
    def test_bind_sort_and_dispatch(self, pr_vm: ProfilesViewModel) -> None:
        received: list[tuple[str, bool]] = []
        pr_vm.bind_sort(lambda col, asc: received.append((col, asc)))
        pr_vm.sort("name", False)
        assert received == [("name", False)]

    def test_duplicate_bind_sort_raises(self, pr_vm: ProfilesViewModel) -> None:
        pr_vm.bind_sort(lambda c, a: None)
        with pytest.raises(CallbackNotDefinedError):
            pr_vm.bind_sort(lambda c, a: None)

    def test_unbound_sort_raises(self, pr_vm: ProfilesViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            pr_vm.sort("col", True)

    def test_grid_action_launch_routes_to_launch_profile(self, pr_vm: ProfilesViewModel) -> None:
        received: list[tuple[str, str]] = []
        pr_vm.bind_launch(lambda s, p: received.append((s, p)))

        bound = MagicMock()
        bound.id_scenario = "sc_abc"
        bound.id_profile = "p_xyz"
        bound.profile_name = "My Profile"
        pr_vm.grid_action("action_launch", bound)
        assert received == [("sc_abc", "p_xyz")]

    def test_grid_action_delete_routes_to_delete_profile(self, pr_vm: ProfilesViewModel) -> None:
        received: list[tuple[str, str, str]] = []
        pr_vm.bind_delete(lambda s, p, n: received.append((s, p, n)))

        bound = MagicMock()
        bound.id_scenario = "sc_abc"
        bound.id_profile = "p_xyz"
        bound.profile_name = "My Profile"
        pr_vm.grid_action("action_delete", bound)
        assert received == [("sc_abc", "p_xyz", "My Profile")]

    def test_grid_action_unknown_does_nothing(self, pr_vm: ProfilesViewModel) -> None:
        bound = MagicMock()
        pr_vm.grid_action("unknown", bound)  # must not raise


# ===========================================================================
# DebugViewModel — duplicate-bind guards and unbound raises
# ===========================================================================


@pytest.fixture()
def debug_vm(tk_root: tk.Tk) -> DebugViewModel:
    return DebugViewModel(master=tk_root)


class TestDebugViewModelBindGuards:
    def test_duplicate_bind_start_raises(self, debug_vm: DebugViewModel) -> None:
        debug_vm.bind_start(lambda u, t, d, w: None)
        with pytest.raises(CallbackNotDefinedError):
            debug_vm.bind_start(lambda u, t, d, w: None)

    def test_duplicate_bind_open_debug_page_raises(self, debug_vm: DebugViewModel) -> None:
        debug_vm.bind_open_debug_page(lambda: None)
        with pytest.raises(CallbackNotDefinedError):
            debug_vm.bind_open_debug_page(lambda: None)

    def test_duplicate_bind_refresh_raises(self, debug_vm: DebugViewModel) -> None:
        debug_vm.bind_refresh(lambda: None)
        with pytest.raises(CallbackNotDefinedError):
            debug_vm.bind_refresh(lambda: None)

    def test_duplicate_bind_analyze_texts_raises(self, debug_vm: DebugViewModel) -> None:
        debug_vm.bind_analyze_texts(lambda s: None)
        with pytest.raises(CallbackNotDefinedError):
            debug_vm.bind_analyze_texts(lambda s: None)

    def test_duplicate_bind_analyze_images_raises(self, debug_vm: DebugViewModel) -> None:
        debug_vm.bind_analyze_images(lambda s: None)
        with pytest.raises(CallbackNotDefinedError):
            debug_vm.bind_analyze_images(lambda s: None)

    def test_duplicate_bind_close_raises(self, debug_vm: DebugViewModel) -> None:
        debug_vm.bind_close(lambda: None)
        with pytest.raises(CallbackNotDefinedError):
            debug_vm.bind_close(lambda: None)


class TestDebugViewModelUnboundRaises:
    def test_unbound_start_raises(self, debug_vm: DebugViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            debug_vm.start("url", "30", "0", "load")

    def test_unbound_open_debug_page_raises(self, debug_vm: DebugViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            debug_vm.open_debug_page()

    def test_unbound_refresh_raises(self, debug_vm: DebugViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            debug_vm.refresh()

    def test_unbound_analyze_texts_raises(self, debug_vm: DebugViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            debug_vm.analyze_texts(".sel")

    def test_unbound_analyze_images_raises(self, debug_vm: DebugViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            debug_vm.analyze_images(".img")

    def test_unbound_close_raises(self, debug_vm: DebugViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            debug_vm.close()

    def test_bound_close_dispatches(self, debug_vm: DebugViewModel) -> None:
        calls: list[bool] = []
        debug_vm.bind_close(lambda: calls.append(True))
        debug_vm.close()
        assert calls == [True]

    def test_bound_refresh_dispatches(self, debug_vm: DebugViewModel) -> None:
        calls: list[bool] = []
        debug_vm.bind_refresh(lambda: calls.append(True))
        debug_vm.refresh()
        assert calls == [True]

    def test_bound_analyze_texts_dispatches(self, debug_vm: DebugViewModel) -> None:
        received: list[str] = []
        debug_vm.bind_analyze_texts(lambda s: received.append(s))
        debug_vm.analyze_texts(".headline")
        assert received == [".headline"]

    def test_master_property(self, debug_vm: DebugViewModel) -> None:
        assert debug_vm.master is not None


# ===========================================================================
# LogViewModel — duplicate-bind guards and bound dispatches
# ===========================================================================


@pytest.fixture()
def log_vm2(tk_root: tk.Tk) -> LogViewModel:
    return LogViewModel(master=tk_root)


class TestLogViewModelMissingCoverage:
    def test_duplicate_bind_show_error_raises(self, log_vm2: LogViewModel) -> None:
        log_vm2.bind_show_error(lambda t, m: None)
        with pytest.raises(CallbackNotDefinedError):
            log_vm2.bind_show_error(lambda t, m: None)

    def test_duplicate_bind_open_logs_folder_raises(self, log_vm2: LogViewModel) -> None:
        log_vm2.bind_open_logs_folder(lambda: None)
        with pytest.raises(CallbackNotDefinedError):
            log_vm2.bind_open_logs_folder(lambda: None)

    def test_bound_show_error_dispatches(self, log_vm2: LogViewModel) -> None:
        received: list[tuple[str, str]] = []
        log_vm2.bind_show_error(lambda t, m: received.append((t, m)))
        log_vm2.show_error("Title", "Message")
        assert received == [("Title", "Message")]

    def test_unbound_open_logs_folder_raises(self, log_vm2: LogViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            log_vm2.open_logs_folder()

    def test_bound_open_logs_folder_dispatches(self, log_vm2: LogViewModel) -> None:
        calls: list[bool] = []
        log_vm2.bind_open_logs_folder(lambda: calls.append(True))
        log_vm2.open_logs_folder()
        assert calls == [True]


# ===========================================================================
# ValidationIssue — except branch (lines 31-32 of validation_result.py)
# ===========================================================================


class TestValidationIssueFallbackMessage:
    def test_message_falls_back_when_format_key_missing(self) -> None:
        from unittest.mock import MagicMock

        mock_code = MagicMock()
        mock_code.value = "Error: {missing_placeholder} required"
        issue = ValidationIssue(code=mock_code, severity=SeverityEnum.E_ERROR, context={})
        msg = issue.message
        assert msg == "Error: {missing_placeholder} required"


# ===========================================================================
# ScenariosViewModel — coverage gap: get_folder_path, duplicate-bind guards,
# and unbound-action raises for edit/duplicate/launch/delete/validate
# ===========================================================================


class TestScenariosViewModelCoverageGap:

    def test_duplicate_bind_edit_raises(self, sc_vm: ScenariosViewModel) -> None:
        sc_vm.bind_edit(lambda _: None)
        with pytest.raises(CallbackNotDefinedError):
            sc_vm.bind_edit(lambda _: None)

    def test_duplicate_bind_duplicate_raises(self, sc_vm: ScenariosViewModel) -> None:
        sc_vm.bind_duplicate(lambda _: None)
        with pytest.raises(CallbackNotDefinedError):
            sc_vm.bind_duplicate(lambda _: None)

    def test_duplicate_bind_launch_raises(self, sc_vm: ScenariosViewModel) -> None:
        sc_vm.bind_launch(lambda _: None)
        with pytest.raises(CallbackNotDefinedError):
            sc_vm.bind_launch(lambda _: None)

    def test_duplicate_bind_delete_raises(self, sc_vm: ScenariosViewModel) -> None:
        sc_vm.bind_delete(lambda _: None)
        with pytest.raises(CallbackNotDefinedError):
            sc_vm.bind_delete(lambda _: None)

    def test_unbound_edit_raises(self, sc_vm: ScenariosViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            sc_vm.edit("abc123")

    def test_unbound_duplicate_raises(self, sc_vm: ScenariosViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            sc_vm.duplicate("abc123")

    def test_unbound_launch_raises(self, sc_vm: ScenariosViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            sc_vm.launch("abc123")

    def test_unbound_delete_raises(self, sc_vm: ScenariosViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            sc_vm.delete("abc123")



# ===========================================================================
# ProfilesViewModel — coverage gap: duplicate-bind guards and unbound-action
# raises for launch_profile, delete_profile, open_folder
# ===========================================================================


class TestProfilesViewModelCoverageGap:
    def test_duplicate_bind_launch_raises(self, pr_vm: ProfilesViewModel) -> None:
        pr_vm.bind_launch(lambda s, p: None)
        with pytest.raises(CallbackNotDefinedError):
            pr_vm.bind_launch(lambda s, p: None)

    def test_duplicate_bind_delete_raises(self, pr_vm: ProfilesViewModel) -> None:
        pr_vm.bind_delete(lambda s, p, n: None)
        with pytest.raises(CallbackNotDefinedError):
            pr_vm.bind_delete(lambda s, p, n: None)

    def test_duplicate_bind_open_folder_raises(self, pr_vm: ProfilesViewModel) -> None:
        pr_vm.bind_open_folder(lambda: None)
        with pytest.raises(CallbackNotDefinedError):
            pr_vm.bind_open_folder(lambda: None)

    def test_unbound_launch_profile_raises(self, pr_vm: ProfilesViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            pr_vm.launch_profile("sc_abc", "p_xyz")

    def test_unbound_delete_profile_raises(self, pr_vm: ProfilesViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            pr_vm.delete_profile("sc_abc", "p_xyz")

    def test_unbound_open_folder_raises(self, pr_vm: ProfilesViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            pr_vm.open_folder()
