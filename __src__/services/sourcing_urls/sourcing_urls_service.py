from interfaces.i_url_source_provider import IUrlSourceProvider
from models.launcher_model import LaunchModel
from services.sourcing_urls.urls_discover_entries_service import UrlsDiscoverEntriesService
from services.sourcing_urls.urls_folder_jsons_service import UrlsFolderJsonsService
from services.sourcing_urls.urls_folder_racs_service import UrlsFolderRacsService
from services.sourcing_urls.urls_manual_list_service import UrlsManualListService
from shared.enums import UrlSourceTypeEnum
from shared.error_code import ErrorCode
from shared.errors.sourcing_urls_service_error import ErrorCodeSUS

from __src__.shared.path_util import path_has_valid_syntax


class SourcingUrlsService:
    _provider_manual: UrlsManualListService
    _provider_folder_racs: UrlsFolderRacsService
    _provider_folder_jsons: UrlsFolderJsonsService
    _provider_discover: UrlsDiscoverEntriesService
    _export_folder: str
    _warmup_url: str | None

    def __init__(self):
        self._launcher: LaunchModel | None = None
        self._provider_manual = UrlsManualListService()
        self._provider_folder_racs = UrlsFolderRacsService()
        self._provider_folder_jsons = UrlsFolderJsonsService()
        self._provider_discover = UrlsDiscoverEntriesService()
        self._export_folder = ""
        self._warmup_url = None

    def get_export_folder(self) -> str:
        assert self._export_folder, "Export folder has not been set."
        return self._export_folder

    def get_warmup_url(self) -> str | None:
        return self._warmup_url

    def get_provider_urls(self) -> IUrlSourceProvider:
        if self._launcher is None:
            raise ValueError("Launcher model has not been set up.")

        if self._launcher.urls_source_type is UrlSourceTypeEnum.E_MANUAL_LIST:
            return self._provider_manual
        if self._launcher.urls_source_type is UrlSourceTypeEnum.E_FOLDER_RACS:
            return self._provider_folder_racs
        if self._launcher.urls_source_type is UrlSourceTypeEnum.E_FOLDER_JSONS:
            return self._provider_folder_jsons
        if self._launcher.urls_source_type is UrlSourceTypeEnum.E_DISCOVER_ENTRIES:
            return self._provider_discover
        raise ValueError(f"Unsupported URL source type: {self._launcher.urls_source_type}")

    def get_provider_discover(self) -> UrlsDiscoverEntriesService:
        return self._provider_discover

    def get_provider_manual(self) -> UrlsManualListService:
        return self._provider_manual

    def get_provider_folder_racs(self) -> UrlsFolderRacsService:
        return self._provider_folder_racs

    def get_provider_folder_jsons(self) -> UrlsFolderJsonsService:
        return self._provider_folder_jsons

    def set_context_scraping(self, launcher: LaunchModel, export_folder: str, warmup_url: str | None) -> None:

        self._launcher = launcher
        self._export_folder = export_folder
        self._warmup_url = warmup_url
        ustype = launcher.urls_source_type

        print(f"Export folder: {export_folder}, Warmup URL: {warmup_url}, Source type: {ustype}")

        if ustype is UrlSourceTypeEnum.E_MANUAL_LIST:
            self._provider_manual.setup_model(launcher.urls_manual_list)
            self._provider_manual.loads_urls()  # Preload and validate URLs
        elif ustype is UrlSourceTypeEnum.E_FOLDER_RACS:
            self._provider_folder_racs.setup_model(launcher.urls_folder_racs)
            self._provider_folder_racs.loads_urls()  # Preload and validate URLs
        elif ustype is UrlSourceTypeEnum.E_FOLDER_JSONS:
            self._provider_folder_jsons.setup_model(launcher.urls_folder_jsons)
            self._provider_folder_jsons.loads_urls()  # Preload and validate URLs
        elif ustype is UrlSourceTypeEnum.E_DISCOVER_ENTRIES:
            self._provider_discover.setup_model(launcher.urls_discover_entries)
            self._provider_discover.loads_urls()  # Preload and validate URLs
        else:
            raise ValueError(f"Unsupported URL source type: {ustype}")

    def is_valid(self) -> ErrorCode | None:
        """Validate the current context and return the first error found.

        Returns:
            The first validation ErrorCode, or None if the context is valid.
        """
        error: ErrorCode | None = None

        if self._launcher is None:
            error = ErrorCodeSUS.SUS_1001
        elif self._launcher.urls_source_type not in {
            UrlSourceTypeEnum.E_MANUAL_LIST,
            UrlSourceTypeEnum.E_FOLDER_RACS,
            UrlSourceTypeEnum.E_FOLDER_JSONS,
            UrlSourceTypeEnum.E_DISCOVER_ENTRIES,
        }:
            error = ErrorCodeSUS.SUS_1002
        elif not self._export_folder or not self._export_folder.strip():
            error = ErrorCodeSUS.SUS_1003
        elif not path_has_valid_syntax(self._export_folder):
            error = ErrorCodeSUS.SUS_1004
        elif not self.get_provider_urls().loads_urls():
            error = ErrorCodeSUS.SUS_1005
        elif not self.get_provider_urls().preview_next_url():
            error = ErrorCodeSUS.SUS_1006
        elif len(self.get_provider_urls().preview_next_url() or "") <= 3:
            error = ErrorCodeSUS.SUS_1007

        return error
