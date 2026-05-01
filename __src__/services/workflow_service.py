"""Service for validating scraping workflow steps.

Provides step-level parameter validation independent of the UI layer.
The presenter calls validate_step() before persisting changes so that
broken configurations are caught before they reach the scraping runner.

Example:
    >>> service = WorkflowService()
    >>> errors = service.validate_step(0, step)
    >>> errors
    []
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from collections.abc import Callable
from typing import Any

from models.step_scrapping_model import StepScrappingModel, StepType


class WorkflowService:
    """Validates scraping workflow step parameters.

    Each step type has a dedicated private validator method. The public
    validate_step() method dispatches to the correct one and returns a
    flat list of human-readable French error messages.

    Example:
        >>> service = WorkflowService()
        >>> errors = service.validate_step(2, jump_step)
        >>> "JUMP_TO_STEP" in errors[0]
        True
    """

    def validate_step(
        self,
        step_index: int,
        step: StepScrappingModel,
    ) -> list[str]:
        """Validates the parameters of a single workflow step.

        Args:
            step_index: Zero-based position of the step in the workflow.
            step: The step to validate.

        Returns:
            A list of error messages; empty when the step is valid.

        Raises:
            None.

        Example:
            >>> service.validate_step(0, StepScrappingModel.create_default(StepType.SLEEP))
            []
        """
        # Resolve and invoke the per-type validator.
        validator = self._get_validator_dispatch().get(step.step_type)
        if validator is None:
            return []
        return validator(step.params, step_index)

    # ------------------------------------------------------------------
    # Validator dispatch builder
    # ------------------------------------------------------------------

    def _get_validator_dispatch(
        self,
    ) -> dict[StepType, Callable[[dict[str, Any], int], list[str]]]:
        """Returns the per-step-type validator dispatch table.

        Returns:
            Mapping from StepType to a callable (params, step_index) → errors.
        """
        return {
            StepType.OPEN_URL: self._validate_open_url,
            StepType.REFRESH_PAGE: lambda p, i: [],
            StepType.SLEEP: self._validate_sleep,
            StepType.RANDOM_PAUSE: self._validate_random_pause,
            StepType.DOWNLOAD_IMAGE: self._validate_download_image,
            StepType.WAIT_IMAGE_SIZE: self._validate_wait_image_size,
            StepType.WAIT_ELEMENT: self._validate_wait_element,
            StepType.COUNT_ELEMENT: self._validate_count_element,
            StepType.CLICK_ELEMENT: self._validate_click_element,
            StepType.SCROLL_DOWN: lambda p, i: [],
            StepType.EXTRACT_TEXT: self._validate_extract_text,
            StepType.JUMP_TO_STEP: self._validate_jump_to_step,
            StepType.CLOSE_TABS: self._validate_close_tabs,
            StepType.END_PROCESS: self._validate_end_process,
        }

    # ------------------------------------------------------------------
    # Per-type validators — existing step types
    # ------------------------------------------------------------------

    def _validate_open_url(self, params: dict[str, Any], step_index: int) -> list[str]:
        """Validates OPEN_URL params.

        Args:
            params: Step parameter dict.
            step_index: Zero-based step index (unused).

        Returns:
            List of error messages.
        """
        errors: list[str] = []
        allowed_units = {"hour", "minute", "second", "millisecond"}
        timeout_duration = params.get("timeout_duration", 0)
        timeout_unit = params.get("timeout_unit", "second")

        # URL is mandatory.
        if not params.get("url", "").strip():
            errors.append("OPEN_URL : l'URL est obligatoire.")

        # Timeout constraints.
        if timeout_duration < 0:
            errors.append("OPEN_URL : timeout_duration doit être >= 0.")
        if timeout_duration > 0 and timeout_unit not in allowed_units:
            errors.append(f"OPEN_URL : timeout_unit invalide — {timeout_unit!r}.")
        return errors

    def _validate_sleep(self, params: dict[str, Any], step_index: int) -> list[str]:
        """Validates SLEEP params.

        Args:
            params: Step parameter dict.
            step_index: Zero-based step index (unused).

        Returns:
            List of error messages.
        """
        errors: list[str] = []
        if params.get("duration", -1) < 0:
            errors.append("SLEEP : duration doit être >= 0.")
        return errors

    def _validate_random_pause(self, params: dict[str, Any], step_index: int) -> list[str]:
        """Validates RANDOM_PAUSE params.

        Args:
            params: Step parameter dict.
            step_index: Zero-based step index (unused).

        Returns:
            List of error messages.
        """
        errors: list[str] = []
        min_val = params.get("min", 0)
        max_val = params.get("max", 1)
        if float(min_val) >= float(max_val):
            errors.append("RANDOM_PAUSE : min doit être strictement inférieur à max.")
        return errors

    def _validate_download_image(self, params: dict[str, Any], step_index: int) -> list[str]:
        """Validates DOWNLOAD_IMAGE dimension params.

        Args:
            params: Step parameter dict.
            step_index: Zero-based step index (unused).

        Returns:
            List of error messages.
        """
        errors: list[str] = []
        for key in ("height_min", "height_max", "width_min", "width_max"):
            try:
                int(params.get(key, 0))
            except (ValueError, TypeError):
                errors.append(f"DOWNLOAD_IMAGE : {key} doit être un entier.")
        return errors

    def _validate_wait_image_size(self, params: dict[str, Any], step_index: int) -> list[str]:
        """Validates WAIT_IMAGE_SIZE params including dimension and timeout checks.

        Args:
            params: Step parameter dict.
            step_index: Zero-based step index (unused).

        Returns:
            List of error messages.
        """
        errors = list(self._validate_download_image(params, step_index))
        allowed_units = {"hour", "minute", "second", "millisecond"}
        timeout_duration = params.get("timeout_duration", 0)
        timeout_unit = params.get("timeout_unit", "second")

        # Timeout constraints.
        if timeout_duration < 0:
            errors.append("WAIT_IMAGE_SIZE : timeout_duration doit être >= 0.")
        if timeout_duration > 0 and timeout_unit not in allowed_units:
            errors.append(f"WAIT_IMAGE_SIZE : timeout_unit invalide — {timeout_unit!r}.")
        return errors

    def _validate_click_element(self, params: dict[str, Any], step_index: int) -> list[str]:
        """Validates CLICK_ELEMENT params.

        Args:
            params: Step parameter dict.
            step_index: Zero-based step index (unused).

        Returns:
            List of error messages.
        """
        errors: list[str] = []
        if not params.get("selector", "").strip():
            errors.append("CLICK_ELEMENT : le sélecteur CSS est obligatoire.")
        return errors

    def _validate_wait_element(self, params: dict[str, Any], step_index: int) -> list[str]:
        """Validates WAIT_ELEMENT params.

        Args:
            params: Step parameter dict.
            step_index: Zero-based step index (unused).

        Returns:
            List of error messages.
        """
        errors: list[str] = []
        allowed_units = {"hour", "minute", "second", "millisecond"}
        timeout_duration = params.get("timeout_duration", 0)
        timeout_unit = params.get("timeout_unit", "second")

        # Selector is mandatory.
        if not params.get("selector", "").strip():
            errors.append("WAIT_ELEMENT : le sélecteur CSS est obligatoire.")

        # Timeout constraints.
        if timeout_duration < 0:
            errors.append("WAIT_ELEMENT : timeout_duration doit être >= 0.")
        if timeout_duration > 0 and timeout_unit not in allowed_units:
            errors.append(f"WAIT_ELEMENT : timeout_unit invalide — {timeout_unit!r}.")
        return errors

    def _validate_count_element(self, params: dict[str, Any], step_index: int) -> list[str]:
        """Validates COUNT_ELEMENT params including operator, condition, and range.

        Args:
            params: Step parameter dict.
            step_index: Zero-based step index (unused).

        Returns:
            List of error messages.
        """
        allowed_units = {"hour", "minute", "second", "millisecond"}
        allowed_operators = {
            "between",
            "not_between",
            "equal",
            "not_equal",
            "greater_than",
            "less_than",
            "greater_or_equal",
            "less_or_equal",
        }
        allowed_success_if = {"success", "failure"}
        errors: list[str] = []

        # Selector is mandatory.
        if not params.get("selector", "").strip():
            errors.append("COUNT_ELEMENT : le sélecteur CSS est obligatoire.")

        # Wait duration and unit constraints.
        if params.get("wait_duration", 0) < 0:
            errors.append("COUNT_ELEMENT : wait_duration doit être >= 0.")
        if params.get("wait_duration", 0) > 0 and params.get("wait_unit") not in allowed_units:
            errors.append(f"COUNT_ELEMENT : wait_unit invalide — {params.get('wait_unit')!r}.")

        # Enum checks for success_if and operator.
        if params.get("success_if") not in allowed_success_if:
            errors.append(f"COUNT_ELEMENT : success_if invalide — {params.get('success_if')!r}.")
        if params.get("operator") not in allowed_operators:
            errors.append(f"COUNT_ELEMENT : operator invalide — {params.get('operator')!r}.")

        # Range operator: value_min must not exceed value_max.
        op = params.get("operator")
        if op in {"between", "not_between"} and params.get("value_min", 0) > params.get("value_max", 0):
            errors.append("COUNT_ELEMENT : value_min doit être <= value_max.")
        return errors

    # ------------------------------------------------------------------
    # Per-type validators — new step types (CLOSE_TABS → END_PROCESS)
    # ------------------------------------------------------------------

    def _validate_close_tabs(self, params: dict[str, Any], step_index: int) -> list[str]:
        """Validates CLOSE_TABS params.

        Args:
            params: Step parameter dict.
            step_index: Zero-based step index (unused).

        Returns:
            List of error messages.
        """
        errors: list[str] = []
        # url_filter may be empty; only max_tabs is constrained.
        if params.get("max_tabs", -1) < 0:
            errors.append("CLOSE_TABS : max_tabs doit être >= 0.")
        return errors

    def _validate_extract_text(self, params: dict[str, Any], step_index: int) -> list[str]:
        """Validates EXTRACT_TEXT params.

        Args:
            params: Step parameter dict.
            step_index: Zero-based step index (unused).

        Returns:
            List of error messages.
        """
        allowed_modes = {"innerText", "textContent", "outerHTML", "innerHTML", "value"}
        allowed_targets = {"first", "last", "all"}
        errors: list[str] = []

        # Selector is mandatory.
        if not params.get("selector", "").strip():
            errors.append("EXTRACT_TEXT : le sélecteur CSS est obligatoire.")
        if params.get("extract_mode") not in allowed_modes:
            errors.append(f"EXTRACT_TEXT : mode d'extraction invalide — {params.get('extract_mode')!r}.")
        if params.get("target") not in allowed_targets:
            errors.append(f"EXTRACT_TEXT : cible invalide — {params.get('target')!r}.")
        return errors

    def _validate_jump_to_step(self, params: dict[str, Any], step_index: int) -> list[str]:
        """Validates JUMP_TO_STEP params including self-loop detection.

        Args:
            params: Step parameter dict.
            step_index: Zero-based index of this step; used for self-loop check.

        Returns:
            List of error messages.
        """
        allowed_conditions = {"success", "failure", "always"}
        errors: list[str] = []

        # Condition must be one of the three allowed values.
        if params.get("condition") not in allowed_conditions:
            errors.append(f"JUMP_TO_STEP : condition invalide — {params.get('condition')!r}.")
        if params.get("target_index", -1) < 0:
            errors.append("JUMP_TO_STEP : target_index doit être >= 0.")
        if params.get("target_index") == step_index:
            errors.append("JUMP_TO_STEP : une étape ne peut pas pointer vers elle-même.")
        return errors

    def _validate_end_process(self, params: dict[str, Any], step_index: int) -> list[str]:
        """Validates END_PROCESS params.

        Args:
            params: Step parameter dict.
            step_index: Zero-based step index (unused).

        Returns:
            List of error messages.
        """
        allowed_units = {"hour", "minute", "second", "millisecond"}
        errors: list[str] = []

        # Duration must be non-negative.
        if params.get("wait_duration", -1) < 0:
            errors.append("END_PROCESS : wait_duration doit être >= 0.")
        if params.get("wait_unit") not in allowed_units:
            errors.append(f"END_PROCESS : unité de temps invalide — {params.get('wait_unit')!r}.")
        return errors
