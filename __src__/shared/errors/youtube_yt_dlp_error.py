# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.error_code import ErrorCode


class ErrorCodeYYD(ErrorCode):
    """Error codes for YoutubeYtDlpModel."""

    # wrong
    YYD_1001 = "Vidéo indisponible (impossible à joindre via yt-dlp)."
    YYD_1002 = "Vidéo soumis à une restriction d'âge (il faut s'identifier)."
    YYD_1003 = "Vidéo réservée aux membres de la chaîne (l'accès est payant)."
    YYD_1004 = "Vidéo réservée aux membres de la chaîne (adhésion obligatoire)."
    YYD_1005 = "Vidéo n'est pas encore disponible (placeholder pour un futur live)."

    # ???
    YYD_9999 = "Erreur inconnue."

    @staticmethod
    def try_simplify_exception(excp: Exception) -> ErrorCodeYYD | None:
        """Simplify the error message for logging."""
        message = str(excp).lower()

        # Z0-Bb0AUHZk: Premieres in 11 days
        if " premieres in " in message:
            return ErrorCodeYYD.YYD_1005

        # join this channel to get access to members-only content like this video
        if " this channel to get access to " in message:
            return ErrorCodeYYD.YYD_1004

        # This video is available to this channel's members
        if " video is available to this channel's members" in message:
            return ErrorCodeYYD.YYD_1003

        # Sign in to confirm your age. This video may be inappropriate for some users.
        if " may be inappropriate for " in message:
            return ErrorCodeYYD.YYD_1002
        if " in to confirm your age" in message:
            return ErrorCodeYYD.YYD_1002

        # Video unavailable. This video is not available
        if "video is not available" in message:
            return ErrorCodeYYD.YYD_1001
        if "video unavailable" in message:
            return ErrorCodeYYD.YYD_1001
        return None


# EOF
