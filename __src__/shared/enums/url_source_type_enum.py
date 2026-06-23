# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum


class UrlSourceTypeEnum(Enum):
    """Enumerates the supported URL source provider types."""

    E_UNSET = "UNSET"
    E_MANUAL_LIST = "MANUAL_LIST"
    E_FOLDER_RACS = "FOLDER_RACS"
    E_FOLDER_JSONS = "FOLDER_JSONS"
    E_DISCOVER_ENTRIES = "DISCOVER_ENTRIES"
    E_UNKNOWN = "UNKNOWN"

    def to_displayable_str(self) -> str:
        """Return a human-readable French label for this URL source type."""
        if self is UrlSourceTypeEnum.E_MANUAL_LIST:
            return "Liste manuelle"
        if self is UrlSourceTypeEnum.E_FOLDER_RACS:
            return "Dossier RACS"
        if self is UrlSourceTypeEnum.E_FOLDER_JSONS:
            return "Dossier JSON"
        if self is UrlSourceTypeEnum.E_DISCOVER_ENTRIES:
            return "Lire nouveautés"
        return "Type inconnu"


# EOF
