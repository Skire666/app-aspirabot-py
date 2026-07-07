# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from datetime import datetime, timedelta
from enum import Enum


class RelativeDateEnum(Enum):
    """Enumerates the relative date options for filtering files in a folder-based URL source."""

    E_UNSET = "UNSET"
    E_LAST_NOW = "LAST_NOW"  # now
    E_LAST_1H = "LAST_1H"  # LAST 1 HOUR
    E_LAST_3H = "LAST_3H"  # LAST 3 HOUR
    E_LAST_1D = "LAST_1D"  # LAST 1 DAYS
    E_LAST_3D = "LAST_3D"  # LAST 3 DAYS
    E_LAST_1W = "LAST_1W"  # LAST 7 DAYS
    E_LAST_3W = "LAST_3W"  # LAST 20 DAYS
    E_LAST_1M = "LAST_1M"  # LAST 30 DAYS
    E_LAST_3M = "LAST_3M"  # LAST 90 DAYS
    E_LAST_1Y = "LAST_1Y"  # LAST 1 YEAR
    E_LAST_3Y = "LAST_3Y"  # LAST 2 YEARS
    E_LAST_99Y = "LAST_99Y"  # LAST 99 YEARS
    E_UNKNOWN = "UNKNOWN"

    def enum_to_view(self) -> str:
        """Convert this enum member to its French display label."""
        return _RELATIVE_DATE_TO_LABEL.get(self, "")

    @classmethod
    def view_to_enum(cls, value: str) -> RelativeDateEnum:
        """Convert a string value to the corresponding RelativeDateEnum member.

        Args:
            value: The string representation of the relative date.

        Returns:
            The corresponding RelativeDateEnum member, or E_UNKNOWN if not found.
        """
        return _LABEL_TO_RELATIVE_DATE.get(value, cls.E_UNKNOWN)

    @classmethod
    def any_to_enum(cls, val_enum: str | RelativeDateEnum | None) -> RelativeDateEnum:
        """Convert a string value to the corresponding RelativeDateEnum member.

        Args:
            val_enum: The value to convert to a RelativeDateEnum member.

        Returns:
            The corresponding RelativeDateEnum member, or E_UNKNOWN if not found.
        """
        try:
            return RelativeDateEnum(val_enum)
        except ValueError:
            return cls.E_UNKNOWN

    def is_lower_than(self, right: RelativeDateEnum) -> bool:
        """Determine if this enum member represents a lower (earlier) relative date than another.

        Args:
            right: Another RelativeDateEnum member to compare against.

        Returns:
            True if this member is lower than the other; False otherwise.
        """
        order = [
            RelativeDateEnum.E_UNSET,
            RelativeDateEnum.E_LAST_NOW,
            RelativeDateEnum.E_LAST_1H,
            RelativeDateEnum.E_LAST_3H,
            RelativeDateEnum.E_LAST_1D,
            RelativeDateEnum.E_LAST_3D,
            RelativeDateEnum.E_LAST_1W,
            RelativeDateEnum.E_LAST_3W,
            RelativeDateEnum.E_LAST_1M,
            RelativeDateEnum.E_LAST_3M,
            RelativeDateEnum.E_LAST_1Y,
            RelativeDateEnum.E_LAST_3Y,
            RelativeDateEnum.E_LAST_99Y,
            RelativeDateEnum.E_UNKNOWN,
        ]
        return order.index(self) < order.index(right)

    def is_valid(self) -> bool:
        """Check if the enum member is a valid relative date (not UNSET or UNKNOWN).

        Returns:
            True if the member is valid; False otherwise.
        """
        return self not in {RelativeDateEnum.E_UNSET, RelativeDateEnum.E_UNKNOWN}

    def to_datetime(self) -> datetime:
        """Convert the relative date enum to an actual datetime object.

        Returns:
            A datetime object representing the relative date.
            Falls back to approximately 99 years ago for E_UNSET or E_UNKNOWN.
        """
        return datetime.now() - _RELATIVE_DATE_TO_TIMEDELTA.get(self, timedelta(days=36135))


_RELATIVE_DATE_TO_LABEL: dict[RelativeDateEnum, str] = {
    RelativeDateEnum.E_LAST_NOW: "Maintenant",
    RelativeDateEnum.E_LAST_1H: "1 heure",
    RelativeDateEnum.E_LAST_3H: "3 heures",
    RelativeDateEnum.E_LAST_1D: "1 jour",
    RelativeDateEnum.E_LAST_3D: "3 jours",
    RelativeDateEnum.E_LAST_1W: "1 semaine",
    RelativeDateEnum.E_LAST_3W: "3 semaines",
    RelativeDateEnum.E_LAST_1M: "1 mois",
    RelativeDateEnum.E_LAST_3M: "3 mois",
    RelativeDateEnum.E_LAST_1Y: "1 an",
    RelativeDateEnum.E_LAST_3Y: "3 ans",
    RelativeDateEnum.E_LAST_99Y: "99 ans",
}
_LABEL_TO_RELATIVE_DATE: dict[str, RelativeDateEnum] = {v: k for k, v in _RELATIVE_DATE_TO_LABEL.items()}

_RELATIVE_DATE_TO_TIMEDELTA: list[timedelta] = [
    timedelta(0),
    timedelta(minutes=5),
    timedelta(minutes=10),
    timedelta(minutes=30),
    timedelta(hours=1),
    timedelta(hours=3),
    timedelta(days=1),
    timedelta(days=3),
    timedelta(weeks=1),
    timedelta(weeks=3),
    timedelta(days=30),
    timedelta(days=90),
    timedelta(days=365),
    timedelta(days=1095),
    timedelta(days=36135),
]


def get_quality_of_updating_date(current: datetime, modified: datetime) -> int:
    gap = current - modified
    nbr_max = len(_RELATIVE_DATE_TO_TIMEDELTA) + 1

    # Date de modification dans le futur -> on considère "Maintenant"
    if gap < timedelta(0):
        return nbr_max

    for i, threshold in enumerate(_RELATIVE_DATE_TO_TIMEDELTA):  # déjà trié croissant
        if gap <= threshold:
            return nbr_max - i

    # Au-delà de 99 ans : on plafonne sur le dernier palier
    return 1


# EOF
