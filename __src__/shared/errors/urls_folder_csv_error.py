# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.error_code import ErrorCode


class ErrorCodeUFC(ErrorCode):
    """Error codes for UrlsFolderCsvModel."""

    # wrong
    UFC_1001 = "Le chemin vers le fichier '.csv' est vide."
    UFC_1002 = "Le chemin possède des caractères interdits."
    UFC_1003 = "Aucun ordre de tri défini."
    UFC_1004 = "L'ordre de tri est invalide."
    UFC_1005 = "Le fichier '.csv' n'existe pas."
    UFC_1006 = "Le fichier doit se terminer par l'extension'.csv'."
    UFC_1007 = "Date de modif. de début est vide."
    UFC_1008 = "Date de modif. de fin est vide."
    UFC_1009 = "Date de modif. de début postérieure à date de modif. de fin."
    UFC_1010 = "Le nombre maximal d'élément à lire doit être >= 1"

    # ???
    UFC_9999 = "Erreur inconnue."


# EOF
