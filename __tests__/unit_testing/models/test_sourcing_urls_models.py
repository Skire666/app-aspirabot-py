"""Tests for models/sourcing_urls/*.py — all URL source model classes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from models.sourcing_urls.urls_discover_item_model import UrlsDiscoverItemModel
from models.sourcing_urls.urls_folder_jsons_model import UrlsFolderJsonsModel
from models.sourcing_urls.urls_folder_racs_model import UrlsFolderRacsModel
from models.sourcing_urls.urls_manual_list_model import UrlsManualListModel
from shared.enums import RelativeDateEnum, UrlSourceTypeEnum


# ===========================================================================
# UrlsManualListModel
# ===========================================================================


class TestUrlsManualListModel:
    def test_get_default_returns_empty(self) -> None:
        m = UrlsManualListModel.get_default()
        assert m.get_urls() == []

    def test_init_with_urls(self) -> None:
        m = UrlsManualListModel(urls=["http://a.com", "http://b.com"])
        assert len(m.get_urls()) == 2

    def test_append_url_adds_stripped(self) -> None:
        m = UrlsManualListModel()
        m.append_url("  http://a.com  ")
        assert m.get_urls() == ["http://a.com"]

    def test_append_url_ignores_blank(self) -> None:
        m = UrlsManualListModel()
        m.append_url("   ")
        assert m.get_urls() == []

    def test_append_urls(self) -> None:
        m = UrlsManualListModel()
        m.append_urls(["http://a.com", "http://b.com"])
        assert len(m.get_urls()) == 2

    def test_clear_urls(self) -> None:
        m = UrlsManualListModel(urls=["http://a.com"])
        m.clear_urls()
        assert m.get_urls() == []

    def test_get_type_source(self) -> None:
        assert UrlsManualListModel.get_type_source() is UrlSourceTypeEnum.E_MANUAL_LIST

    def test_import_from_data_json(self) -> None:
        data = {"url_sources_list_manual": ["http://a.com"]}
        m = UrlsManualListModel.import_from_data_json(data)
        assert m.get_urls() == ["http://a.com"]

    def test_import_from_data_json_missing_key(self) -> None:
        m = UrlsManualListModel.import_from_data_json({})
        assert m.get_urls() == []

    def test_import_from_data_json_non_list_value(self) -> None:
        m = UrlsManualListModel.import_from_data_json({"url_sources_list_manual": "not a list"})
        assert m.get_urls() == []

    def test_export_to_data_json(self) -> None:
        m = UrlsManualListModel(urls=["http://x.com"])
        d = m.export_to_data_json()
        assert d["url_sources_list_manual"] == ["http://x.com"]

    def test_validate_empty_urls_is_error(self) -> None:
        m = UrlsManualListModel()
        vr = m.validate()
        assert vr.has_errors_or_fatals()

    def test_validate_too_short_url_is_error(self) -> None:
        m = UrlsManualListModel(urls=["ab"])
        vr = m.validate()
        assert vr.has_errors_or_fatals()

    def test_validate_valid_urls_passes(self) -> None:
        m = UrlsManualListModel(urls=["http://example.com"])
        vr = m.validate()
        assert not vr.has_errors_or_fatals()


# ===========================================================================
# UrlsFolderRacsModel
# ===========================================================================


class TestUrlsFolderRacsModel:
    def test_get_default_empty(self) -> None:
        m = UrlsFolderRacsModel.get_default()
        assert m.folder_racs == ""
        assert m.orders_racs == ""

    def test_strips_whitespace_on_init(self) -> None:
        m = UrlsFolderRacsModel(folder_racs="  path  ", orders_racs="  ASC  ")
        assert m.folder_racs == "path"
        assert m.orders_racs == "ASC"

    def test_get_type_source(self) -> None:
        assert UrlsFolderRacsModel.get_type_source() is UrlSourceTypeEnum.E_FOLDER_RACS

    def test_import_from_data_json(self) -> None:
        m = UrlsFolderRacsModel.import_from_data_json({"folder_racs": "f", "orders_racs": "ASC"})
        assert m.folder_racs == "f"
        assert m.orders_racs == "ASC"

    def test_import_missing_keys(self) -> None:
        m = UrlsFolderRacsModel.import_from_data_json({})
        assert m.folder_racs == ""

    def test_export_to_data_json(self) -> None:
        m = UrlsFolderRacsModel(folder_racs="myfolder", orders_racs="ASC")
        d = m.export_to_data_json()
        assert d["folder_racs"] == "myfolder"
        assert d["orders_racs"] == "ASC"

    def test_validate_empty_folder_is_error(self) -> None:
        vr = UrlsFolderRacsModel.get_default().validate()
        assert vr.has_errors_or_fatals()

    def test_validate_invalid_path_syntax_is_error(self) -> None:
        m = UrlsFolderRacsModel(folder_racs="invalid<path>", orders_racs="ASC")
        vr = m.validate()
        assert vr.has_errors_or_fatals()

    def test_validate_empty_orders_is_error(self) -> None:
        with patch("models.sourcing_urls.urls_folder_racs_model.path_has_valid_syntax", return_value=True):
            m = UrlsFolderRacsModel(folder_racs="some_folder", orders_racs="")
            vr = m.validate()
            assert vr.has_errors_or_fatals()

    def test_validate_unset_orders_is_error(self) -> None:
        with patch("models.sourcing_urls.urls_folder_racs_model.path_has_valid_syntax", return_value=True):
            m = UrlsFolderRacsModel(folder_racs="some_folder", orders_racs="UNSET")
            vr = m.validate()
            assert vr.has_errors_or_fatals()

    def test_validate_folder_not_exists_is_error(self) -> None:
        with (
            patch("models.sourcing_urls.urls_folder_racs_model.path_has_valid_syntax", return_value=True),
            patch("models.sourcing_urls.urls_folder_racs_model.folder_exists", return_value=False),
        ):
            m = UrlsFolderRacsModel(folder_racs="some_folder", orders_racs="ASC")
            vr = m.validate()
            assert vr.has_errors_or_fatals()

    def test_validate_no_url_files_is_error(self) -> None:
        with (
            patch("models.sourcing_urls.urls_folder_racs_model.path_has_valid_syntax", return_value=True),
            patch("models.sourcing_urls.urls_folder_racs_model.folder_exists", return_value=True),
            patch("models.sourcing_urls.urls_folder_racs_model.count_files_in_folder", return_value=0),
        ):
            m = UrlsFolderRacsModel(folder_racs="some_folder", orders_racs="ASC")
            vr = m.validate()
            assert vr.has_errors_or_fatals()

    def test_validate_passes_with_valid_folder(self) -> None:
        with (
            patch("models.sourcing_urls.urls_folder_racs_model.path_has_valid_syntax", return_value=True),
            patch("models.sourcing_urls.urls_folder_racs_model.folder_exists", return_value=True),
            patch("models.sourcing_urls.urls_folder_racs_model.count_files_in_folder", return_value=3),
        ):
            m = UrlsFolderRacsModel(folder_racs="some_folder", orders_racs="ASC")
            vr = m.validate()
            assert not vr.has_errors_or_fatals()


# ===========================================================================
# UrlsFolderJsonsModel
# ===========================================================================


class TestUrlsFolderJsonsModel:
    def test_get_default_empty(self) -> None:
        m = UrlsFolderJsonsModel.get_default()
        assert m.folder_jsons == ""

    def test_strips_whitespace(self) -> None:
        m = UrlsFolderJsonsModel(
            folder_json="  folder  ",
            orders_json="  ASC  ",
            url_regexp="http*",
            date_modified_start=RelativeDateEnum.E_UNSET,
            date_modified_end=RelativeDateEnum.E_UNSET,
        )
        assert m.folder_jsons == "folder"
        assert m.orders_jsons == "ASC"

    def test_get_type_source(self) -> None:
        assert UrlsFolderJsonsModel.get_type_source() is UrlSourceTypeEnum.E_FOLDER_JSONS

    def test_import_from_data_json(self) -> None:
        m = UrlsFolderJsonsModel.import_from_data_json({
            "folder_json": "f",
            "orders_json": "ASC",
            "date_modified_start": "LAST_3D",
            "date_modified_end": "LAST_1Y",
        })
        assert m.folder_jsons == "f"

    def test_export_to_data_json(self) -> None:
        m = UrlsFolderJsonsModel.get_default()
        d = m.export_to_data_json()
        assert "folder_json" in d
        assert "orders_json" in d

    def test_validate_empty_folder_is_error(self) -> None:
        vr = UrlsFolderJsonsModel.get_default().validate()
        assert vr.has_errors_or_fatals()

    def test_validate_invalid_path_syntax_is_error(self) -> None:
        m = UrlsFolderJsonsModel(
            folder_json="invalid<>path",
            orders_json="ASC",
            url_regexp="http*",
            date_modified_start=RelativeDateEnum.E_LAST_3D,
            date_modified_end=RelativeDateEnum.E_LAST_1Y,
        )
        vr = m.validate()
        assert vr.has_errors_or_fatals()

    def test_validate_empty_orders_is_error(self) -> None:
        with patch("models.sourcing_urls.urls_folder_jsons_model.path_has_valid_syntax", return_value=True):
            m = UrlsFolderJsonsModel(
                folder_json="folder",
                orders_json="",
                url_regexp="http*",
                date_modified_start=RelativeDateEnum.E_UNSET,
                date_modified_end=RelativeDateEnum.E_UNSET,
            )
            vr = m.validate()
            assert vr.has_errors_or_fatals()

    def test_validate_unset_orders_is_error(self) -> None:
        with patch("models.sourcing_urls.urls_folder_jsons_model.path_has_valid_syntax", return_value=True):
            m = UrlsFolderJsonsModel(
                folder_json="folder",
                orders_json="UNSET",
                url_regexp="http*",
                date_modified_start=RelativeDateEnum.E_UNSET,
                date_modified_end=RelativeDateEnum.E_UNSET,
            )
            vr = m.validate()
            assert vr.has_errors_or_fatals()

    def test_validate_folder_not_exists_is_error(self) -> None:
        with (
            patch("models.sourcing_urls.urls_folder_jsons_model.path_has_valid_syntax", return_value=True),
            patch("models.sourcing_urls.urls_folder_jsons_model.folder_exists", return_value=False),
        ):
            m = UrlsFolderJsonsModel(
                folder_json="folder",
                orders_json="ASC",
                url_regexp="http*",
                date_modified_start=RelativeDateEnum.E_UNSET,
                date_modified_end=RelativeDateEnum.E_UNSET,
            )
            vr = m.validate()
            assert vr.has_errors_or_fatals()

    def test_validate_no_json_files_is_error(self) -> None:
        with (
            patch("models.sourcing_urls.urls_folder_jsons_model.path_has_valid_syntax", return_value=True),
            patch("models.sourcing_urls.urls_folder_jsons_model.folder_exists", return_value=True),
            patch("models.sourcing_urls.urls_folder_jsons_model.count_files_in_folder", return_value=0),
        ):
            m = UrlsFolderJsonsModel(
                folder_json="folder",
                orders_json="ASC",
                url_regexp="http*",
                date_modified_start=RelativeDateEnum.E_UNSET,
                date_modified_end=RelativeDateEnum.E_UNSET,
            )
            vr = m.validate()
            assert vr.has_errors_or_fatals()

    def test_validate_invalid_start_date_is_error(self) -> None:
        with (
            patch("models.sourcing_urls.urls_folder_jsons_model.path_has_valid_syntax", return_value=True),
            patch("models.sourcing_urls.urls_folder_jsons_model.folder_exists", return_value=True),
            patch("models.sourcing_urls.urls_folder_jsons_model.count_files_in_folder", return_value=1),
        ):
            m = UrlsFolderJsonsModel(
                folder_json="folder",
                orders_json="ASC",
                url_regexp="http*",
                date_modified_start=RelativeDateEnum.E_UNSET,
                date_modified_end=RelativeDateEnum.E_LAST_1Y,
            )
            vr = m.validate()
            assert vr.has_errors_or_fatals()

    def test_validate_invalid_end_date_is_error(self) -> None:
        with (
            patch("models.sourcing_urls.urls_folder_jsons_model.path_has_valid_syntax", return_value=True),
            patch("models.sourcing_urls.urls_folder_jsons_model.folder_exists", return_value=True),
            patch("models.sourcing_urls.urls_folder_jsons_model.count_files_in_folder", return_value=1),
        ):
            m = UrlsFolderJsonsModel(
                folder_json="folder",
                orders_json="ASC",
                url_regexp="http*",
                date_modified_start=RelativeDateEnum.E_LAST_3D,
                date_modified_end=RelativeDateEnum.E_UNSET,
            )
            vr = m.validate()
            assert vr.has_errors_or_fatals()

    def test_validate_start_not_lower_than_end_is_error(self) -> None:
        with (
            patch("models.sourcing_urls.urls_folder_jsons_model.path_has_valid_syntax", return_value=True),
            patch("models.sourcing_urls.urls_folder_jsons_model.folder_exists", return_value=True),
            patch("models.sourcing_urls.urls_folder_jsons_model.count_files_in_folder", return_value=1),
        ):
            m = UrlsFolderJsonsModel(
                folder_json="folder",
                orders_json="ASC",
                url_regexp="http*",
                date_modified_start=RelativeDateEnum.E_LAST_1Y,
                date_modified_end=RelativeDateEnum.E_LAST_3D,
            )
            vr = m.validate()
            assert vr.has_errors_or_fatals()

    def test_validate_passes_with_all_valid(self) -> None:
        with (
            patch("models.sourcing_urls.urls_folder_jsons_model.path_has_valid_syntax", return_value=True),
            patch("models.sourcing_urls.urls_folder_jsons_model.folder_exists", return_value=True),
            patch("models.sourcing_urls.urls_folder_jsons_model.count_files_in_folder", return_value=3),
        ):
            m = UrlsFolderJsonsModel(
                folder_json="folder",
                orders_json="ASC",
                url_regexp="http*",
                date_modified_start=RelativeDateEnum.E_LAST_3D,
                date_modified_end=RelativeDateEnum.E_LAST_1Y,
            )
            vr = m.validate()
            assert not vr.has_errors_or_fatals()


# ===========================================================================
# UrlsDiscoverItemModel
# ===========================================================================


class TestUrlsDiscoverItemModel:
    def test_get_default(self) -> None:
        m = UrlsDiscoverItemModel.get_default()
        assert m.folder_json == ""
        assert m.pattern_json == "export*.json"

    def test_import_from_data_json(self) -> None:
        data = {
            "id_discover": "abc",
            "folder_json": "myfolder",
            "pattern_json": "*.json",
            "key_mapping": "url",
            "pattern_urls": "https*",
        }
        m = UrlsDiscoverItemModel.import_from_data_json(data)
        assert m.id_discover == "abc"
        assert m.folder_json == "myfolder"

    def test_import_missing_keys(self) -> None:
        m = UrlsDiscoverItemModel.import_from_data_json({})
        assert m.id_discover == ""
        assert m.folder_json == ""

    def test_export_to_data_json(self) -> None:
        m = UrlsDiscoverItemModel.get_default()
        d = m.export_to_data_json()
        assert "id_discover" in d
        assert "folder_json" in d

    def test_validate_inputs_empty_folder_is_error(self) -> None:
        m = UrlsDiscoverItemModel.get_default()
        vr = m.validate_inputs()
        assert vr.has_errors_or_fatals()

    def test_validate_inputs_folder_not_exists_is_error(self) -> None:
        with patch("models.sourcing_urls.urls_discover_item_model.folder_exists", return_value=False):
            m = UrlsDiscoverItemModel(
                id_discover="x",
                folder_json="nonexistent",
                pattern_json="*.json",
                key_mapping="url",
                pattern_urls="https*",
            )
            vr = m.validate_inputs()
            assert vr.has_errors_or_fatals()

    def test_validate_inputs_no_json_files_is_error(self) -> None:
        with (
            patch("models.sourcing_urls.urls_discover_item_model.folder_exists", return_value=True),
            patch("models.sourcing_urls.urls_discover_item_model.count_files_in_folder", return_value=0),
        ):
            m = UrlsDiscoverItemModel(
                id_discover="x",
                folder_json="folder",
                pattern_json="*.json",
                key_mapping="url",
                pattern_urls="https*",
            )
            vr = m.validate_inputs()
            assert vr.has_errors_or_fatals()

    def test_validate_inputs_empty_pattern_json_is_error(self) -> None:
        with (
            patch("models.sourcing_urls.urls_discover_item_model.folder_exists", return_value=True),
            patch("models.sourcing_urls.urls_discover_item_model.count_files_in_folder", return_value=1),
        ):
            m = UrlsDiscoverItemModel(
                id_discover="x",
                folder_json="folder",
                pattern_json="",
                key_mapping="url",
                pattern_urls="https*",
            )
            vr = m.validate_inputs()
            assert vr.has_errors_or_fatals()

    def test_validate_inputs_pattern_not_ending_json_is_error(self) -> None:
        with (
            patch("models.sourcing_urls.urls_discover_item_model.folder_exists", return_value=True),
            patch("models.sourcing_urls.urls_discover_item_model.count_files_in_folder", return_value=1),
        ):
            m = UrlsDiscoverItemModel(
                id_discover="x",
                folder_json="folder",
                pattern_json="export*.txt",
                key_mapping="url",
                pattern_urls="https*",
            )
            vr = m.validate_inputs()
            assert vr.has_errors_or_fatals()

    def test_validate_inputs_empty_key_mapping_is_error(self) -> None:
        with (
            patch("models.sourcing_urls.urls_discover_item_model.folder_exists", return_value=True),
            patch("models.sourcing_urls.urls_discover_item_model.count_files_in_folder", return_value=1),
        ):
            m = UrlsDiscoverItemModel(
                id_discover="x",
                folder_json="folder",
                pattern_json="export*.json",
                key_mapping="",
                pattern_urls="https*",
            )
            vr = m.validate_inputs()
            assert vr.has_errors_or_fatals()

    def test_validate_inputs_empty_pattern_urls_is_error(self) -> None:
        with (
            patch("models.sourcing_urls.urls_discover_item_model.folder_exists", return_value=True),
            patch("models.sourcing_urls.urls_discover_item_model.count_files_in_folder", return_value=1),
        ):
            m = UrlsDiscoverItemModel(
                id_discover="x",
                folder_json="folder",
                pattern_json="export*.json",
                key_mapping="url",
                pattern_urls="",
            )
            vr = m.validate_inputs()
            assert vr.has_errors_or_fatals()

    def test_validate_inputs_passes_for_valid_model(self) -> None:
        with (
            patch("models.sourcing_urls.urls_discover_item_model.folder_exists", return_value=True),
            patch("models.sourcing_urls.urls_discover_item_model.count_files_in_folder", return_value=2),
        ):
            m = UrlsDiscoverItemModel(
                id_discover="x",
                folder_json="folder",
                pattern_json="export*.json",
                key_mapping="url",
                pattern_urls="https*",
            )
            vr = m.validate_inputs()
            assert not vr.has_errors_or_fatals()

    def test_validate_output_empty_folder_is_error(self) -> None:
        m = UrlsDiscoverItemModel.get_default()
        vr = m.validate_output()
        assert vr.has_errors_or_fatals()

    def test_validate_output_folder_not_exists_is_error(self) -> None:
        with patch("models.sourcing_urls.urls_discover_item_model.folder_exists", return_value=False):
            m = UrlsDiscoverItemModel(
                id_discover="x",
                folder_json="folder",
                pattern_json="export*.json",
                key_mapping="url",
                pattern_urls="https*",
            )
            vr = m.validate_output()
            assert vr.has_errors_or_fatals()

    def test_validate_output_warning_when_no_files(self) -> None:
        with (
            patch("models.sourcing_urls.urls_discover_item_model.folder_exists", return_value=True),
            patch("models.sourcing_urls.urls_discover_item_model.count_files_in_folder", return_value=0),
        ):
            m = UrlsDiscoverItemModel(
                id_discover="x",
                folder_json="folder",
                pattern_json="export*.json",
                key_mapping="url",
                pattern_urls="https*",
            )
            vr = m.validate_output()
            assert vr.has_warnings()
            assert not vr.has_errors_or_fatals()
