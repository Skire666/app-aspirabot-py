"""Business logic and validation service for scraping workflows.

This module enforces domain-level rules on WorkflowModel instances.
It has no Tkinter dependency and no file access, making it fully
unit-testable in isolation.

Example:
    >>> from models.workflow_model import WorkflowModel
    >>> service = WorkflowService()
    >>> errors = service.validate(WorkflowModel(provider_id_file="x"))
    >>> errors[0]
    'Le workflow doit contenir au moins une étape.'
"""

import logging

from models.step_scrapping_model import StepScrappingModel, StepType

# Allowed values for constrained fields.
_VALID_WAIT_STATES = frozenset({"commit", "domcontentloaded", "load", "networkidle"})
_VALID_UNITS = frozenset({"hour", "minute", "second", "millisecond"})
_VALID_DOWNLOAD_MODES = frozenset({"largest", "first", "last", "all"})
_VALID_CLICK_MODES = frozenset({"Normal", "Forced", "JS Direct"})


class WorkflowService:
    """Validates and manages workflow business rules.

    This service enforces structural and semantic constraints on
    WorkflowModel instances without touching the UI or file system.
    """

    def __init__(self) -> None:
        """Initializes the service with a logger."""
        self._logger = logging.getLogger(__name__)

    def validate(self, workflow: WorkflowModel) -> list[str]:
        """Validates the entire workflow and returns a list of error messages.

        Args:
            workflow: The workflow to validate.

        Returns:
            A list of error strings. Empty means the workflow is valid.

        Raises:
            None.

        Example:
            >>> service.validate(WorkflowModel(provider_id_file="x"))
            ['Le workflow doit contenir au moins une étape.']
        """
        # An empty workflow is always invalid.
        if not workflow.steps:
            return ["Le workflow doit contenir au moins une étape."]

        errors: list[str] = []

        # First step must open a URL.
        if workflow.steps[0].step_type != StepType.OPEN_URL:
            errors.append("La première étape doit être de type OPEN_URL.")

        # Validate each step individually.
        for i, step in enumerate(workflow.steps):
            for msg in self._validate_step(step):
                errors.append(f"Étape {i + 1}: {msg}")

        return errors

    def _validate_step(self, step: StepScrappingModel) -> list[str]:
        """Dispatches validation to the per-type validator.

        Args:
            step: The step to validate.

        Returns:
            A list of error messages for this step; empty if valid.
        """
        # Map each type to its validator method.
        validators = {
            StepType.OPEN_URL: self._validate_open_url,
            StepType.SLEEP: self._validate_sleep,
            StepType.RANDOM_PAUSE: self._validate_random_pause,
            StepType.REFRESH_PAGE: self._validate_refresh_page,
            StepType.DOWNLOAD_IMAGE: self._validate_download_image,
            StepType.WAIT_IMAGE_SIZE: self._validate_wait_image_size,
            StepType.CLICK_ELEMENT: self._validate_click_element,
            StepType.WAIT_ELEMENT: self._validate_wait_element,
            StepType.SCROLL_DOWN: self._validate_scroll_down,
        }
        validator = validators.get(step.step_type)
        if validator is None:
            return [f"Type inconnu: {step.step_type}"]
        return validator(step.params)

    def _validate_open_url(self, params: dict) -> list[str]:
        """Validates OPEN_URL params.

        Args:
            params: Step parameter dictionary.

        Returns:
            List of error messages.
        """
        errors: list[str] = []
        # URL must be a non-empty string.
        if not str(params.get("url", "")).strip():
            errors.append("url est obligatoire.")
        # wait_state must be one of the allowed values.
        if params.get("wait_state") not in _VALID_WAIT_STATES:
            errors.append(f"wait_state invalide. Valeurs: {sorted(_VALID_WAIT_STATES)}")
        return errors

    def _validate_sleep(self, params: dict) -> list[str]:
        """Validates SLEEP params.

        Args:
            params: Step parameter dictionary.

        Returns:
            List of error messages.
        """
        errors: list[str] = []
        if not isinstance(params.get("duration"), (int, float)):
            errors.append("duration doit être un nombre.")
        if params.get("unit") not in _VALID_UNITS:
            errors.append(f"unit invalide. Valeurs: {sorted(_VALID_UNITS)}")
        return errors

    def _validate_random_pause(self, params: dict) -> list[str]:
        """Validates RANDOM_PAUSE params including min < max constraint.

        Args:
            params: Step parameter dictionary.

        Returns:
            List of error messages.
        """
        errors: list[str] = []
        min_val = params.get("min")
        max_val = params.get("max")

        # Validate types first.
        if not isinstance(min_val, (int, float)):
            errors.append("min doit être un nombre.")
        if not isinstance(max_val, (int, float)):
            errors.append("max doit être un nombre.")

        # Enforce strict ordering only when both are valid numbers.
        if isinstance(min_val, (int, float)) and isinstance(max_val, (int, float)):
            if min_val >= max_val:
                errors.append("min doit être strictement inférieur à max.")

        if params.get("unit") not in _VALID_UNITS:
            errors.append(f"unit invalide. Valeurs: {sorted(_VALID_UNITS)}")
        return errors

    def _validate_refresh_page(self, params: dict) -> list[str]:
        """Validates REFRESH_PAGE params.

        Args:
            params: Step parameter dictionary.

        Returns:
            List of error messages.
        """
        if not isinstance(params.get("clear_cache"), bool):
            return ["clear_cache doit être un booléen."]
        return []

    def _validate_download_image(self, params: dict) -> list[str]:
        """Validates DOWNLOAD_IMAGE params.

        Args:
            params: Step parameter dictionary.

        Returns:
            List of error messages.
        """
        errors: list[str] = []
        if params.get("mode") not in _VALID_DOWNLOAD_MODES:
            errors.append(f"mode invalide. Valeurs: {sorted(_VALID_DOWNLOAD_MODES)}")

        # All four dimension fields must be integers.
        for key in ("height_min", "height_max", "width_min", "width_max"):
            if not isinstance(params.get(key), int):
                errors.append(f"{key} doit être un entier.")
        return errors

    def _validate_wait_image_size(self, params: dict) -> list[str]:
        """Validates WAIT_IMAGE_SIZE params.

        Args:
            params: Step parameter dictionary.

        Returns:
            List of error messages.
        """
        errors: list[str] = []
        for key in ("height_min", "height_max", "width_min", "width_max"):
            if not isinstance(params.get(key), int):
                errors.append(f"{key} doit être un entier.")
        return errors

    def _validate_click_element(self, params: dict) -> list[str]:
        """Validates CLICK_ELEMENT params.

        Args:
            params: Step parameter dictionary.

        Returns:
            List of error messages.
        """
        errors: list[str] = []
        if not str(params.get("selector", "")).strip():
            errors.append("selector est obligatoire.")
        if params.get("click_mode") not in _VALID_CLICK_MODES:
            errors.append(f"click_mode invalide. Valeurs: {sorted(_VALID_CLICK_MODES)}")
        return errors

    def _validate_wait_element(self, params: dict) -> list[str]:
        """Validates WAIT_ELEMENT params.

        Args:
            params: Step parameter dictionary.

        Returns:
            List of error messages.
        """
        if not str(params.get("selector", "")).strip():
            return ["selector est obligatoire."]
        return []

    def _validate_scroll_down(self, params: dict) -> list[str]:
        """Validates SCROLL_DOWN params.

        Args:
            params: Step parameter dictionary.

        Returns:
            List of error messages.
        """
        if not isinstance(params.get("pixels"), int):
            return ["pixels doit être un entier."]
        return []
