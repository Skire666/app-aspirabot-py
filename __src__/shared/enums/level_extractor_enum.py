# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum

C_E0_STR = "e0 (UNSET)"
C_E1_STR = "e1 (discover / minimal)"
C_E2_STR = "e2 (partial / JS)"
C_E3_STR = "e3 (complet / API)"


class LevelExtractorEnum(Enum):
    """Enumerates the types of events that can be logged during scraping."""

    E_UNSET = "UNSET"
    E_E0_EMPTY = "e0"  # wtf ???
    E_E1_DISCOVER = "e1"  # discover (minimaliste)
    E_E2_PARTIAL = "e2"  # partiel (JS à la mano)
    E_E3_COMPLET = "e3"  # complet (souvent API)
    E_UNKNOWN = "UNKNOWN"

    @classmethod
    def view_to_enum(cls, view: str) -> LevelExtractorEnum:
        """Convert a view string to the corresponding enum value."""
        for enum_value in cls:
            if view.startswith(enum_value.value):
                print(f"DEBUG: view_to_enum matched view '{view}' to enum_value '{enum_value}'")
                return enum_value
        return cls.E_E1_DISCOVER  # default to E1_DISCOVER if no match found

    @classmethod
    def enum_to_view(cls, enum_value: LevelExtractorEnum) -> str:
        """Convert an enum value to the corresponding view string."""
        print(f"DEBUG: enum_to_view called with enum_value: {enum_value}")
        if enum_value is cls.E_E1_DISCOVER:
            return C_E1_STR
        if enum_value is cls.E_E2_PARTIAL:
            return C_E2_STR
        if enum_value is cls.E_E3_COMPLET:
            return C_E3_STR
        print("DEBUG: WTF ???????")
        return C_E0_STR  # default to E0_EMPTY if no match found

    @classmethod
    def to_displayable_list(cls) -> list[str]:
        """Return a list of all enum values as strings."""
        return [C_E1_STR, C_E2_STR, C_E3_STR]


# EOF
