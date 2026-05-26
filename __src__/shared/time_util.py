"""Utility functions for converting durations between time units."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.exception_util import InvalidDurationError, InvalidTimeUnitError

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_UNITS_TIME_CONVERSION_TO_MS: dict[str, int] = {
    "m": 60 * 1000,
    "min": 60 * 1000,
    "min.": 60 * 1000,
    "s": 1000,
    "sec": 1000,
    "sec.": 1000,
    "ms": 1,
    "millisec": 1,
    "millisec.": 1,
}

C_UNITS_TIME_CONVERSION_TO_SEC: dict[str, float] = {
    "m": 60.0,
    "min": 60.0,
    "min.": 60.0,
    "s": 1.0,
    "sec": 1.0,
    "sec.": 1.0,
    "ms": 0.001,
    "millisec": 0.001,
    "millisec.": 0.001,
}

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------


def convert_to_ms(duration: int, time_unit: str) -> int:
    """Converts a duration in the given unit to milliseconds.

    Args:
        duration: Numeric duration value (must be >= 0).
        time_unit: Time unit string (e.g. "s", "ms", "min").

    Returns:
        The duration expressed in milliseconds.

    Raises:
        InvalidTimeUnitError: When time_unit is empty or unrecognized.
        InvalidDurationError: When duration is negative.
    """
    if not time_unit:
        raise InvalidTimeUnitError(time_unit)
    if time_unit not in C_UNITS_TIME_CONVERSION_TO_MS:
        raise InvalidTimeUnitError(time_unit)
    if duration <= -1:
        raise InvalidDurationError(duration)

    # convert
    return int(duration * C_UNITS_TIME_CONVERSION_TO_MS.get(time_unit))


def convert_to_sec(duration: int, time_unit: str) -> float:
    """Converts a duration in the given unit to seconds.

    Args:
        duration: Numeric duration value (must be >= 0).
        time_unit: Time unit string (e.g. "s", "ms", "min").

    Returns:
        The duration expressed in seconds.

    Raises:
        InvalidTimeUnitError: When time_unit is empty or unrecognized.
        InvalidDurationError: When duration is negative.
    """
    if not time_unit:
        raise InvalidTimeUnitError(time_unit)
    if time_unit not in C_UNITS_TIME_CONVERSION_TO_SEC:
        raise InvalidTimeUnitError(time_unit)
    if duration <= -1:
        raise InvalidDurationError(duration)

    # convert
    return float(duration * C_UNITS_TIME_CONVERSION_TO_SEC.get(time_unit))


# EOF
