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

    # ???
    YYD_9999 = "Erreur inconnue."


# EOF
