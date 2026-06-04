"""Additional tests for executor_presenter.py — branches not covered by the base file.

Covers lines 212-214, 229, 333-336, 377-383, 391-392, 403, 407-416, 428-431,
438-448, 451-458, 461-471, 474-486, 490-498, 506-510, 513-514, 529-535, 543-548,
552-559, 563-569.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from models.launcher_model import LaunchModel
from models.profiles_list_model import ProfilesModel
from models.scenario_model import ScenarioModel
from presenters.executor_presenter import ExecutorPresenter
from services.profiles_service import ProfilesService
from services.scenarios_service import ScenariosService
from shared.enums import UrlSortOrderEnum, UrlSourceTypeEnum
from shared.exception_util import CallbackNotDefinedError
from shared.i18n_fra import C_EXEC_NO_PROFILE, C_EXEC_NO_SCENARIO

# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def _make_presenter() -> tuple[ExecutorPresenter, MagicMock, MagicMock, MagicMock]:
    vm = MagicMock()
    svc_scen = MagicMock(spec=ScenariosService)
    svc_prof = MagicMock(spec=ProfilesService)
    p = ExecutorPresenter(vm=vm, scenarios_service=svc_scen, profiles_service=svc_prof)
    return p, vm, svc_scen, svc_prof


def _make_scenario(id_file: str = "sc001") -> ScenarioModel:
    s = ScenarioModel.get_default_data()
    s.id_file = id_file
    s.scenario_name = "Test Scenario"
    return s


def _make_profile(id_scenario: str = "sc001") -> LaunchModel:
    return LaunchModel.get_default(id_scenario)


def _make_profiles_model(id_scenario: str = "sc001") -> ProfilesModel:
    return ProfilesModel.get_default(id_scenario)


def _setup_vm_for_apply(vm: MagicMock) -> None:
    """Configure VM mock vars so _apply_form_to_profile produces deterministic values."""
    vm.export_folder_var.get.return_value = "/tmp/export"
    vm.url_source_type_var.get.return_value = UrlSourceTypeEnum.E_MANUAL.value
    vm.manual_urls_var.get.return_value = ""
    vm.url_source_path_var.get.return_value = ""
    vm.url_sort_order_var.get.return_value = UrlSortOrderEnum.E_MTIME_ASC.value
    vm.step_id_selected_var.get.return_value = "step001"
    vm.global_threshold_var.get.return_value = "10"
    vm.step_threshold_var.get.return_value = "5"


# ---------------------------------------------------------------------------
# Lines 212-214: _fetch_or_create_profiles — empty profiles list
# ---------------------------------------------------------------------------


class TestFetchOrCreateProfilesEmptyList:
    def test_empty_list_triggers_default_profile_creation(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        scenario = _make_scenario()
        presenter._current_scenario = scenario

        profiles_model = _make_profiles_model()
        profiles_model.launch_profiles = []
        default = _make_profile()

        svc_prof.read_profiles.side_effect = [profiles_model, profiles_model]
        svc_prof.create_profile_launch.return_value = default

        result = presenter._fetch_or_create_profiles("sc001")

        svc_prof.create_profile_launch.assert_called_once_with("sc001", "Profil par défaut")
        assert result == []


# ---------------------------------------------------------------------------
# Line 229: _select_best_profile — no best profile → _clear_profile_form
# ---------------------------------------------------------------------------


class TestSelectBestProfileNoBest:
    def test_no_best_profile_clears_current_profile(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        profiles_model = MagicMock()
        profiles_model.get_most_recently_used_profile.return_value = None
        presenter._current_profiles_model = profiles_model

        presenter._select_best_profile([_make_profile()])

        assert presenter._current_profile is None


# ---------------------------------------------------------------------------
# Lines 333-336: _push_url_source_vars — manual URL source branch
# ---------------------------------------------------------------------------


class TestPushUrlSourceVarsManual:
    def test_list_value_joins_with_newline_and_sets_preview(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        profile = _make_profile()
        profile.url_source_type = UrlSourceTypeEnum.E_MANUAL.value
        profile.url_source_value = ["http://a.com", "http://b.com"]

        presenter._push_url_source_vars(profile)

        vm.manual_urls_var.set.assert_called_with("http://a.com\nhttp://b.com")
        vm.set_url_preview.assert_called_with(["http://a.com", "http://b.com"])

    def test_non_list_value_yields_empty_preview(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        profile = _make_profile()
        profile.url_source_type = UrlSourceTypeEnum.E_MANUAL.value
        profile.url_source_value = "not_a_list"

        presenter._push_url_source_vars(profile)

        vm.manual_urls_var.set.assert_called_with("")
        vm.set_url_preview.assert_called_with([])


# ---------------------------------------------------------------------------
# Lines 377-383: _clear_profile_form
# ---------------------------------------------------------------------------


class TestClearProfileForm:
    def test_resets_current_profile_and_all_vm_vars(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        presenter._current_profile = _make_profile()

        presenter._clear_profile_form()

        assert presenter._current_profile is None
        vm.current_profile_name_var.set.assert_called_with("")
        vm.export_folder_var.set.assert_called_with("")
        vm.is_profile_section_enabled_var.set.assert_called_with(False)
        vm.is_rename_btn_enabled_var.set.assert_called_with(False)
        vm.is_delete_btn_enabled_var.set.assert_called_with(False)
        vm.is_save_btn_enabled_var.set.assert_called_with(False)


# ---------------------------------------------------------------------------
# Lines 391-392: _refresh_url_preview_from_form
# ---------------------------------------------------------------------------


class TestRefreshUrlPreviewFromForm:
    def test_delegates_to_update_url_preview_using_vm_state(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        vm.url_source_type_var.get.return_value = ""
        vm.url_sort_order_var.get.return_value = UrlSortOrderEnum.E_MTIME_ASC.value
        vm.url_source_path_var.get.return_value = ""

        presenter._refresh_url_preview_from_form()

        vm.set_url_preview.assert_called_with([])


# ---------------------------------------------------------------------------
# Lines 403, 407-416: _update_url_preview — all branches
# ---------------------------------------------------------------------------


class TestUpdateUrlPreview:
    def test_manual_type_returns_early_without_setting_preview(self) -> None:
        presenter, vm, _, _ = _make_presenter()

        presenter._update_url_preview(UrlSourceTypeEnum.E_MANUAL.value, ["url1"], "mtime_asc")

        vm.set_url_preview.assert_not_called()

    def test_unknown_type_sets_empty_preview(self) -> None:
        presenter, vm, _, _ = _make_presenter()

        presenter._update_url_preview("TOTALLY_UNKNOWN", "somepath", "mtime_asc")

        vm.set_url_preview.assert_called_with([])

    def test_folder_with_none_value_sets_empty_preview(self) -> None:
        presenter, vm, _, _ = _make_presenter()

        presenter._update_url_preview(UrlSourceTypeEnum.E_FOLDER.value, None, "mtime_asc")

        vm.set_url_preview.assert_called_with([])

    def test_folder_with_list_value_sets_empty_preview(self) -> None:
        presenter, vm, _, _ = _make_presenter()

        presenter._update_url_preview(UrlSourceTypeEnum.E_FOLDER.value, ["list_not_str"], "mtime_asc")

        vm.set_url_preview.assert_called_with([])

    def test_folder_with_valid_path_calls_provider_and_sets_urls(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        provider = MagicMock()
        provider.preview_url_listed.return_value = ["http://x.com"]

        with patch("presenters.executor_presenter.build_url_source_scenario", return_value=provider) as mock_build:
            presenter._update_url_preview(UrlSourceTypeEnum.E_FOLDER.value, "/some/path", "mtime_asc")

        mock_build.assert_called_once()
        vm.set_url_preview.assert_called_with(["http://x.com"])

    def test_provider_error_sets_empty_preview(self) -> None:
        presenter, vm, _, _ = _make_presenter()

        with patch("presenters.executor_presenter.build_url_source_scenario", side_effect=CallbackNotDefinedError()):
            presenter._update_url_preview(UrlSourceTypeEnum.E_FOLDER.value, "/some/path", "mtime_asc")

        vm.set_url_preview.assert_called_with([])


# ---------------------------------------------------------------------------
# Lines 428-431: _parse_sort_order (static)
# ---------------------------------------------------------------------------


class TestParseSortOrder:
    def test_valid_value_returns_matching_member(self) -> None:
        assert ExecutorPresenter._parse_sort_order("name_asc") == UrlSortOrderEnum.E_NAME_ASC
        assert ExecutorPresenter._parse_sort_order("mtime_desc") == UrlSortOrderEnum.E_MTIME_DESC

    def test_invalid_value_returns_default_mtime_asc(self) -> None:
        assert ExecutorPresenter._parse_sort_order("totally_invalid") == UrlSortOrderEnum.E_MTIME_ASC

    def test_empty_string_returns_default(self) -> None:
        assert ExecutorPresenter._parse_sort_order("") == UrlSortOrderEnum.E_MTIME_ASC


# ---------------------------------------------------------------------------
# Lines 438-448: _on_new_profile
# ---------------------------------------------------------------------------


class TestOnNewProfile:
    def test_no_scenario_returns_early(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        presenter._current_scenario = None

        presenter._on_new_profile("New Profile")

        svc_prof.create_profile_launch.assert_not_called()

    def test_creates_and_selects_new_profile(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        scenario = _make_scenario()
        presenter._current_scenario = scenario

        new_profile = _make_profile()
        profiles_model = _make_profiles_model()
        profiles_model.launch_profiles = [new_profile]

        svc_prof.create_profile_launch.return_value = new_profile
        svc_prof.read_profiles.return_value = profiles_model

        presenter._on_new_profile("New Profile")

        svc_prof.create_profile_launch.assert_called_once_with(scenario.id_file, "New Profile")
        vm.set_profiles.assert_called()

    def test_service_error_returns_early(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        presenter._current_scenario = _make_scenario()
        svc_prof.create_profile_launch.side_effect = CallbackNotDefinedError()

        presenter._on_new_profile("Broken Profile")

        vm.set_profiles.assert_not_called()


# ---------------------------------------------------------------------------
# Lines 451-458: _on_rename_profile
# ---------------------------------------------------------------------------


class TestOnRenameProfile:
    def test_no_profile_returns_early(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        presenter._current_profile = None

        presenter._on_rename_profile("New Name")

        svc_prof.update_profile_launch.assert_not_called()

    def test_same_name_is_no_op(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        profile = _make_profile()
        profile.profile_name = "Same"
        presenter._current_profile = profile

        presenter._on_rename_profile("Same")

        svc_prof.update_profile_launch.assert_not_called()
        assert presenter._is_dirty is False

    def test_different_name_renames_and_saves(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        scenario = _make_scenario()
        profile = _make_profile()
        profile.profile_name = "Old"
        profiles_model = _make_profiles_model()
        profiles_model.launch_profiles = [profile]

        presenter._current_scenario = scenario
        presenter._current_profile = profile
        presenter._current_profiles_model = profiles_model

        svc_prof.update_profile_launch.return_value = None
        svc_prof.read_profiles.return_value = profiles_model
        _setup_vm_for_apply(vm)

        presenter._on_rename_profile("New Name")

        assert profile.profile_name == "New Name"
        vm.current_profile_name_var.set.assert_called_with("New Name")
        svc_prof.update_profile_launch.assert_called_once()


# ---------------------------------------------------------------------------
# Lines 461-471: _on_delete_profile
# ---------------------------------------------------------------------------


class TestOnDeleteProfile:
    def test_no_profile_returns_early(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        presenter._current_profile = None
        presenter._current_scenario = _make_scenario()

        presenter._on_delete_profile()

        svc_prof.delete_profile_launch.assert_not_called()

    def test_no_scenario_returns_early(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        presenter._current_profile = _make_profile()
        presenter._current_scenario = None

        presenter._on_delete_profile()

        svc_prof.delete_profile_launch.assert_not_called()

    def test_deletes_profile_and_clears_form(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        scenario = _make_scenario()
        profile = _make_profile()
        profiles_model = _make_profiles_model()
        profiles_model.launch_profiles = []

        presenter._current_scenario = scenario
        presenter._current_profile = profile
        presenter._current_profiles_model = profiles_model

        svc_prof.delete_profile_launch.return_value = None
        svc_prof.read_profiles.return_value = profiles_model

        presenter._on_delete_profile()

        svc_prof.delete_profile_launch.assert_called_once_with(scenario.id_file, profile.id_profile)
        assert presenter._current_profile is None

    def test_service_error_returns_early(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        presenter._current_scenario = _make_scenario()
        presenter._current_profile = _make_profile()
        svc_prof.delete_profile_launch.side_effect = CallbackNotDefinedError()

        presenter._on_delete_profile()

        vm.set_profiles.assert_not_called()


# ---------------------------------------------------------------------------
# Lines 474-486: _on_save_profile
# ---------------------------------------------------------------------------


class TestOnSaveProfile:
    def test_no_profile_returns_early(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        presenter._current_profile = None
        presenter._current_scenario = _make_scenario()

        presenter._on_save_profile()

        svc_prof.update_profile_launch.assert_not_called()

    def test_no_scenario_returns_early(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        presenter._current_profile = _make_profile()
        presenter._current_scenario = None

        presenter._on_save_profile()

        svc_prof.update_profile_launch.assert_not_called()

    def test_saves_profile_and_clears_dirty_flag(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        scenario = _make_scenario()
        profile = _make_profile()
        profiles_model = _make_profiles_model()
        profiles_model.launch_profiles = [profile]

        presenter._current_scenario = scenario
        presenter._current_profile = profile
        presenter._current_profiles_model = profiles_model
        presenter._is_dirty = True

        svc_prof.update_profile_launch.return_value = None
        svc_prof.read_profiles.return_value = profiles_model
        _setup_vm_for_apply(vm)

        presenter._on_save_profile()

        svc_prof.update_profile_launch.assert_called_once_with(scenario.id_file, profile)
        assert presenter._is_dirty is False

    def test_service_error_shows_error_dialog(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        presenter._current_scenario = _make_scenario()
        presenter._current_profile = _make_profile()
        svc_prof.update_profile_launch.side_effect = CallbackNotDefinedError()
        _setup_vm_for_apply(vm)

        presenter._on_save_profile()

        vm.show_error.assert_called_once()


# ---------------------------------------------------------------------------
# Lines 490-498: _apply_form_to_profile
# ---------------------------------------------------------------------------


class TestApplyFormToProfile:
    def test_no_profile_returns_early_without_error(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        presenter._current_profile = None

        presenter._apply_form_to_profile()  # should not raise

    def test_writes_all_vm_vars_to_profile(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        profile = _make_profile()
        presenter._current_profile = profile
        _setup_vm_for_apply(vm)

        presenter._apply_form_to_profile()

        assert profile.export_folder == "/tmp/export"
        assert profile.url_source_type == UrlSourceTypeEnum.E_MANUAL.value
        assert profile.emergency_stop_threshold == 10
        assert profile.emergency_stop_step_threshold == 5
        assert profile.emergency_stop_step_id == "step001"


# ---------------------------------------------------------------------------
# Lines 506-510: _read_url_source_value_from_vm
# ---------------------------------------------------------------------------


class TestReadUrlSourceValueFromVm:
    def test_manual_parses_multiline_url_list(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        vm.url_source_type_var.get.return_value = UrlSourceTypeEnum.E_MANUAL.value
        vm.manual_urls_var.get.return_value = "  http://a.com  \n  http://b.com  \n"

        result = presenter._read_url_source_value_from_vm()

        assert result == ["http://a.com", "http://b.com"]

    def test_manual_blank_input_returns_empty_list(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        vm.url_source_type_var.get.return_value = UrlSourceTypeEnum.E_MANUAL.value
        vm.manual_urls_var.get.return_value = "   "

        assert presenter._read_url_source_value_from_vm() == []

    def test_non_manual_returns_path_string(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        vm.url_source_type_var.get.return_value = UrlSourceTypeEnum.E_FOLDER.value
        vm.url_source_path_var.get.return_value = "/some/folder"

        assert presenter._read_url_source_value_from_vm() == "/some/folder"

    def test_non_manual_empty_path_returns_none(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        vm.url_source_type_var.get.return_value = UrlSourceTypeEnum.E_FOLDER.value
        vm.url_source_path_var.get.return_value = "   "

        assert presenter._read_url_source_value_from_vm() is None


# ---------------------------------------------------------------------------
# Lines 513-514: _on_form_changed
# ---------------------------------------------------------------------------


class TestOnFormChanged:
    def test_marks_dirty_and_refreshes_url_preview(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        vm.url_source_type_var.get.return_value = ""
        vm.url_sort_order_var.get.return_value = UrlSortOrderEnum.E_MTIME_ASC.value
        vm.url_source_path_var.get.return_value = ""

        presenter._on_form_changed()

        assert presenter._is_dirty is True


# ---------------------------------------------------------------------------
# Lines 543-548: _validate_launch — guard conditions
# ---------------------------------------------------------------------------


class TestValidateLaunch:
    def test_no_scenario_returns_no_scenario_error(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        presenter._current_scenario = None

        assert presenter._validate_launch() == C_EXEC_NO_SCENARIO

    def test_no_profile_returns_no_profile_error(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        presenter._current_scenario = _make_scenario()
        presenter._current_profile = None

        assert presenter._validate_launch() == C_EXEC_NO_PROFILE

    def test_valid_profile_returns_none(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        presenter._current_scenario = _make_scenario()
        presenter._current_profile = _make_profile()

        vm.url_source_type_var.get.return_value = UrlSourceTypeEnum.E_MANUAL.value
        vm.manual_urls_var.get.return_value = "http://example.com"
        vm.url_source_path_var.get.return_value = ""
        vm.url_sort_order_var.get.return_value = UrlSortOrderEnum.E_MTIME_ASC.value
        vm.step_id_selected_var.get.return_value = "step001"
        vm.global_threshold_var.get.return_value = "10"
        vm.step_threshold_var.get.return_value = "5"
        vm.export_folder_var.get.return_value = "/tmp/export"

        assert presenter._validate_launch() is None


# ---------------------------------------------------------------------------
# Lines 552-559: _save_before_launch
# ---------------------------------------------------------------------------


class TestSaveBeforeLaunch:
    def test_no_profile_returns_early(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        presenter._current_profile = None
        presenter._current_scenario = _make_scenario()

        presenter._save_before_launch()

        svc_prof.update_profile_launch.assert_not_called()

    def test_no_scenario_returns_early(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        presenter._current_profile = _make_profile()
        presenter._current_scenario = None

        presenter._save_before_launch()

        svc_prof.update_profile_launch.assert_not_called()

    def test_increments_launch_count_and_persists(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        scenario = _make_scenario()
        profile = _make_profile()
        initial_count = profile.launch_count

        presenter._current_scenario = scenario
        presenter._current_profile = profile
        svc_prof.update_profile_launch.return_value = None

        presenter._save_before_launch()

        assert profile.launch_count == initial_count + 1
        svc_prof.update_profile_launch.assert_called_once_with(scenario.id_file, profile)

    def test_service_error_is_logged_but_does_not_raise(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        scenario = _make_scenario()
        profile = _make_profile()
        presenter._current_scenario = scenario
        presenter._current_profile = profile
        svc_prof.update_profile_launch.side_effect = CallbackNotDefinedError()

        presenter._save_before_launch()  # must not propagate the exception

        svc_prof.update_profile_launch.assert_called_once()


# ---------------------------------------------------------------------------
# Lines 529-535: _on_launch_clicked — success and failure paths
# ---------------------------------------------------------------------------


class TestOnLaunchClicked:
    def _setup_valid_vm(self, vm: MagicMock) -> None:
        vm.url_source_type_var.get.return_value = UrlSourceTypeEnum.E_MANUAL.value
        vm.manual_urls_var.get.return_value = "http://example.com"
        vm.url_source_path_var.get.return_value = ""
        vm.url_sort_order_var.get.return_value = UrlSortOrderEnum.E_MTIME_ASC.value
        vm.step_id_selected_var.get.return_value = "step001"
        vm.global_threshold_var.get.return_value = "10"
        vm.step_threshold_var.get.return_value = "5"
        vm.export_folder_var.get.return_value = "/tmp/export"

    def test_invalid_profile_sets_error_message_and_does_not_call_hook(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        presenter._current_scenario = _make_scenario()
        presenter._current_profile = _make_profile()

        # Leave VM vars returning empty/invalid values (MagicMock defaults)
        vm.url_source_type_var.get.return_value = ""
        vm.export_folder_var.get.return_value = ""
        vm.url_sort_order_var.get.return_value = ""
        vm.step_id_selected_var.get.return_value = ""
        vm.global_threshold_var.get.return_value = "0"
        vm.step_threshold_var.get.return_value = "0"
        vm.manual_urls_var.get.return_value = ""
        vm.url_source_path_var.get.return_value = ""

        hook = MagicMock()
        presenter.on_request_launch_scraping = hook

        presenter._on_launch_clicked()

        vm.verification_message_var.set.assert_called()
        hook.assert_not_called()

    def test_valid_profile_calls_launch_hook(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        scenario = _make_scenario()
        profile = _make_profile()
        presenter._current_scenario = scenario
        presenter._current_profile = profile
        svc_prof.update_profile_launch.return_value = None

        self._setup_valid_vm(vm)

        hook = MagicMock()
        presenter.on_request_launch_scraping = hook

        presenter._on_launch_clicked()

        vm.verification_message_var.set.assert_called_with("")
        hook.assert_called_once_with(scenario, profile)

    def test_no_hook_does_not_raise_when_valid(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        presenter._current_scenario = _make_scenario()
        presenter._current_profile = _make_profile()
        presenter.on_request_launch_scraping = None
        svc_prof.update_profile_launch.return_value = None

        self._setup_valid_vm(vm)

        presenter._on_launch_clicked()  # should not raise


# ---------------------------------------------------------------------------
# Lines 563-569: _on_open_export_folder
# ---------------------------------------------------------------------------


class TestOnOpenExportFolder:
    def test_empty_folder_returns_early(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        vm.export_folder_var.get.return_value = ""

        presenter._on_open_export_folder()

        svc_prof.open_export_folder.assert_not_called()

    def test_valid_folder_calls_service(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        vm.export_folder_var.get.return_value = "/tmp/export"
        svc_prof.open_export_folder.return_value = None

        presenter._on_open_export_folder()

        svc_prof.open_export_folder.assert_called_once_with("/tmp/export")

    def test_service_error_shows_error_dialog(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        vm.export_folder_var.get.return_value = "/tmp/export"
        svc_prof.open_export_folder.side_effect = CallbackNotDefinedError()

        presenter._on_open_export_folder()

        vm.show_error.assert_called_once()

    def test_os_error_shows_error_dialog(self) -> None:
        presenter, vm, _, svc_prof = _make_presenter()
        vm.export_folder_var.get.return_value = "/tmp/export"
        svc_prof.open_export_folder.side_effect = OSError("permission denied")

        presenter._on_open_export_folder()

        vm.show_error.assert_called_once()
