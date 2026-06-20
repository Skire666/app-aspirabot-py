# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.error_code import ErrorCode


class ErrorCodeUDO(ErrorCode):
    """Error codes for UrlsFolderJsonsModel."""

    # wrong
    UDO_1001 = "Aucun dossier [OUT] renseigné pour les URLs."
    UDO_1003 = "Dossier [OUT] n'existe pas pour les URLs."
    UDO_1004 = "Dossier [OUT] ne contient aucun fichier JSON."
    UDO_1005 = "Regexp [OUT] des fichiers JSON est vide."
    UDO_1006 = "Regexp [OUT] des fichiers JSON doit terminer par '.json'."
    UDO_1007 = "Clé de mappage [OUT] est vide."
    UDO_1008 = "Regexp pour les URLs [OUT] est vide."

    # ???
    UDO_9999 = "Erreur inconnue."


# EOF
