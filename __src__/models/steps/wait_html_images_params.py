"""Typed parameter model for the WAIT_IMAGE_SIZE step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from models.step_scraping_model import StepType
from shared.constants import C_MAXIMUM_SIZE_IMAGE, C_UNITS_TIME_DEFAULT_MODEL

from __src__.views.steps.wait_html_elements_form_def import C_INPUT_DEFAULT_RETRY_DELAY


@dataclass(frozen=True)
class WaitHtmlImagesParams(IStepParams):
    """Parameters for the wait image size scraping step."""

    height_min: int
    height_max: int
    width_min: int
    width_max: int
    operator: str
    quantity: int
    retry_delay: int
    retry_unit: str
    retry_max: int
    comment: str = ""

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(
            height_min=0,
            height_max=C_MAXIMUM_SIZE_IMAGE,
            width_min=0,
            width_max=C_MAXIMUM_SIZE_IMAGE,
            operator="equal",
            quantity=1,
            retry_delay=C_INPUT_DEFAULT_RETRY_DELAY,
            retry_unit=C_UNITS_TIME_DEFAULT_MODEL,
            retry_max=10,
            comment="",
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "height_min": self.height_min,
            "height_max": self.height_max,
            "width_min": self.width_min,
            "width_max": self.width_max,
            "operator": self.operator,
            "quantity": self.quantity,
            "retry_delay": self.retry_delay,
            "retry_unit": self.retry_unit,
            "retry_max": self.retry_max,
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            height_min=int(data.get("height_min", 0)),
            height_max=int(data.get("height_max", C_MAXIMUM_SIZE_IMAGE)),
            width_min=int(data.get("width_min", 0)),
            width_max=int(data.get("width_max", C_MAXIMUM_SIZE_IMAGE)),
            operator=data.get("operator", "equal"),
            quantity=int(data.get("quantity", 1)),
            retry_delay=int(data.get("retry_delay", C_INPUT_DEFAULT_RETRY_DELAY)),
            retry_unit=data.get("retry_unit", C_UNITS_TIME_DEFAULT_MODEL),
            retry_max=int(data.get("retry_max", 10)),
            comment=data.get("comment", ""),
        )

    @classmethod
    def get_step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.WAIT_HTML_IMAGES
