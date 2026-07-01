"""Domain model for a scraping workflow step.

This module defines a strongly typed step entity used by scenarios.
It includes the StepTypeEnum enumeration and default parameter values for each type.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from models.steps.jump_to_step_params import JumpToStepParams
from shared.datetime_util import dict_with_key_to_optional_datetime
from shared.enums import StepTypeEnum
from shared.random_util import generate_rng_id_step

if TYPE_CHECKING:
    from interfaces.i_step_params import IStepParams

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------


@dataclass
class StepScrapingModel:
    """Represents one executable step in a scraping workflow.

    Attributes:
        step_type: The type of action to perform.
        step_id: Unique identifier for this step instance.
        is_active: Whether this step is enabled during execution.
        modified_date: Timestamp of the last modification.
        params: Typed parameters specific to this step type.
    """

    step_type: StepTypeEnum
    step_id: str
    params: IStepParams
    is_active: bool = True
    modified_date: datetime = field(default_factory=datetime.now)

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> StepScrapingModel:
        """Deserialize a step from a raw dictionary using the registered params builder.

        Args:
            data: A dict with 'step_type', 'step_id', 'is_active', and 'params' keys.

        Returns:
            A new StepScrapingModel instance with fully typed params.

        Raises:
            ValueError: When the step_type value is unknown.
            ParamsBuilderNotRegisteredError: When no builder is registered for the type.
        """
        from shared.step_registry import build_params  # local import avoids circular import at module level

        step_type = StepTypeEnum(data.get("step_type"))
        raw_params: dict[str, Any] = data.get("params") or {}
        raw_date = dict_with_key_to_optional_datetime(data, "modified_date")
        return cls(
            step_type=step_type,
            step_id=str(data.get("step_id", "")),
            is_active=bool(data.get("is_active", True)),
            modified_date=raw_date if raw_date is not None else datetime.now(),
            params=build_params(step_type, raw_params),
        )

    def export_to_data_json(self) -> dict[str, Any]:
        """Serialize the step to a JSON-compatible dictionary.

        Returns:
            A dict with 'step_type', 'step_id', 'is_active', 'modified_date', and 'params' keys.

        Raises:
            None.
        """
        return {
            "step_type": self.step_type.value,
            "step_id": self.step_id,
            "is_active": self.is_active,
            "modified_date": self.modified_date,
            "params": self.params.to_dict(),
        }

    def copy_business(self) -> StepScrapingModel:
        """Create a duplicate of this step with a new unique ID.

        The typed params instance is shared (frozen dataclasses are immutable),
        so no deep copy is needed.

        Returns:
            A new StepScrapingModel with identical type and params but a fresh step_id.
        """
        return StepScrapingModel(
            step_type=self.step_type,
            step_id=generate_rng_id_step(),
            is_active=self.is_active,
            params=self.params,
            modified_date=datetime.now(),
        )

    def mark_as_modified(self) -> None:
        """Update the step's modified date to the current time."""
        self.modified_date = datetime.now()

    def is_jump_to_step_and_handle_error(self) -> bool:
        """Check if this step is a JUMP_TO_STEP type.

        Returns:
            True if the step_type is StepTypeEnum.E_JUMP_TO_STEP, else False.
        """
        return bool(self.step_type == StepTypeEnum.E_JUMP_TO_STEP and isinstance(self.params, JumpToStepParams))


# EOF
