"""Factory function for building IUrlSourceProvider instances.

Selects the correct concrete scenario based on the source type string returned
by ``ExecutorView.get_url_source()``.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast

from interfaces.i_url_source_provider import IUrlSourceProvider
from models.urls_discover_entries_model import UrlsDiscoverEntriesModel
from models.urls_folder_jsons_model import UrlsFolderJsonsModel
from models.urls_folder_racs_model import UrlsFolderRacsModel
from models.urls_manual_list_model import UrlsManualListModel
from models.workflow_run_config_model import WorkflowRunConfigModel
from services.url_sources.urls_discover_entries_service import UrlsDiscoverEntriesService
from services.url_sources.urls_folder_jsons_service import UrlsFolderJsonsService
from services.url_sources.urls_folder_racs_service import UrlsFolderRacsService
from services.url_sources.urls_manual_list_service import UrlsManualListService
from shared.enums import UrlSourceTypeEnum
from shared.exception_util import UnknownUrlSourceTypeError

# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------


def build_urls_source(source: WorkflowRunConfigModel) -> IUrlSourceProvider:
    """Instantiate the appropriate URL source scenario for the given type.

    Args:
        source: A WorkflowRunConfigModel containing the URL source type and value.

    Returns:
        A concrete ``IUrlSourceProvider`` ready for iteration.

    Raises:
        UnknownUrlSourceTypeError: When ``source_type`` is not recognised.
        InvalidUrlSourceValueTypeError: When ``source_value`` has an incompatible
            type for the requested source.
    """
    stype: str = source.urls_source_provider.get_type_source().value

    if stype == UrlSourceTypeEnum.E_MANUAL_LIST.value:
        return UrlsManualListService(cast(UrlsManualListModel, source.urls_source_provider))
    if stype == UrlSourceTypeEnum.E_FOLDER_RACS.value:
        return UrlsFolderRacsService(cast(UrlsFolderRacsModel, source.urls_source_provider))
    if stype == UrlSourceTypeEnum.E_FOLDER_JSONS.value:
        return UrlsFolderJsonsService(cast(UrlsFolderJsonsModel, source.urls_source_provider))
    if stype == UrlSourceTypeEnum.E_DISCOVER_ENTRIES.value:
        return UrlsDiscoverEntriesService(cast(UrlsDiscoverEntriesModel, source.urls_source_provider))
    raise UnknownUrlSourceTypeError(stype)


# EOF
