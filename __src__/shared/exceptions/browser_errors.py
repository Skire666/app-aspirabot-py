"""Browser lifecycle, navigation, click, and image-wait errors."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.exceptions.base_error import AspirabotBaseError


class ElementNotFoundForClickError(ValueError, AspirabotBaseError):
    """Raised when a click target cannot be found for the requested mode."""

    def __init__(self, selector: str, mode: str) -> None:
        """Initialize the error message.

        Args:
            selector: CSS selector used for the click.
            mode: Click mode label (normal, forced).
        """
        super().__init__(f"Élément {selector!r} introuvable pour le clic en mode {mode}.")


class UnsupportedClickModeError(ValueError, AspirabotBaseError):
    """Raised when a click mode is not supported."""

    def __init__(self, click_mode: str) -> None:
        """Initialize the error message.

        Args:
            click_mode: Click mode received from parameters.
        """
        super().__init__(f"Mode de clic non pris en charge : {click_mode}")


class CurrentPageClosedUnexpectedlyError(ValueError, AspirabotBaseError):
    """Raised when the active page is closed during a close-tabs step."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("La page courante a été fermée de manière inattendue.")


class CountHtmlElementsConditionNotMetError(ValueError, AspirabotBaseError):
    """Raised when the COUNT_HTML_ELEMENTS condition is not satisfied."""

    def __init__(self, count: int, operator: str, value_ask: str) -> None:
        """Initialize the error message.

        Args:
            count: Measured element count.
            operator: Operator used for comparison.
            value_ask: Display string describing the expected value.
        """
        super().__init__(f"Condition non satisfaite (COUNT={count}, {operator} {value_ask})")


class CountHtmlImagesConditionNotMetError(ValueError, AspirabotBaseError):
    """Raised when the COUNT_HTML_IMAGES condition is not satisfied."""

    def __init__(self, count: int, operator: str, value_desc: str) -> None:
        """Initialize the error message.

        Args:
            count: Measured element count.
            operator: Operator used for comparison.
            value_desc: Display string describing the expected value.
        """
        super().__init__(f"Condition non satisfaite (COUNT={count}, {operator} {value_desc})")


class NoMatchingImageFoundError(ValueError, AspirabotBaseError):
    """Raised when no image matches the configured size constraints."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Aucune image correspondant aux contraintes de taille n'a été trouvée sur la page.")


class ImageDownloadFailedError(ValueError, AspirabotBaseError):
    """Raised when an image download fails with an HTTP error."""

    def __init__(self, status: int) -> None:
        """Initialize the error message.

        Args:
            status: HTTP response status code.
        """
        super().__init__(f"Échec du téléchargement de l'image : HTTP {status}")


class ImageNotDownloadedError(ValueError, AspirabotBaseError):
    """Raised when no image could be downloaded from selected targets."""

    def __init__(self, found: int) -> None:
        """Initialize the error message.

        Args:
            found: Number of matching targets found.
        """
        super().__init__(f"Aucune image n'a été téléchargée (cibles trouvées : {found}).")


class ImageWaitTimeoutError(TimeoutError, AspirabotBaseError):
    """Raised when waiting for an image size times out."""

    def __init__(self, wait_seconds: float) -> None:
        """Initialize the error message.

        Args:
            wait_seconds: Timeout duration in seconds.
        """
        super().__init__(
            f"Aucune image correspondant aux contraintes de taille n'est apparue"
            f" dans le délai imparti ({wait_seconds}s)."
        )


class BrowserAlreadyLaunchedError(RuntimeError, AspirabotBaseError):
    """Raised when launch is called while a browser is already active."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Le navigateur est déjà lancé. Appelez close_browser() en premier.")


class BrowserLaunchFailedError(RuntimeError, AspirabotBaseError):
    """Raised when the browser fails to launch."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Échec du lancement du navigateur. Consultez les journaux pour plus de détails.")


class BrowserNotLaunchedError(RuntimeError, AspirabotBaseError):
    """Raised when a browser operation requires a launched instance."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Le navigateur n'est pas lancé ou a été fermé.")


class PageNotAvailableOrClosedError(RuntimeError, AspirabotBaseError):
    """Raised when a browser operation requires a launched instance."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("La page n'est pas disponible ou a été fermée.")


class DnsSolverTimeoutExceededError(RuntimeError, AspirabotBaseError):
    """Raised when the DNS solver wait duration exceeds the maximum allowed."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Délai DNS solver atteint (>= 30 sec).")


class UrlNavigationMismatchError(RuntimeError, AspirabotBaseError):
    """Raised when the browser lands on a different URL than the intended target."""

    def __init__(self, final_url: str, target_url: str) -> None:
        """Initialize the error message.

        Args:
            final_url: The URL the browser actually landed on.
            target_url: The URL that was requested.
        """
        super().__init__(f"URL finale différente de la cible : {final_url} vs {target_url}")


# EOF
