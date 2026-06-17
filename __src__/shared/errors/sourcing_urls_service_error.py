# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.error_code import ErrorCode


class ErrorCodeSUS(ErrorCode):
    """Error codes for SourcingUrlsService."""

    # wrong
    SUS_1001 = "Aucun profil de lancement défini."
    SUS_1002 = "Le type de source d'URLs n'est pas supporté."
    SUS_1003 = "Le chemin d'export est vide."
    SUS_1004 = "Le chemin d'export est invalide."
    SUS_1005 = "La liste des URLs à consommer est vide."
    SUS_1006 = "La 1ère URL à consommer est vide."
    SUS_1007 = "La 1ère URL à consommer possède 3 caractères ou moins."

    # ???
    SUS_9999 = "Erreur inconnue."


# EOF
