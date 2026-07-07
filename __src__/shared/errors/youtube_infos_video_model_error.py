# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.error_code import ErrorCode


class ErrorCodeYIV(ErrorCode):
    """Error codes for YoutubeInfosVideoModel."""

    # wrong
    YIV_1001 = "L'URL de la vidéo est manquante."
    YIV_1002 = "Le titre de la vidéo est manquant."
    YIV_1003 = "L'URL de la page web est manquante."
    YIV_1004 = "La durée de la vidéo est manquante."
    YIV_1005 = "La durée de la vidéo est invalide ou égal à 0."
    YIV_1006 = "La langue de la vidéo est manquante."

    # ???
    YIV_9999 = "Erreur inconnue."


# EOF
