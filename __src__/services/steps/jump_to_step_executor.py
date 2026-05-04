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

    def _resolve_target_step_id(self, params: dict[str, Any]) -> str:
        raw_target = params.get("target_hexastring", "")
        if isinstance(raw_target, str):
            return raw_target
        if isinstance(raw_target, int):
            step_id_by_index = params.get("_step_id_by_index")
            if isinstance(step_id_by_index, list) and 0 <= raw_target < len(step_id_by_index):
                return step_id_by_index[raw_target]
            if isinstance(step_id_by_index, dict):
                return str(step_id_by_index.get(raw_target, ""))
        return ""

    def execute(self, page: Page, params: dict[str, Any]) -> None:
        p = JumpToStepParams.from_dict(params)
        prev_success: bool = params.get("_prev_success", True)
        should_jump = (
            p.condition == "always"
            or (p.condition == "success" and prev_success)
            or (p.condition == "failure" and not prev_success)
        )
        target_step_id = self._resolve_target_step_id(params)
        if should_jump and target_step_id:
            # Signal the service by writing to the mutable params dict.
            params["_pending_jump"] = target_step_id

    def validate(self, params: dict[str, Any], step_index: int) -> list[str]:
        p = JumpToStepParams.from_dict(params)
        errors: list[str] = []
        if p.condition not in {"success", "failure", "always"}:
            errors.append(f"JUMP_TO_STEP : condition invalide — {p.condition!r}.")
        target_step_id = self._resolve_target_step_id(params)
        if not target_step_id:
            errors.append("JUMP_TO_STEP : target_hexastring doit référencer un step_id valide.")
        if target_step_id:
            workflow_step_ids = params.get("_workflow_step_ids")
            if isinstance(workflow_step_ids, list) and target_step_id not in workflow_step_ids:
                errors.append("JUMP_TO_STEP : l'étape cible est introuvable.")
            self_step_id = params.get("_self_step_id")
            if self_step_id and target_step_id == self_step_id:
                errors.append("JUMP_TO_STEP : une étape ne peut pas pointer vers elle-même.")
        return errors


register_executor(JumpToStepExecutor())
