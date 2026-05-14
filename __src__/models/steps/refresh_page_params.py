"""Typed parameter model for the REFRESH_PAGE step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL


@dataclass(frozen=True)
class RefreshPageParams(IStepParams):
    """Parameters for the refresh page scraping step."""

    clear_cache: bool
    wait_state: str
    timeout_duration: int
    timeout_unit: str
    comment: str

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(
            clear_cache=False,
            wait_state="load",
            timeout_duration=8,
            timeout_unit=C_UNITS_TIME_DEFAULT_MODEL,
            comment="",
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "clear_cache": self.clear_cache,
            "wait_state": self.wait_state,
            "timeout_duration": self.timeout_duration,
            "timeout_unit": self.timeout_unit,
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            clear_cache=bool(data.get("clear_cache")),
            wait_state=data.get("wait_state", "load"),
            timeout_duration=data.get("timeout_duration", 8),
            timeout_unit=data.get("timeout_unit", C_UNITS_TIME_DEFAULT_MODEL),
            comment=data.get("comment", ""),
        )

    @classmethod
    def get_step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_REFRESH_PAGE
