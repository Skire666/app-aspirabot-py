"""IStepExecutor for JUMP_TO_STEP."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.jump_to_step_params import JumpToStepParams
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import StepTypeEnum
from shared.step_registry import register_step_executor


class JumpToStepExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the jump to step scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_JUMP_TO_STEP

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(JumpToStepParams, context.step_scraping_data.params)
        should_jump = (
            p.condition == "always"
            or (context.last_result_step and p.condition == "success")
            or (not context.last_result_step and p.condition == "failure")
        )
        if should_jump and p.target_hexastring:
            context.pending_jump = p.target_hexastring

        str_jump = (
            f"Doit sauter vers l'étape [#{p.target_hexastring}]"
            if should_jump
            else "Ne saute pas. Lit prochaine étape."
        )
        context.last_message_step = str_jump


register_step_executor(JumpToStepExecutor())


# EOF
