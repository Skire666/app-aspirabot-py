# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.error_code import ErrorCode


class ErrorCodeUFR(ErrorCode):
    """Error codes for UrlsFolderRacsModel."""

    # wrong
    UFR_1001 = "Le dossier '.url' est vide."
    UFR_1002 = "Le dossier '.url' possède des caractères interdits."
    UFR_1003 = "Aucun ordre de tri défini."
    UFR_1004 = "L'ordre de tri est invalide."
    UFR_1005 = "Le dossier '.url' n'existe pas."
    UFR_1006 = "Le dossier ne contient aucun fichier '.url'."

    # ???
    UFR_9999 = "Erreur inconnue."


# EOF
