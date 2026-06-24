"""Tests for presenters/url_config_presenter.py."""

from __future__ import annotations

from unittest.mock import MagicMock

from models.launcher_model import LaunchModel
from models.sourcing_urls.urls_discover_entries_model import UrlsDiscoverEntriesModel
from models.sourcing_urls.urls_discover_item_model import UrlsDiscoverItemModel
from models.sourcing_urls.urls_folder_jsons_model import UrlsFolderJsonsModel
from models.sourcing_urls.urls_folder_racs_model import UrlsFolderRacsModel
from presenters.url_config_presenter import UrlConfigPresenter
from services.sourcing_urls.sourcing_urls_service import SourcingUrlsService
from shared.enums import RelativeDateEnum, UrlSortOrderEnum, UrlSourceTypeEnum
from view_models.executor_view_model import DiscoverRowState

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_vm() -> MagicMock:
    vm = MagicMock()
    # Mimick StringVar.get() / set() on relevant vars
    vm.urls_source_type_var.get.return_value = UrlSourceTypeEnum.E_MANUAL_LIST.value
    vm.urls_path_folder_racs_var.get.return_value = "/racs"
    vm.url_sort_order_shortcuts_var.get.return_value = UrlSortOrderEnum.E_MTIME_ASC.value
    vm.urls_path_folder_jsons_var.get.return_value = "/jsons"
    vm.url_sort_order_jsons_var.get.return_value = UrlSortOrderEnum.E_MTIME_ASC.value
    vm.json_date_modified_start_var.get.return_value = RelativeDateEnum.E_LAST_NOW.enum_to_view()
    vm.json_date_modified_end_var.get.return_value = RelativeDateEnum.E_LAST_99.enum_to_view()
    vm.disc_out_pattern_json_var.get.return_value = ""
    vm.disc_out_key_mapping_var.get.return_value = ""
    vm.disc_out_pattern_urls_var.get.return_value = ""
    vm.export_folder_var.get.return_value = "/export"
    vm.get_discovers_in_rows.return_value = []
    return vm


def _make_sourcing() -> MagicMock:
    return MagicMock(spec=SourcingUrlsService)


def _make_presenter() -> tuple[UrlConfigPresenter, MagicMock, MagicMock]:
    vm = _make_vm()
    sourcing = _make_sourcing()
    presenter = UrlConfigPresenter(vm=vm, sourcing_urls=sourcing)
    return presenter, vm, sourcing


def _make_item(
    id_discover: str = "id1",
    folder: str = "/folder",
    pattern: str = "export*.json",
    key: str = "url",
    urls: str = "https*",
) -> UrlsDiscoverItemModel:
    return UrlsDiscoverItemModel(
        id_discover=id_discover, folder_json=folder, pattern_json=pattern, key_mapping=key, pattern_urls=urls
    )


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


class TestInit:
    def test_out_discover_id_is_set(self) -> None:
        presenter, *_ = _make_presenter()
        assert presenter._out_discover_id != ""

    def test_vm_stored(self) -> None:
        vm = _make_vm()
        sourcing = _make_sourcing()
        presenter = UrlConfigPresenter(vm=vm, sourcing_urls=sourcing)
        assert presenter._vm is vm


# ---------------------------------------------------------------------------
# refresh_preview_for_profile
# ---------------------------------------------------------------------------


