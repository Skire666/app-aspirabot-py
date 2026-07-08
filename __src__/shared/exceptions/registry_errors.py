"""Step registry lookup errors and generic time/duration errors."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.exceptions.base_error import AspirabotBaseError


class NoExecutorsRegisteredError(ValueError, AspirabotBaseError):
    """Raised when the workflow registry is empty."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Aucun exécuteur enregistré dans le registre.")


class ExecutorNotRegisteredError(ValueError, AspirabotBaseError):
    """Raised when no executor is registered for a step type."""

    def __init__(self, step_type: object) -> None:
        """Initialize the error message.

        Args:
            step_type: The step type that was requested.
        """
        super().__init__(f"Aucun exécuteur enregistré pour le type d'étape {step_type}.")


class FormNotRegisteredError(ValueError, AspirabotBaseError):
    """Raised when no form definition is registered for a step type."""

    def __init__(self, step_type: object) -> None:
        """Initialize the error message.

        Args:
            step_type: The step type that was requested.
        """
        super().__init__(f"Aucun formulaire enregistré pour le type d'étape : {step_type}")


class ParamsBuilderNotRegisteredError(ValueError, AspirabotBaseError):
    """Raised when no params builder is registered for a step type."""

    def __init__(self, step_type: object) -> None:
        """Initialize the error message.

        Args:
            step_type: The step type that was requested.
        """
        super().__init__(f"Aucun constructeur de paramètres enregistré pour le type d'étape : {step_type}")


class InvalidTimeUnitError(ValueError, AspirabotBaseError):
    """Raised when a time unit is missing or not in the recognised set."""

    def __init__(self, time_unit: str | None) -> None:
        """Initialize the error message.

        Args:
            time_unit: The invalid or missing time unit value.
        """
        super().__init__(f"Unité de temps invalide ou manquante : '{time_unit}'")


class InvalidDurationError(ValueError, AspirabotBaseError):
    """Raised when a duration value is negative."""

    def __init__(self, duration: int | float) -> None:
        """Initialize the error message.

        Args:
            duration: The invalid duration value.
        """
        super().__init__(f"Durée invalide (doit être >= 0) : {duration}")


class OpenUrlTooManyRetriesError(RuntimeError, AspirabotBaseError):
    """Raised when the open URL step fails after all retries are exhausted."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Échec de l'ouverture de l'URL après plusieurs tentatives.")


# EOF
