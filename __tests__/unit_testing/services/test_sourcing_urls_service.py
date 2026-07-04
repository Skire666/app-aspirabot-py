"""Tests for services/sourcing_urls/sourcing_urls_service.py."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from models.launcher_model import LaunchModel
from services.sourcing_urls.sourcing_urls_service import SourcingUrlsService
from services.sourcing_urls.urls_folder_csv_service import UrlsFolderCsvService
from services.sourcing_urls.urls_folder_racs_service import UrlsFolderRacsService
from services.sourcing_urls.urls_manual_list_service import UrlsManualListService
from shared.enums import UrlSourceTypeEnum
from shared.exception_util import UnknownUrlSourceTypeError, UrlSourceLauncherNotInitializedError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_service() -> tuple[SourcingUrlsService, MagicMock, MagicMock, MagicMock, MagicMock]:
    provider_manual = MagicMock(spec=UrlsManualListService)
    provider_racs = MagicMock(spec=UrlsFolderRacsService)
    provider_jsons = MagicMock(spec=UrlsFolderCsvService)
    svc = SourcingUrlsService(
        provider_manual=provider_manual, provider_folder_racs=provider_racs, provider_folder_csv=provider_jsons
    )
    return svc, provider_manual, provider_racs, provider_jsons


def _make_launcher(source_type: UrlSourceTypeEnum = UrlSourceTypeEnum.E_MANUAL_LIST) -> MagicMock:
    launcher = MagicMock(spec=LaunchModel)
    launcher.urls_source_type = source_type
    launcher.urls_manual_list = MagicMock()
    launcher.urls_folder_racs = MagicMock()
    launcher.urls_folder_csv = MagicMock()
    return launcher


# ---------------------------------------------------------------------------
# __init__ / simple getters
# ---------------------------------------------------------------------------


class TestInit:
    def test_get_export_folder_raises_when_not_set(self) -> None:
        svc, *_ = _make_service()
        with pytest.raises(AssertionError):
            svc.get_export_folder()

    def test_get_warmup_url_none_by_default(self) -> None:
        svc, *_ = _make_service()
        assert svc.get_warmup_url() is None

    def test_get_provider_manual_returns_instance(self) -> None:
        svc, manual, *_ = _make_service()
        assert svc.get_provider_manual() is manual

    def test_get_provider_folder_racs_returns_instance(self) -> None:
        svc, _, racs, *_ = _make_service()
        assert svc.get_provider_folder_racs() is racs

    def test_get_provider_folder_csv_returns_instance(self) -> None:
        svc, _, _, jsons, _ = _make_service()
        assert svc.get_provider_folder_csv() is jsons


# ---------------------------------------------------------------------------
# get_provider_urls — without context
# ---------------------------------------------------------------------------


class TestGetProviderUrlsNoContext:
    def test_raises_when_no_launcher_set(self) -> None:
        svc, *_ = _make_service()
        with pytest.raises(UrlSourceLauncherNotInitializedError):
            svc.get_provider_urls()


# ---------------------------------------------------------------------------
# set_context_scraping — per source type
# ---------------------------------------------------------------------------


class TestSetContextScraping:
    def test_sets_export_folder_and_warmup(self) -> None:
        svc, manual, *_ = _make_service()
        launcher = _make_launcher(UrlSourceTypeEnum.E_MANUAL_LIST)
        manual.is_ready_to_consum_urls.return_value = True

        svc.set_context_scraping(launcher, "export/path", "http://warmup.com")

        assert svc.get_export_folder() == "export/path"
        assert svc.get_warmup_url() == "http://warmup.com"

    def test_manual_list_calls_setup_and_loads(self) -> None:
        svc, manual, *_ = _make_service()
        launcher = _make_launcher(UrlSourceTypeEnum.E_MANUAL_LIST)

        svc.set_context_scraping(launcher, "out", None)

        manual.setup_model.assert_called_once_with(launcher.urls_manual_list)
        manual.is_ready_to_consum_urls.assert_called_once()

    def test_folder_racs_calls_setup_and_loads(self) -> None:
        svc, _, racs, *_ = _make_service()
        launcher = _make_launcher(UrlSourceTypeEnum.E_FOLDER_RACS)

        svc.set_context_scraping(launcher, "out", None)

        racs.setup_model.assert_called_once_with(launcher.urls_folder_racs)
        racs.is_ready_to_consum_urls.assert_called_once()

    def test_unknown_source_type_raises(self) -> None:
        svc, *_ = _make_service()
        launcher = _make_launcher(UrlSourceTypeEnum.E_UNKNOWN)

        with pytest.raises(UnknownUrlSourceTypeError):
            svc.set_context_scraping(launcher, "out", None)


# ---------------------------------------------------------------------------
# get_provider_urls — with context set
# ---------------------------------------------------------------------------


class TestGetProviderUrlsWithContext:
    def test_returns_manual_provider(self) -> None:
        svc, manual, *_ = _make_service()
        launcher = _make_launcher(UrlSourceTypeEnum.E_MANUAL_LIST)
        svc.set_context_scraping(launcher, "out", None)
        assert svc.get_provider_urls() is manual

    def test_returns_racs_provider(self) -> None:
        svc, _, racs, *_ = _make_service()
        launcher = _make_launcher(UrlSourceTypeEnum.E_FOLDER_RACS)
        svc.set_context_scraping(launcher, "out", None)
        assert svc.get_provider_urls() is racs

    def test_returns_jsons_provider(self) -> None:
        svc, _, _, jsons, _ = _make_service()
        launcher = _make_launcher(UrlSourceTypeEnum.E_REFRESH_URLS)
        svc.set_context_scraping(launcher, "out", None)
        assert svc.get_provider_urls() is jsons


# ---------------------------------------------------------------------------
# validate — no launcher
# ---------------------------------------------------------------------------


class TestValidateNoLauncher:
    def test_returns_error_when_no_launcher(self) -> None:
        svc, *_ = _make_service()
        result = svc.validate()
        assert result.has_errors_or_fatals()


# ---------------------------------------------------------------------------
# validate — export path checks
# ---------------------------------------------------------------------------


class TestValidateExportPath:
    def _setup(self, svc: SourcingUrlsService, export_folder: str) -> None:
        svc._launcher = _make_launcher(UrlSourceTypeEnum.E_MANUAL_LIST)
        svc._export_folder = export_folder

    def test_empty_export_folder_returns_error(self) -> None:
        svc, *_ = _make_service()
        self._setup(svc, "")
        result = svc.validate()
        assert result.has_errors_or_fatals()

    def test_dot_export_folder_returns_error(self) -> None:
        svc, *_ = _make_service()
        self._setup(svc, ".")
        result = svc.validate()
        assert result.has_errors_or_fatals()

    def test_slash_prefixed_export_folder_returns_error(self) -> None:
        svc, *_ = _make_service()
        self._setup(svc, "/absolute/path")
        result = svc.validate()
        assert result.has_errors_or_fatals()

    def test_invalid_path_syntax_returns_error(self) -> None:
        svc, *_ = _make_service()
        self._setup(svc, "<invalid>")
        result = svc.validate()
        assert result.has_errors_or_fatals()


# ---------------------------------------------------------------------------
# validate — URL provider checks
# ---------------------------------------------------------------------------


class TestValidateUrlProvider:
    def _setup_with_manual(self, svc: SourcingUrlsService, provider: MagicMock, export: str = "valid/out") -> None:
        svc._launcher = _make_launcher(UrlSourceTypeEnum.E_MANUAL_LIST)
        svc._export_folder = export

    def test_no_urls_loaded_returns_error(self) -> None:
        svc, manual, *_ = _make_service()
        self._setup_with_manual(svc, manual)
        manual.is_ready_to_consum_urls.return_value = False

        result = svc.validate()
        assert result.has_errors_or_fatals()

    def test_no_next_url_returns_error(self) -> None:
        svc, manual, *_ = _make_service()
        self._setup_with_manual(svc, manual)
        manual.is_ready_to_consum_urls.return_value = True
        manual.read_current_url.return_value = None

        result = svc.validate()
        assert result.has_errors_or_fatals()

    def test_valid_url_with_zero_count_returns_error(self) -> None:
        svc, manual, *_ = _make_service()
        self._setup_with_manual(svc, manual)
        manual.is_ready_to_consum_urls.return_value = True
        manual.read_current_url.return_value = "https://example.com"
        manual.preview_all_urls.return_value = ["https://a.com"] * 4
        manual.count_urls.return_value = 0

        result = svc.validate()
        assert result.has_errors_or_fatals()

    def test_valid_url_small_count_no_issues(self) -> None:
        svc, manual, *_ = _make_service()
        self._setup_with_manual(svc, manual)
        manual.is_ready_to_consum_urls.return_value = True
        manual.read_current_url.return_value = "https://example.com"
        manual.preview_all_urls.return_value = ["https://a.com"] * 5
        manual.count_urls.return_value = 5

        result = svc.validate()
        assert not result.has_errors_or_fatals()

    def test_large_count_over_100_adds_warning(self) -> None:
        svc, manual, *_ = _make_service()
        self._setup_with_manual(svc, manual)
        manual.is_ready_to_consum_urls.return_value = True
        manual.read_current_url.return_value = "https://example.com"
        manual.preview_all_urls.return_value = ["https://a.com"] * 5
        manual.count_urls.return_value = 500

        result = svc.validate()
        assert not result.has_errors_or_fatals()
        assert result.has_issues()

    def test_very_large_count_over_1000_adds_warning(self) -> None:
        svc, manual, *_ = _make_service()
        self._setup_with_manual(svc, manual)
        manual.is_ready_to_consum_urls.return_value = True
        manual.read_current_url.return_value = "https://example.com"
        manual.preview_all_urls.return_value = ["https://a.com"] * 5
        manual.count_urls.return_value = 2000

        result = svc.validate()
        assert not result.has_errors_or_fatals()
        assert result.has_issues()