class TestRefreshPreviewForProfile:
    def test_folder_racs_calls_provider(self) -> None:
        presenter, vm, sourcing = _make_presenter()
        profile = MagicMock(spec=LaunchModel)
        profile.urls_source_type = UrlSourceTypeEnum.E_FOLDER_RACS
        profile.urls_folder_racs = UrlsFolderRacsModel(
            folder_racs="/folder", orders_racs=UrlSortOrderEnum.E_MTIME_ASC.value
        )

        provider = MagicMock()
        provider.preview_all_urls.return_value = ["https://a.com"]
        sourcing.get_provider_folder_racs.return_value = provider

        presenter.refresh_preview_for_profile(profile)

        provider.setup_model.assert_called_once()
        provider.loads_urls.assert_called_once()
        vm.set_url_preview_shortcuts.assert_called_once_with(["https://a.com"])

    def test_folder_jsons_calls_provider(self) -> None:
        presenter, vm, sourcing = _make_presenter()
        profile = MagicMock(spec=LaunchModel)
        profile.urls_source_type = UrlSourceTypeEnum.E_FOLDER_JSONS
        profile.urls_folder_jsons = UrlsFolderJsonsModel(
            folder_json="/jsons",
            orders_json=UrlSortOrderEnum.E_MTIME_ASC.value,
            date_modified_start=RelativeDateEnum.E_LAST_99,
            date_modified_end=RelativeDateEnum.E_LAST_NOW,
        )

        provider = MagicMock()
        provider.preview_all_urls.return_value = ["https://b.com"]
        sourcing.get_provider_folder_jsons.return_value = provider

        presenter.refresh_preview_for_profile(profile)

        provider.setup_model.assert_called_once()
        vm.set_url_preview_jsons.assert_called_once_with(["https://b.com"])

    def test_other_source_type_is_noop(self) -> None:
        presenter, vm, sourcing = _make_presenter()
        profile = MagicMock(spec=LaunchModel)
        profile.urls_source_type = UrlSourceTypeEnum.E_MANUAL_LIST

        presenter.refresh_preview_for_profile(profile)

        sourcing.get_provider_folder_racs.assert_not_called()
        sourcing.get_provider_folder_jsons.assert_not_called()

    def test_provider_exception_results_in_empty_preview(self) -> None:
        presenter, vm, sourcing = _make_presenter()
        profile = MagicMock(spec=LaunchModel)
        profile.urls_source_type = UrlSourceTypeEnum.E_FOLDER_RACS
        profile.urls_folder_racs = UrlsFolderRacsModel(
            folder_racs="/bad", orders_racs=UrlSortOrderEnum.E_MTIME_ASC.value
        )

        provider = MagicMock()
        provider.loads_urls.side_effect = RuntimeError("failed")
        sourcing.get_provider_folder_racs.return_value = provider

        presenter.refresh_preview_for_profile(profile)  # must not raise
        vm.set_url_preview_shortcuts.assert_called_once_with([])


# ---------------------------------------------------------------------------
# load_discover_hub
# ---------------------------------------------------------------------------


class TestLoadDiscoverHub:
    def test_delegates_to_internal_loader(self) -> None:
        presenter, vm, _ = _make_presenter()
        inp = _make_item("in1", "/in")
        out = _make_item("out1", "/out")
        hub = UrlsDiscoverEntriesModel(inputs=[inp], output=out)

        presenter.load_discover_hub(hub)

        vm.set_discovers_in_rows.assert_called_once()
        vm.disc_out_pattern_json_var.set.assert_called_once()


# ---------------------------------------------------------------------------
# refresh_preview_from_vm
# ---------------------------------------------------------------------------


class TestRefreshPreviewFromVm:
    def test_invalid_source_type_is_noop(self) -> None:
        presenter, vm, sourcing = _make_presenter()
        vm.urls_source_type_var.get.return_value = "INVALID_TYPE"

        presenter.refresh_preview_from_vm()  # must not raise

        sourcing.get_provider_folder_racs.assert_not_called()

    def test_folder_racs_refreshes_preview(self) -> None:
        presenter, vm, sourcing = _make_presenter()
        vm.urls_source_type_var.get.return_value = UrlSourceTypeEnum.E_FOLDER_RACS.value

        provider = MagicMock()
        provider.preview_all_urls.return_value = ["https://x.com"]
        sourcing.get_provider_folder_racs.return_value = provider

        presenter.refresh_preview_from_vm()

        vm.set_url_preview_shortcuts.assert_called_once_with(["https://x.com"])

    def test_folder_jsons_refreshes_preview(self) -> None:
        presenter, vm, sourcing = _make_presenter()
        vm.urls_source_type_var.get.return_value = UrlSourceTypeEnum.E_FOLDER_JSONS.value

        provider = MagicMock()
        provider.preview_all_urls.return_value = ["https://y.com"]
        sourcing.get_provider_folder_jsons.return_value = provider

        presenter.refresh_preview_from_vm()

        vm.set_url_preview_jsons.assert_called_once_with(["https://y.com"])


# ---------------------------------------------------------------------------
# get_current_discovers_hub
# ---------------------------------------------------------------------------


class TestGetCurrentDiscoverHub:
    def test_returns_hub_from_vm(self) -> None:
        presenter, vm, _ = _make_presenter()
        hub = presenter.get_current_discovers_hub()
        assert isinstance(hub, UrlsDiscoverEntriesModel)


# ---------------------------------------------------------------------------
# clear_url_state
# ---------------------------------------------------------------------------


