"""IStepExecutor for JUMP_TO_STEP."""

from __future__ import annotations

from typing import Any

from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.jump_to_step_params import JumpToStepParams
from services.workflow_service import register_step_executor


class JumpToStepExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.JUMP_TO_STEP

    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return JumpToStepParams.default().to_dict()

    def execute(self, page: Any, params: dict[str, Any]) -> None:
        """Execute the step."""
        p = JumpToStepParams.from_dict(params)
        prev_success: bool = params.get("_prev_success", True)
        should_jump = (
            p.condition == "always"
            or (prev_success and p.condition == "success")
            or (not prev_success and p.condition == "failure")
        )
        target_step_id = params.get("target_hexastring", "")
        if should_jump and target_step_id:
            # Signal the service by writing to the mutable params dict.
            params["_pending_jump"] = target_step_id

    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        condition = model.params.get("condition", "success")
        target_step_id = model.params.get("target_hexastring", "")

        errors: list[str] = []
        step_idx_display = str(step_index + 1).zfill(2)
        if condition not in {"success", "failure", "always"}:
            errors.append(f"Dans l'étape {step_idx_display}. : condition invalide - {condition}.")

        # Basic check for presence of target step ID.
        if not target_step_id:
            errors.append(f"Dans l'étape {step_idx_display}. : Aucune étape de référencée.")
            return errors

        # Additional checks if a target step ID is provided.
        if target_step_id:
            # Check for self-referencing jump.
            if target_step_id == model.step_id:
                errors.append(f"Dans l'étape {step_idx_display}. : ne peut pas pointer vers elle-même.")

            # TODO PCO : pas optimisé la recherche, un dictionnaire serait mieux.
            step_found = None
            for step_item in model.parent_context:  # type: ignore
                if step_item.step_id == target_step_id:
                    step_found = step_item
                    break

            if step_found is None:
                errors.append(f"Dans l'étape {step_idx_display}. : la cible [{target_step_id}] est introuvable.")

        # Note: We cannot check for jump loops here, as it would require analyzing the entire workflow
        return errors


register_step_executor(JumpToStepExecutor())
