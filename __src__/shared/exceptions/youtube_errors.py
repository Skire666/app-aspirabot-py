"""YouTube video and subtitle download errors."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.exceptions.base_error import AspirabotBaseError


class YoutubeSubtitlesDownloadedError(AspirabotBaseError):
    """Raised when no subtitle file was downloaded for a YouTube step."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Aucun fichier de sous-titres téléchargé.")


class YoutubeLanguageMismatchError(AspirabotBaseError):
    """Raised when the original audio language does not match the video's declared language."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("La langue audio originale ne correspond pas à la langue déclarée de la vidéo.")


class YoutubeVideoDataIncompleteError(AspirabotBaseError):
    """Raised when the YouTube video data dictionary is missing required keys."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Les données de la vidéo YouTube sont incomplètes (clés requises manquantes).")


class YoutubeSubtitlesNotFoundInMetadataError(AspirabotBaseError):
    """Raised when no subtitle tracks are found in the video metadata."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Aucun sous-titre trouvé dans les métadonnées du flux vidéo.")


class YoutubeUrlParameterEmptyError(ValueError, AspirabotBaseError):
    """Raised when the url_youtube parameter is empty or blank."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Le paramètre 'url_youtube' doit être une vidéo/short valide.")


class YoutubeOutputDirParameterEmptyError(ValueError, AspirabotBaseError):
    """Raised when the output_dir parameter is empty or blank."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Le paramètre 'output_dir' doit être une chaîne non vide.")


# EOF
