"""Shared converters for Aspirabot application."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from typing import Literal, cast

from shared.enums import WaitUntilEnum

# -----------------------------------------------------------------------------
# Codes
# -----------------------------------------------------------------------------


def convert_str_to_wait_until(wait_until: str) -> WaitUntilEnum:
    """Convert a wait_until string to a WaitUntilEnum value."""
    mapping: dict[str, WaitUntilEnum] = {
        "domcontentloaded": WaitUntilEnum.E_DOM,
        "load": WaitUntilEnum.E_LOAD,
        "networkidle": WaitUntilEnum.E_IDLE,
    }
    return mapping.get(wait_until, WaitUntilEnum.E_UNKNOWN)


def convert_wait_until_to_literals(wait_until: WaitUntilEnum) -> Literal["domcontentloaded", "load", "networkidle"]:
    """Convert a WaitUntilEnum value to a literal string for Playwright."""
    return cast(Literal["domcontentloaded", "load", "networkidle"], wait_until.value)


# EOF
