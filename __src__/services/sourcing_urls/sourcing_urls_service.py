from interfaces.i_url_source_provider import IUrlSourceProvider
from models.launcher_model import LaunchModel
from services.sourcing_urls.urls_discover_entries_service import UrlsDiscoverEntriesService
from services.sourcing_urls.urls_folder_jsons_service import UrlsFolderJsonsService
from services.sourcing_urls.urls_folder_racs_service import UrlsFolderRacsService
from services.sourcing_urls.urls_manual_list_service import UrlsManualListService
from shared.enums import UrlSourceTypeEnum


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

    def get_warmup_url(self) -> str:
        assert self._warmup_url is not None, "Warmup URL has not been set."
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

    def setup_context_scraping(self, launcher: LaunchModel) -> None:
        self._launcher = launcher
        ustype = launcher.urls_source_type

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
