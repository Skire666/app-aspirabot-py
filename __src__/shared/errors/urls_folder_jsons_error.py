# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.error_code import ErrorCode


class ErrorCodeUFJ(ErrorCode):
    """Error codes for UrlsFolderJsonsModel."""

    # wrong
    UFJ_1001 = "Le dossier '.json' est vide."
    UFJ_1002 = "Le dossier '.json' possède des caractères interdits."
    UFJ_1003 = "Aucun ordre de tri défini."
    UFJ_1004 = "L'ordre de tri est invalide."
    UFJ_1005 = "Le dossier '.json' n'existe pas."
    UFJ_1006 = "Le dossier ne contient aucun fichier '.json'."

    # ???
    UFJ_9999 = "Erreur inconnue."


# EOF
