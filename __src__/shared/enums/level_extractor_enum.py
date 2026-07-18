# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum


class LevelExtractorEnum(Enum):
    """Enumerates the types of events that can be logged during scraping."""

    E_UNSET = "UNSET"
    E_E0_MANUAL_ENTRY = "e0"  # entrée manuelle
    E_E1_LIST_LINKS = "e1"  # liens basiques
    E_E2_DISCOVER = "e2"  # discover (minimaliste)
    E_E3_BASIC_INFO = "e3"  # fiche basique (JS)
    E_E4_EXTEND_INFO = "e4"  # fiche détaillée (JS)
    E_E5_API_INFO = "e5"  # complet (souvent API)
    E_E6_AGGREGATE = "e6"  # agrégation des sources
    E_UNKNOWN = "UNKNOWN"

    @classmethod
    def view_to_enum(cls, view: str | None) -> LevelExtractorEnum:
        """Convert a view string to the corresponding enum value."""
        if view:
            for enum_value in cls:
                if view.startswith(enum_value.value):
                    return enum_value
        return cls.E_E0_MANUAL_ENTRY  # default to E0_EMPTY if no match found

    @classmethod
    def enum_to_view(cls, enum_value: LevelExtractorEnum | str) -> str:
        """Convert an enum value (or its raw string value, e.g. after JSON round-trip) to the view string."""
        try:
            member = cls(enum_value)
        except ValueError:
            return C_LEVEL_EXTRACTOR_TO_I18N_FRA[cls.E_E0_MANUAL_ENTRY]
        if member in C_LEVEL_EXTRACTOR_TO_I18N_FRA:
            return C_LEVEL_EXTRACTOR_TO_I18N_FRA[member]
        return C_LEVEL_EXTRACTOR_TO_I18N_FRA[cls.E_E0_MANUAL_ENTRY]

    @classmethod
    def to_displayable_list(cls) -> list[str]:
        """Return a list of all enum values as strings."""
        return [
            C_LEVEL_EXTRACTOR_TO_I18N_FRA[LevelExtractorEnum.E_E0_MANUAL_ENTRY],
            C_LEVEL_EXTRACTOR_TO_I18N_FRA[LevelExtractorEnum.E_E1_LIST_LINKS],
            C_LEVEL_EXTRACTOR_TO_I18N_FRA[LevelExtractorEnum.E_E2_DISCOVER],
            C_LEVEL_EXTRACTOR_TO_I18N_FRA[LevelExtractorEnum.E_E3_BASIC_INFO],
            C_LEVEL_EXTRACTOR_TO_I18N_FRA[LevelExtractorEnum.E_E4_EXTEND_INFO],
            C_LEVEL_EXTRACTOR_TO_I18N_FRA[LevelExtractorEnum.E_E5_API_INFO],
            C_LEVEL_EXTRACTOR_TO_I18N_FRA[LevelExtractorEnum.E_E6_AGGREGATE],
        ]


C_LEVEL_EXTRACTOR_TO_I18N_FRA: dict[LevelExtractorEnum, str] = {
    LevelExtractorEnum.E_UNSET: "Non défini",
    LevelExtractorEnum.E_E0_MANUAL_ENTRY: "e0 (entrée manuelle)",
    LevelExtractorEnum.E_E1_LIST_LINKS: "e1 (liens basiques)",
    LevelExtractorEnum.E_E2_DISCOVER: "e2 (discover (minimaliste))",
    LevelExtractorEnum.E_E3_BASIC_INFO: "e3 (fiche basique / JS)",
    LevelExtractorEnum.E_E4_EXTEND_INFO: "e4 (fiche détaillée / JS)",
    LevelExtractorEnum.E_E5_API_INFO: "e5 (fiche complète / API)",
    LevelExtractorEnum.E_E6_AGGREGATE: "e6 (agrégation des sources)",
    LevelExtractorEnum.E_UNKNOWN: "Inconnu",
}

# EOF
