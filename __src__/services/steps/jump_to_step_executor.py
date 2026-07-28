"""IStepExecutor for JUMP_TO_STEP."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.jump_to_step_params import JumpToStepParams
from shared.constants import C_STATE_JUMP_TO_STEP_FAILURE
from shared.enums import ProcessResultEnum, StepTypeEnum
from shared.step_registry import register_step_executor


class JumpToStepExecutor(IStepExecutor):
    """Executor for the jump to step scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_JUMP_TO_STEP

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> ProcessResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(JumpToStepParams, context.step_scraping_data.params)
        last_was_success = context.last_step_was_success()

        try:
            should_jump = (last_was_success and p.condition == "success") or (
                not last_was_success and p.condition == C_STATE_JUMP_TO_STEP_FAILURE
            )
            if should_jump and p.target_hexastring:
                context.pending_jump = p.target_hexastring
            str_jump = (
                f"Doit sauter vers l'étape [#{p.target_hexastring}] (comment : {p.comment})"
                if should_jump
                else "Ne saute pas. Lit prochaine étape."
            )
            event_bus.log_step(context, str_jump)
        except Exception as exc:  # ruff: ignore[blind-except]
            event_bus.log_step(context, f"Excp : {exc}")
            return ProcessResultEnum.E_ERROR
        else:
            return ProcessResultEnum.E_SUCCESS


register_step_executor(JumpToStepExecutor())


# EOF
