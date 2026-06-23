# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum


class SubtitleOriginEnum(Enum):
    """Enum for the origin (manual or auto-generated) of a YouTube subtitle track."""

    E_UNSET = "UNSET"
    E_MANUAL = "MANUAL"
    E_AUTO = "AUTO"
    E_UNKNOWN = "UNKNOWN"


class SubtitleLanguageEnum(Enum):
    """Enum for the language of a YouTube subtitle track (FR, EN, or unknown)."""

    E_UNSET = "UNSET"
    E_FR = "fr"
    E_EN = "en"
    E_UNKNOWN = "UNKNOWN"


# EOF
