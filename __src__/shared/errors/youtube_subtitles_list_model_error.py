# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.error_code import ErrorCode


class ErrorCodeYSL(ErrorCode):
    """Error codes for YoutubeSubtitlesListModel."""

    # wrong
    YSL_1001 = "Aucune langue ni aucun sous-titre disponible (tout est vide)."
    YSL_1002 = "Un ou plusieurs sous-titres ne possède aucun code."
    YSL_1004 = "Un ou plusieurs sous-titres sont de type UNSET"
    YSL_1005 = "Un ou plusieurs sous-titres sont de type UNKNOWN"
    YSL_1007 = "Aucun sous-titre manuel avec FRA ou ENG"
    YSL_1006 = "Sous-titres manuels disponibles, mais pas avec FRA ou ENG."
    YSL_1008 = "Aucun sous-titre automatique avec FRA ou ENG"
    YSL_1009 = "Aucun sous-titre de qualité n'est disponible en FRA ou ENG."

    # ???
    YSL_9999 = "Erreur inconnue."


# EOF
