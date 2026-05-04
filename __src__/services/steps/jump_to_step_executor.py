"""IStepExecutor for JUMP_TO_STEP."""
from __future__ import annotations
from typing import Any
from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepType
from models.steps.jump_to_step_params import JumpToStepParams
from playwright.sync_api import Page
from shared.step_registry import register_executor


class JumpToStepExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.JUMP_TO_STEP

    def default_params_dict(self) -> dict[str, Any]:
        return JumpToStepParams.default().to_dict()

    def execute(self, page: Page, params: dict[str, Any]) -> None:
        p = JumpToStepParams.from_dict(params)
        prev_success: bool = params.get("_prev_success", True)
        should_jump = (
            p.condition == "always"
            or (p.condition == "success" and prev_success)
            or (p.condition == "failure" and not prev_success)
        )
        if should_jump:
            # Signal the service by writing to the mutable params dict.
            params["_pending_jump"] = p.target_index

    def validate(self, params: dict[str, Any], step_index: int) -> list[str]:
        p = JumpToStepParams.from_dict(params)
        errors: list[str] = []
        if p.condition not in {"success", "failure", "always"}:
            errors.append(f"JUMP_TO_STEP : condition invalide — {p.condition!r}.")
        if p.target_index < 0:
            errors.append("JUMP_TO_STEP : target_index doit être >= 0.")
        if p.target_index == step_index:
            errors.append("JUMP_TO_STEP : une étape ne peut pas pointer vers elle-même.")
        return errors


register_executor(JumpToStepExecutor())
