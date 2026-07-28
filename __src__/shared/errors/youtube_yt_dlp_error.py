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
        for pattern, code in _MESSAGE_PATTERNS:
            if pattern in message:
                return code
        return None


# Substring → simplified error code, checked in order (first match wins).
_MESSAGE_PATTERNS: tuple[tuple[str, ErrorCodeYYD], ...] = (
    # Z0-Bb0AUHZk: Premieres in 11 days
    (" premieres in ", ErrorCodeYYD.YYD_1005),
    # join this channel to get access to members-only content like this video
    (" this channel to get access to ", ErrorCodeYYD.YYD_1004),
    # This video is available to this channel's members
    (" video is available to this channel's members", ErrorCodeYYD.YYD_1003),
    # Sign in to confirm your age. This video may be inappropriate for some users.
    (" may be inappropriate for ", ErrorCodeYYD.YYD_1002),
    (" in to confirm your age", ErrorCodeYYD.YYD_1002),
    # Video unavailable. This video is not available
    ("video is not available", ErrorCodeYYD.YYD_1001),
    ("video unavailable", ErrorCodeYYD.YYD_1001),
)


# EOF
