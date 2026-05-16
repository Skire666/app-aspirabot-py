# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


def convert_to_ms(duration: int, time_unit: str) -> int | None:
    """Returns timeout in ms or None when duration is 0."""
    if not time_unit:
        raise ValueError("Time unit is required for conversion to ms.")
    if time_unit not in C_UNITS_TIME_CONVERSION_TO_MS:
        raise ValueError(f"Invalid time unit for conversion to ms: {time_unit}")
    if duration <= -1:
        raise ValueError(f"Invalid duration for conversion to ms: {duration}")

    # convert
    return int(duration * C_UNITS_TIME_CONVERSION_TO_MS.get(time_unit))


def convert_to_sec(duration: int, time_unit: str) -> float | None:
    """Returns timeout in seconds or None when duration is 0."""
    if not time_unit:
        raise ValueError("Time unit is required for conversion to sec.")
    if time_unit not in C_UNITS_TIME_CONVERSION_TO_SEC:
        raise ValueError(f"Invalid time unit for conversion to sec: {time_unit}")
    if duration <= -1:
        raise ValueError(f"Invalid duration for conversion to sec: {duration}")

    # convert
    return float(duration * C_UNITS_TIME_CONVERSION_TO_SEC.get(time_unit))


# EOF
