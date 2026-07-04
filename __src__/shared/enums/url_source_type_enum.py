# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum


class UrlSourceTypeEnum(Enum):
    """Enumerates the supported URL source provider types."""

    E_UNSET = "UNSET"
    E_MANUAL_LIST = "MANUAL_LIST"
    E_FOLDER_RACS = "FOLDER_RACS"
    E_REFRESH_URLS = "REFRESH_URLS"
    E_UNKNOWN = "UNKNOWN"

    def to_displayable_str(self) -> str:
        """Return a human-readable French label for this URL source type."""
        if self is UrlSourceTypeEnum.E_MANUAL_LIST:
            return "Liste manuelle"
        if self is UrlSourceTypeEnum.E_FOLDER_RACS:
            return "Dossier RACS"
        if self is UrlSourceTypeEnum.E_REFRESH_URLS:
            return "Chemin vers CSV"
        return "Type inconnu"


# EOF
