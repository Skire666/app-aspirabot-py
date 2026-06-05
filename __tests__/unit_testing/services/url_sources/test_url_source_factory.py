"""Tests for services/url_sources/url_source_factory.py."""

from __future__ import annotations

import pytest
from services.url_sources.folder_url_source import FolderUrlSourceProvider
from services.url_sources.json_url_source import JsonUrlSourceProvider
from services.url_sources.manual_url_source import ManualUrlSourceProvider
from services.url_sources.url_source_factory import build_url_source_scenario
from shared.enums import UrlSortOrderEnum
from shared.exception_util import InvalidUrlSourceValueTypeError, UnknownUrlSourceTypeError


class TestBuildUrlSourceScenario:
    def test_manual_with_list_returns_manual_provider(self) -> None:
        provider = build_url_source_scenario("MANUAL", ["http://example.com"])
        assert isinstance(provider, ManualUrlSourceProvider)

    def test_manual_with_empty_list(self) -> None:
        provider = build_url_source_scenario("MANUAL", [])
        assert isinstance(provider, ManualUrlSourceProvider)
        assert not provider.load_url_if_available()

    def test_manual_with_str_raises_type_error(self) -> None:
        with pytest.raises(InvalidUrlSourceValueTypeError):
            build_url_source_scenario("MANUAL", "/some/path")  # type: ignore[arg-type]

    def test_folder_with_str_returns_folder_provider(self, tmp_path: object) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            provider = build_url_source_scenario("FOLDER", d)
            assert isinstance(provider, FolderUrlSourceProvider)

    def test_folder_with_list_raises_type_error(self) -> None:
        with pytest.raises(InvalidUrlSourceValueTypeError):
            build_url_source_scenario("FOLDER", ["http://x.com"])  # type: ignore[arg-type]

    def test_json_with_str_returns_json_provider(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            provider = build_url_source_scenario("JSON", d)
            assert isinstance(provider, JsonUrlSourceProvider)

    def test_json_with_list_raises_type_error(self) -> None:
        with pytest.raises(InvalidUrlSourceValueTypeError):
            build_url_source_scenario("JSON", ["url"])  # type: ignore[arg-type]

    def test_unknown_type_raises(self) -> None:
        with pytest.raises(UnknownUrlSourceTypeError):
            build_url_source_scenario("CSV", "/some/path")

    def test_folder_passes_sort_order(self, tmp_path: object) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            provider = build_url_source_scenario("FOLDER", d, UrlSortOrderEnum.E_NAME_ASC)
            assert isinstance(provider, FolderUrlSourceProvider)
            assert provider._sort_order is UrlSortOrderEnum.E_NAME_ASC
