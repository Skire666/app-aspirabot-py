"""IStepExecutor for JUMP_TO_STEP."""

from __future__ import annotations

from typing import override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.jump_to_step_params import JumpToStepParams
from services.workflow_service import register_step_executor
from shared.enums import StepTypeEnum
from shared.i18n_fra import ERROR_TEMPLATES


class JumpToStepExecutor(IStepExecutor):
    """Executor for the jump to step scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_JUMP_TO_STEP

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = JumpToStepParams.from_dict(context.step_params)
        should_jump = (
            p.condition == "always"
            or (context.last_result_step and p.condition == "success")
            or (not context.last_result_step and p.condition == "failure")
        )
        target_step_id = context.step_params.get("target_hexastring", "")
        if should_jump and target_step_id:
            context.pending_jump = target_step_id

        str_jump = (
            f"Doit sauter vers l'étape [#{target_step_id}]" if should_jump else "Ne saute pas. Lit prochaine étape."
        )
        context.last_message_step = str_jump

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        condition = model.params.get("condition", "success")
        target_step_id = model.params.get("target_hexastring", "")

        errors: list[str] = []
        step_idx_display = str(step_index + 1).zfill(2)
        if condition not in {"success", "failure", "always"}:
            errors.append(
                ERROR_TEMPLATES["jump_to_step_condition_invalid"].format(step=step_idx_display, value=condition),
            )

        # Basic check for presence of target step ID.
        if not target_step_id:
            errors.append(ERROR_TEMPLATES["jump_to_step_target_missing"].format(step=step_idx_display))
            return errors

        # Additional checks if a target step ID is provided.
        if target_step_id:
            # Check for self-referencing jump.
            if target_step_id == model.step_id:
                errors.append(ERROR_TEMPLATES["jump_to_step_self_reference"].format(step=step_idx_display))

            # TODO PCO : pas optimisé la recherche, un dictionnaire serait mieux.
            step_found = None
            for step_item in model.parent_context:  # type: ignore
                if step_item.step_id == target_step_id:
                    step_found = step_item
                    break

            if step_found is None:
                errors.append(
                    ERROR_TEMPLATES["jump_to_step_target_not_found"].format(
                        step=step_idx_display, value=target_step_id
                    ),
                )

        # Note: We cannot check for jump loops here, as it would require analyzing the entire workflow
        return errors


register_step_executor(JumpToStepExecutor())
