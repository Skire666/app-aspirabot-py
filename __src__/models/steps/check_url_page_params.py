"""Typed parameter model for the CHECK_URL_PAGE step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, cast

from models.steps.base_step_params import BaseStepParams, step_label
from pydantic import ValidationInfo, model_validator
from shared.i18n_fra import ERROR_TEMPLATES


class CheckUrlPageParams(BaseStepParams):
    """Parameters for the check URL page scraping step."""

    check_domain: bool
    check_path: bool
    comment: str = ""

    @model_validator(mode="before")
    @classmethod
    def check_at_least_one_bool(cls, data: Any, info: ValidationInfo) -> dict[str, Any]:  # noqa: ANN401
        """Validate that at least one of check_domain or check_path is True."""
        if not isinstance(data, dict) or not info.context:
            return cast(dict[str, Any], data)
        d = cast(dict[str, Any], data)
        if not d.get("check_domain") and not d.get("check_path"):
            raise ValueError(ERROR_TEMPLATES["check_url_page_nothing_to_check"].format(step=step_label(info.context)))
        return d


# EOF
