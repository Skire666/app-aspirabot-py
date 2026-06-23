# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.error_code import ErrorCode


class ErrorCodeYSL(ErrorCode):
    """Error codes for YoutubeSubtitlesListModel."""

    # wrong
    YSL_1001 = "Aucun sous-titre FR ou EN disponible."
    YSL_1002 = "Un ou plusieurs sous-titres ne possède aucun code."
    YSL_1003 = "Tous les sous-titres ont une qualité insuffisante (toutes à 0)."
    YSL_1004 = "Un ou plusieurs sous-titres sont de type UNSET"
    YSL_1005 = "Un ou plusieurs sous-titres sont de type UNKNOWN"

    # ???
    YSL_9999 = "Erreur inconnue."


# EOF
