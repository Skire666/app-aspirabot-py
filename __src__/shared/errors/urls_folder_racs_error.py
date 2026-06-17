# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.error_code import ErrorCode


class ErrorCodeUFR(ErrorCode):
    """Error codes for UrlsFolderRacsModel."""

    # wrong
    UFR_1001 = "Aucune dossier disponible."
    UFR_1002 = "Le dossier est invalide."
    UFR_1003 = "Aucun ordre de tri défini."
    UFR_1004 = "L'ordre de tri est invalide."
    UFR_1005 = "Le dossier n'existe pas."
    UFR_1006 = "Le dossier ne contient aucun fichier URL."

    # ???
    UFR_9999 = "Erreur inconnue."


# EOF
