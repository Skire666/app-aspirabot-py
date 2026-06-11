"""Typed parameter model for the CHECK_URL_PAGE step."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from models.steps.base_step_params import extract_pydantic_errors, step_label
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, model_validator
from shared.i18n_fra import ERROR_TEMPLATES

if TYPE_CHECKING:
    from models.steps_context_model import StepsCollections


class CheckUrlPageParams(BaseModel):
    """Parameters for the check URL page scraping step."""

    model_config = ConfigDict(frozen=True)

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

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict (enum fields serialized as their string values)."""
        return self.model_dump(mode="json")

    def validate_with_context(self, step_index: int, steps_context: StepsCollections, step_id: str) -> list[str]:
        """Validate params in workflow context and return French error strings."""
        ctx: dict[str, Any] = {"step_index": step_index, "steps_context": steps_context, "step_id": step_id}
        try:
            type(self).model_validate(self.to_dict(), context=ctx)
        except ValidationError as exc:
            return extract_pydantic_errors(exc)
        return []


# EOF
