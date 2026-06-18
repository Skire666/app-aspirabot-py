# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging

from interfaces.i_url_source_provider import IUrlSourceProvider
from models.launcher_model import LaunchModel
from services.sourcing_urls.urls_discover_entries_service import UrlsDiscoverEntriesService
from services.sourcing_urls.urls_folder_jsons_service import UrlsFolderJsonsService
from services.sourcing_urls.urls_folder_racs_service import UrlsFolderRacsService
from services.sourcing_urls.urls_manual_list_service import UrlsManualListService
from shared.enums import SeverityEnum, UrlSourceTypeEnum
from shared.errors.sourcing_urls_service_error import ErrorCodeSUS
from shared.exception_util import UnknownUrlSourceTypeError, UrlSourceLauncherNotInitializedError
from shared.path_util import path_has_valid_syntax
from shared.validation_result import ValidationResult

_C_MIN_URL_LENGTH = 3  # URLs shorter than this are treated as empty/invalid.
_C_MAX_URL_WARNING_COUNT = 100  # Warn when the URL queue exceeds this threshold.


class SourcingUrlsService:
    """Orchestrates URL sourcing across all provider strategies.

    Holds references to the four URL provider implementations and delegates
    to the one matching the active launcher's source type. Context must be
    set via ``set_context_scraping`` before any URL is consumed.
    """

    _export_folder: str
    _warmup_url: str | None

    def __init__(
        self,
        provider_manual: UrlsManualListService,
        provider_folder_racs: UrlsFolderRacsService,
        provider_folder_jsons: UrlsFolderJsonsService,
        provider_discover: UrlsDiscoverEntriesService,
    ) -> None:
        """Initialise the service with all four injected URL providers.

        Args:
            provider_manual: Provider for manual URL lists.
            provider_folder_racs: Provider for RAC shortcut folders.
            provider_folder_jsons: Provider for JSON file folders.
            provider_discover: Provider for discovery-based URL sets.
        """
        self._logger = logging.getLogger(__name__)
        self._launcher: LaunchModel | None = None
        self._provider_manual = provider_manual
        self._provider_folder_racs = provider_folder_racs
        self._provider_folder_jsons = provider_folder_jsons
        self._provider_discover = provider_discover
        self._export_folder = ""
        self._warmup_url = None

    def get_export_folder(self) -> str:
        """Return the configured export folder path.

        Returns:
            The export folder path string.
        """
        assert self._export_folder, "Export folder has not been set."
        return self._export_folder

    def get_warmup_url(self) -> str | None:
        """Return the optional warmup URL.

        Returns:
            The warmup URL, or None when not configured.
        """
        return self._warmup_url

    def get_provider_urls(self) -> IUrlSourceProvider:
        """Return the active URL provider for the current launcher source type.

        Returns:
            The provider matching the launcher's URL source type.

        Raises:
            UrlSourceNotReadyError: When no launcher context has been set.
            UnknownUrlSourceTypeError: When the source type is not supported.
        """
        if self._launcher is None:
            raise UrlSourceLauncherNotInitializedError()

        if self._launcher.urls_source_type is UrlSourceTypeEnum.E_MANUAL_LIST:
            return self._provider_manual
        if self._launcher.urls_source_type is UrlSourceTypeEnum.E_FOLDER_RACS:
            return self._provider_folder_racs
        if self._launcher.urls_source_type is UrlSourceTypeEnum.E_FOLDER_JSONS:
            return self._provider_folder_jsons
        if self._launcher.urls_source_type is UrlSourceTypeEnum.E_DISCOVER_ENTRIES:
            return self._provider_discover
        raise UnknownUrlSourceTypeError(str(self._launcher.urls_source_type))

    def get_provider_discover(self) -> UrlsDiscoverEntriesService:
        """Return the discovery provider directly.

        Returns:
            The UrlsDiscoverEntriesService instance.
        """
        return self._provider_discover

    def get_provider_manual(self) -> UrlsManualListService:
        """Return the manual-list provider directly.

        Returns:
            The UrlsManualListService instance.
        """
        return self._provider_manual

    def get_provider_folder_racs(self) -> UrlsFolderRacsService:
        """Return the RAC folder provider directly.

        Returns:
            The UrlsFolderRacsService instance.
        """
        return self._provider_folder_racs

    def get_provider_folder_jsons(self) -> UrlsFolderJsonsService:
        """Return the JSON folder provider directly.

        Returns:
            The UrlsFolderJsonsService instance.
        """
        return self._provider_folder_jsons

    def set_context_scraping(self, launcher: LaunchModel, export_folder: str, warmup_url: str | None) -> None:
        """Configure the scraping context and preload the active URL provider.

        Args:
            launcher: The launch profile defining the URL source type.
            export_folder: Destination folder for scraped output.
            warmup_url: Optional URL to load before the main sequence.

        Raises:
            UnknownUrlSourceTypeError: When the launcher source type is not supported.
        """
        assert launcher is not None, "Launcher context must be provided and valid."
        self._launcher = launcher
        self._export_folder = export_folder
        self._warmup_url = warmup_url
        ustype = launcher.urls_source_type

        if ustype is UrlSourceTypeEnum.E_MANUAL_LIST:
            self._provider_manual.setup_model(launcher.urls_manual_list)
            self._provider_manual.loads_urls()
        elif ustype is UrlSourceTypeEnum.E_FOLDER_RACS:
            self._provider_folder_racs.setup_model(launcher.urls_folder_racs)
            self._provider_folder_racs.loads_urls()
        elif ustype is UrlSourceTypeEnum.E_FOLDER_JSONS:
            self._provider_folder_jsons.setup_model(launcher.urls_folder_jsons)
            self._provider_folder_jsons.loads_urls()
        elif ustype is UrlSourceTypeEnum.E_DISCOVER_ENTRIES:
            self._provider_discover.setup_model(launcher.urls_discover_entries)
            self._provider_discover.loads_urls()
        else:
            raise UnknownUrlSourceTypeError(str(ustype))

    def _validate_launcher_config(self, rs: ValidationResult) -> bool:
        """Validate launcher and source type. Returns True if an error was appended."""
        if self._launcher is None:
            rs.append(ErrorCodeSUS.SUS_1001, SeverityEnum.E_ERROR)
            return True
        if self._launcher.urls_source_type not in {
            UrlSourceTypeEnum.E_MANUAL_LIST,
            UrlSourceTypeEnum.E_FOLDER_RACS,
            UrlSourceTypeEnum.E_FOLDER_JSONS,
            UrlSourceTypeEnum.E_DISCOVER_ENTRIES,
        }:
            rs.append(ErrorCodeSUS.SUS_1002, SeverityEnum.E_ERROR)
            return True
        return False

    def _validate_export_path(self, rs: ValidationResult) -> bool:
        """Validate the export folder path. Returns True if an error was appended."""
        if not self._export_folder or not self._export_folder.strip():
            rs.append(ErrorCodeSUS.SUS_1003, SeverityEnum.E_ERROR)
            return True
        if not path_has_valid_syntax(self._export_folder):
            rs.append(ErrorCodeSUS.SUS_1004, SeverityEnum.E_ERROR)
            return True
        if self._export_folder.strip() in {".", "./"}:
            rs.append(ErrorCodeSUS.SUS_1008, SeverityEnum.E_ERROR)
            return True
        if self._export_folder.strip().startswith("/"):
            rs.append(ErrorCodeSUS.SUS_1009, SeverityEnum.E_ERROR)
            return True
        return False

    def _validate_url_provider(self, rs: ValidationResult) -> None:
        """Validate that the active URL provider yields usable URLs."""
        provider = self.get_provider_urls()
        if not provider.loads_urls():
            rs.append(ErrorCodeSUS.SUS_1005, SeverityEnum.E_ERROR)
            return
        if not provider.preview_next_url():
            rs.append(ErrorCodeSUS.SUS_1006, SeverityEnum.E_ERROR)
            return
        if len(provider.preview_next_url() or "") <= _C_MIN_URL_LENGTH:
            rs.append(ErrorCodeSUS.SUS_1007, SeverityEnum.E_ERROR)
            return
        count = provider.count_urls()
        if count == 0:
            rs.append(ErrorCodeSUS.SUS_1010, SeverityEnum.E_ERROR)
        elif count > _C_MAX_URL_WARNING_COUNT:
            rs.append(ErrorCodeSUS.SUS_1011, SeverityEnum.E_WARNING)

    def validate(self) -> ValidationResult:
        """Validate the current context and return any validation issues.

        Returns:
            A ValidationResult instance containing any validation issues.
        """
        rs = ValidationResult()
        if self._validate_launcher_config(rs):
            return rs
        if self._validate_export_path(rs):
            return rs
        self._validate_url_provider(rs)
        return rs


# EOF
