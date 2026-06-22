from enum import Enum


class SubtitleOriginEnum(Enum):
    E_UNSET = "UNSET"
    E_MANUAL = "MANUAL"
    E_AUTO = "AUTO"
    E_UNKNOWN = "UNKNOWN"


class SubtitleLanguageEnum(Enum):
    E_UNSET = "UNSET"
    E_FR = "fr"
    E_EN = "en"
    E_UNKNOWN = "UNKNOWN"
