"""Generic validate_model() base implementation for all step executors."""

from __future__ import annotations

from pydantic import ValidationError

from models.step_scraping_model import StepScrapingModel
from models.steps_context_model import StepsContext


class StepExecutorBase:
    """Mixin providing a generic ``validate_model()`` that delegates to the params model.

    Concrete executors inherit this class and remove their hand-written
    ``validate_model()`` override.  The base implementation:

    1. Builds a context dict with step_index, steps_context, and step_id.
    2. Calls ``type(model.params).model_validate(model.params.to_dict(), context=ctx)``.
    3. Returns ``[]`` on success, or the collected Pydantic error messages on failure.

    The params model's validators are context-aware — they only activate when
    this context dict is present, so normal construction is unaffected.
    """

    def validate_model(
        self,
        model: StepScrapingModel,
        step_index: int,
        steps_context: StepsContext,
    ) -> list[str]:
        """Validate *model* params using the Pydantic model's own validators.

        Args:
            model: The step model whose ``params`` object will be re-validated.
            step_index: Zero-based position of the step in the workflow.
            steps_context: Read-only workflow snapshot for cross-step checks.

        Returns:
            A list of French error strings; empty when the params are valid.
        """
        ctx = {
            "step_index": step_index,
            "steps_context": steps_context,
            "step_id": model.step_id,
        }
        try:
            type(model.params).model_validate(model.params.to_dict(), context=ctx)
            return []
        except ValidationError as exc:
            return [str(err["ctx"]["error"]) if "ctx" in err and "error" in err["ctx"] else err["msg"]
                    for err in exc.errors()]
