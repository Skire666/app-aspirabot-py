# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.error_code import ErrorCode


class ErrorCodeUDI(ErrorCode):
    """Error codes for UrlsFolderJsonsModel."""

    # wrong
    UDI_1001 = "Aucun dossier [IN] renseigné pour les URLs."
    UDI_1003 = "Dossier [IN] n'existe pas pour les URLs."
    UDI_1004 = "Dossier [IN] ne contient aucun fichier JSON."
    UDI_1005 = "Regexp [IN] des fichiers JSON est vide."
    UDI_1006 = "Regexp [IN] des fichiers JSON doit terminer par '.json'."
    UDI_1007 = "Clé de mappage [IN] est vide."
    UDI_1008 = "Regexp des URLs [IN] est vide."

    # ???
    UDI_9999 = "Erreur inconnue."


# EOF
