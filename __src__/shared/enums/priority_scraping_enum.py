# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum


class PriorityScrapingEnum(Enum):
    """Enumerates the priority options for scraping URLs."""

    E_UNSET = "UNSET"
    E_FIRST_CREATED_BY_NEW = "LAST_CREATED_BY_NEW"  # last created by new
    E_LAST_CREATED_BY_OLD = "LAST_CREATED_BY_OLD"  # last created by old
    E_LAST_MODIFIED_BY_NEW = "LAST_MODIFIED_BY_NEW"  # last modified by new
    E_LAST_MODIFIED_BY_OLD = "LAST_MODIFIED_BY_OLD"  # last modified by old
    E_QUALITY_BY_LOW = "QUALITY_BY_LOW"  # worst quality
    E_LOW_EXTRACTOR_NEWEST = "LOW_EXTRACTOR_NEWEST"  # low extractor newest
    E_LOW_EXTRACTOR_OLDEST = "LOW_EXTRACTOR_OLDEST"  # low extractor oldest
    E_UNKNOWN = "UNKNOWN"

    def enum_to_view(self) -> str:
        """Convert this enum member to its French display label."""
        return _PRIORITY_SCRAPING_TO_LABEL.get(self, "")

    @classmethod
    def view_to_enum(cls, value: str) -> PriorityScrapingEnum:
        """Convert a string value to the corresponding PriorityScrapingEnum member.

        Args:
            value: The string representation of the priority scraping option.

        Returns:
            The corresponding PriorityScrapingEnum member, or E_UNKNOWN if not found.
        """
        return _LABEL_TO_PRIORITY_SCRAPING.get(value, cls.E_UNKNOWN)

    @staticmethod
    def any_to_enum(val_enum: str | PriorityScrapingEnum | None) -> PriorityScrapingEnum:
        """Convert a string value to the corresponding PriorityScrapingEnum member.

        Args:
            val_enum: The value to convert to a PriorityScrapingEnum member.

        Returns:
            The corresponding PriorityScrapingEnum member, or E_UNKNOWN if not found.
        """
        try:
            return PriorityScrapingEnum(val_enum)
        except ValueError:
            return PriorityScrapingEnum.E_UNKNOWN

    def is_valid(self) -> bool:
        """Check if this enum member is a valid priority scraping option.

        Returns:
            True if the enum member is valid, False otherwise.
        """
        return self in {
            PriorityScrapingEnum.E_FIRST_CREATED_BY_NEW,
            PriorityScrapingEnum.E_LAST_CREATED_BY_OLD,
            PriorityScrapingEnum.E_LAST_MODIFIED_BY_NEW,
            PriorityScrapingEnum.E_LAST_MODIFIED_BY_OLD,
            PriorityScrapingEnum.E_QUALITY_BY_LOW,
            PriorityScrapingEnum.E_LOW_EXTRACTOR_NEWEST,
            PriorityScrapingEnum.E_LOW_EXTRACTOR_OLDEST,
        }

    @staticmethod
    def to_displayable_list() -> list[str]:
        """Return a list of all valid enum values as their French display labels."""
        return [
            PriorityScrapingEnum.E_FIRST_CREATED_BY_NEW.enum_to_view(),
            PriorityScrapingEnum.E_LAST_CREATED_BY_OLD.enum_to_view(),
            PriorityScrapingEnum.E_LAST_MODIFIED_BY_NEW.enum_to_view(),
            PriorityScrapingEnum.E_LAST_MODIFIED_BY_OLD.enum_to_view(),
            PriorityScrapingEnum.E_QUALITY_BY_LOW.enum_to_view(),
            PriorityScrapingEnum.E_LOW_EXTRACTOR_NEWEST.enum_to_view(),
            PriorityScrapingEnum.E_LOW_EXTRACTOR_OLDEST.enum_to_view(),
        ]


_PRIORITY_SCRAPING_TO_LABEL: dict[PriorityScrapingEnum, str] = {
    PriorityScrapingEnum.E_FIRST_CREATED_BY_NEW: "Ordre de création -> Prendre 1er ",
    PriorityScrapingEnum.E_LAST_CREATED_BY_OLD: "Ordre de création -> Prendre dernier",
    PriorityScrapingEnum.E_LAST_MODIFIED_BY_NEW: "Ordre de modification -> Prendre récents",
    PriorityScrapingEnum.E_LAST_MODIFIED_BY_OLD: "Ordre de modification -> Prendre anciens",
    PriorityScrapingEnum.E_QUALITY_BY_LOW: "Qualité faible à compléter",
    PriorityScrapingEnum.E_LOW_EXTRACTOR_NEWEST: "Nouvelles entrées à compléter",
    PriorityScrapingEnum.E_LOW_EXTRACTOR_OLDEST: "Anciennes entrées à compléter",
}

_LABEL_TO_PRIORITY_SCRAPING: dict[str, PriorityScrapingEnum] = {
    _PRIORITY_SCRAPING_TO_LABEL[
        PriorityScrapingEnum.E_FIRST_CREATED_BY_NEW
    ]: PriorityScrapingEnum.E_FIRST_CREATED_BY_NEW,
    _PRIORITY_SCRAPING_TO_LABEL[PriorityScrapingEnum.E_LAST_CREATED_BY_OLD]: PriorityScrapingEnum.E_LAST_CREATED_BY_OLD,
    _PRIORITY_SCRAPING_TO_LABEL[
        PriorityScrapingEnum.E_LAST_MODIFIED_BY_NEW
    ]: PriorityScrapingEnum.E_LAST_MODIFIED_BY_NEW,
    _PRIORITY_SCRAPING_TO_LABEL[
        PriorityScrapingEnum.E_LAST_MODIFIED_BY_OLD
    ]: PriorityScrapingEnum.E_LAST_MODIFIED_BY_OLD,
    _PRIORITY_SCRAPING_TO_LABEL[PriorityScrapingEnum.E_QUALITY_BY_LOW]: PriorityScrapingEnum.E_QUALITY_BY_LOW,
    _PRIORITY_SCRAPING_TO_LABEL[
        PriorityScrapingEnum.E_LOW_EXTRACTOR_NEWEST
    ]: PriorityScrapingEnum.E_LOW_EXTRACTOR_NEWEST,
    _PRIORITY_SCRAPING_TO_LABEL[
        PriorityScrapingEnum.E_LOW_EXTRACTOR_OLDEST
    ]: PriorityScrapingEnum.E_LOW_EXTRACTOR_OLDEST,
}


# EOF
