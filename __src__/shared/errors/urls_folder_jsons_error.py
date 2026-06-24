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
    UFJ_1007 = "Date de modif. de début est vide."
    UFJ_1008 = "Date de modif. de fin est vide."
    UFJ_1009 = "Date de modif. de début postérieure à date de modif. de fin."
    UFJ_1010 = "Le filtre d'URL est vide."

    # ???
    UFJ_9999 = "Erreur inconnue."


# EOF