class TestClearUrlState:
    def test_clears_previews_and_discover_state(self) -> None:
        presenter, vm, _ = _make_presenter()

        presenter.clear_url_state()

        vm.set_url_preview_shortcuts.assert_called_once_with([])
        vm.set_url_preview_jsons.assert_called_once_with([])
        vm.set_discovers_in_rows.assert_called_once_with([])
        vm.disc_out_pattern_json_var.set.assert_called_once_with("")
        vm.disc_out_key_mapping_var.set.assert_called_once_with("")
        vm.disc_out_pattern_urls_var.set.assert_called_once_with("")


# ---------------------------------------------------------------------------
# _on_select_discover
# ---------------------------------------------------------------------------


class TestOnSelectDiscover:
    def test_sets_selected_discover_id(self) -> None:
        presenter, vm, _ = _make_presenter()
        presenter._on_select_discover("disc_id_42")
        vm.selected_discover_id_var.set.assert_called_once_with("disc_id_42")


# ---------------------------------------------------------------------------
# _load_discover_hub_into_vm
# ---------------------------------------------------------------------------


class TestLoadDiscoverHubIntoVm:
    def test_sets_out_discover_id(self) -> None:
        presenter, vm, _ = _make_presenter()
        out = _make_item(id_discover="out_id_123")
        hub = UrlsDiscoverEntriesModel(inputs=[], output=out)

        presenter._load_discover_hub_into_vm(hub)

        assert presenter._out_discover_id == "out_id_123"

    def test_builds_rows_from_inputs(self) -> None:
        presenter, vm, _ = _make_presenter()
        inp = _make_item("in1", "/folder_in", "exp*.json", "key", "https*")
        out = _make_item("out1")
        hub = UrlsDiscoverEntriesModel(inputs=[inp], output=out)

        presenter._load_discover_hub_into_vm(hub)

        rows = vm.set_discovers_in_rows.call_args[0][0]
        assert len(rows) == 1
        row = rows[0]
        assert row.id_discover == "in1"
        assert row.folder_json == "/folder_in"

    def test_sets_out_form_fields(self) -> None:
        presenter, vm, _ = _make_presenter()
        out = _make_item("out1", "/out_folder", "exp*.json", "key_out", "https*")
        hub = UrlsDiscoverEntriesModel(inputs=[], output=out)

        presenter._load_discover_hub_into_vm(hub)

        vm.disc_out_pattern_json_var.set.assert_called_once_with("exp*.json")
        vm.disc_out_key_mapping_var.set.assert_called_once_with("key_out")
        vm.disc_out_pattern_urls_var.set.assert_called_once_with("https*")


# ---------------------------------------------------------------------------
# _display_to_relative_date_value
# ---------------------------------------------------------------------------


class TestDisplayToRelativeDateValue:
    def test_known_display_returns_value(self) -> None:
        display = RelativeDateEnum.E_LAST_3D.enum_to_view()
        result = UrlConfigPresenter._display_to_relative_date_value(display)
        assert result == RelativeDateEnum.E_LAST_3D.value

    def test_unknown_display_returns_unset(self) -> None:
        result = UrlConfigPresenter._display_to_relative_date_value("UNKNOWN_DISPLAY_STRING")
        assert result == RelativeDateEnum.E_UNSET.value


# ---------------------------------------------------------------------------
# _build_discover_hub_from_vm
# ---------------------------------------------------------------------------


class TestBuildDiscoverHubFromVm:
    def test_non_empty_out_fields_produce_output_item(self) -> None:
        presenter, vm, _ = _make_presenter()
        vm.disc_out_pattern_json_var.get.return_value = "exp*.json"
        vm.disc_out_key_mapping_var.get.return_value = "key_url"
        vm.disc_out_pattern_urls_var.get.return_value = "https*"
        vm.export_folder_var.get.return_value = "/export/folder"
        vm.get_discovers_in_rows.return_value = []

        hub = presenter._build_discover_hub_from_vm()

        assert hub.output is not None
        assert hub.output.pattern_json == "exp*.json"
        assert hub.output.key_mapping == "key_url"
        assert hub.output.folder_json == "/export/folder"

    def test_input_rows_are_converted_to_models(self) -> None:
        presenter, vm, _ = _make_presenter()
        vm.disc_out_pattern_json_var.get.return_value = ""
        vm.disc_out_key_mapping_var.get.return_value = ""
        vm.disc_out_pattern_urls_var.get.return_value = ""

        row = DiscoverRowState(
            id_discover="row1", folder_json="/in", pattern_json="*.json", key_mapping="key", pattern_urls="https*"
        )
        vm.get_discovers_in_rows.return_value = [row]

        hub = presenter._build_discover_hub_from_vm()

        assert len(hub.inputs) == 1
        assert hub.inputs[0].id_discover == "row1"
        assert hub.inputs[0].folder_json == "/in"
