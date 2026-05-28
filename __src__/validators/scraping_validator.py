"""Validator for the scraping launch profile (LaunchModel)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from models.launcher_model import LaunchModel
from shared.enums import UrlSourceTypeEnum
from shared.i18n_fra import (
    C_EXEC_FOLDER_URL_SOURCE_EMPTY,
    C_EXEC_INVALID_GLOBAL_THRESHOLD,
    C_EXEC_INVALID_STEP_THRESHOLD,
    C_EXEC_NO_EXPORT_FOLDER,
    C_EXEC_NO_URL_SOURCE,
    C_EXEC_STEP_THRESHOLD_WITHOUT_STEP,
)
from validators.abstract_validator import AbstractValidator

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

_MAX_THRESHOLD = 9_999_999

_NON_MANUAL_SOURCE_TYPES = {
    UrlSourceTypeEnum.E_FOLDER.value,
    UrlSourceTypeEnum.E_JSON.value,
}


def _valid_threshold(value: int) -> bool:
    """Return True when *value* is an integer in [1, 9 999 999].

    Args:
        value: Raw integer from the launch profile.

    Returns:
        True when the threshold is within the accepted range.
    """
    return isinstance(value, int) and 1 <= value <= _MAX_THRESHOLD


# -----------------------------------------------------------------------------
# Validator
# -----------------------------------------------------------------------------


class ScrapingLaunchValidator(AbstractValidator[LaunchModel]):
    """Validates a LaunchModel before triggering a scraping session.

    All rules are domain rules (they would exist in a headless version):

    - export_folder must be non-empty.
    - url_source_type must be set.
    - url_source_value must be set when source type is folder or JSON.
    - emergency_stop_threshold must be an integer in [1, 9 999 999].
    - emergency_stop_step_id must be set (a monitoring step must be chosen).
    - emergency_stop_step_threshold must be an integer in [1, 9 999 999].
    """

    def __init__(self) -> None:
        """Define all validation rules for a scraping launch profile."""
        super().__init__()

        # Export folder
        self.rule_for(lambda p: p.export_folder, "export_folder").must(
            lambda v: bool(v and v.strip()), C_EXEC_NO_EXPORT_FOLDER
        )

        # URL source type
        self.rule_for(lambda p: p.url_source_type, "url_source_type").not_empty(
            C_EXEC_NO_URL_SOURCE
        )

        # URL source value — only required for folder/JSON sources
        self.rule_for(lambda p: p.url_source_value, "url_source_value").must(
            bool, C_EXEC_FOLDER_URL_SOURCE_EMPTY
        ).when(lambda p: p.url_source_type in _NON_MANUAL_SOURCE_TYPES)

        # Global error threshold
        self.rule_for(lambda p: p.emergency_stop_threshold, "emergency_stop_threshold").must(
            _valid_threshold, C_EXEC_INVALID_GLOBAL_THRESHOLD
        )

        # Per-step monitoring: a step must be selected
        self.rule_for(lambda p: p.emergency_stop_step_id, "emergency_stop_step_id").must(
            bool, C_EXEC_STEP_THRESHOLD_WITHOUT_STEP
        )

        # Per-step error threshold
        self.rule_for(
            lambda p: p.emergency_stop_step_threshold, "emergency_stop_step_threshold"
        ).must(_valid_threshold, C_EXEC_INVALID_STEP_THRESHOLD)


# EOF
