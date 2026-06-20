# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.error_code import ErrorCode


class ErrorCodeSUS(ErrorCode):
    """Error codes for SourcingUrlsService."""

    # wrong
    SUS_1001 = "Aucun profil de lancement sélectionné."
    SUS_1002 = "Le type de source d'URLs n'est pas supporté."
    SUS_1003 = "Le dossier d'export est vide."
    SUS_1004 = "Le dossier d'export possède des caractères interdits."
    SUS_1005 = "La liste des URLs à consommer est vide."
    SUS_1006 = "La 1ère URL à consommer est vide."
    SUS_1007 = "La 1ère URL à consommer possède 3 caractères ou moins."
    SUS_1008 = "Le dossier d'export ne peux pas être '.' ou './'"
    SUS_1009 = "Le dossier d'export ne peux pas commencer par '/'"
    SUS_1010 = "Aucune URL à consommer pour ce type de source"
    SUS_1011 = "Plus de 100 URLs disponibles (scraping longue durée)"
    SUS_1012 = "Plus de 1000 URLs disponibles (scraping longue durée)"

    # ???
    SUS_9999 = "Erreur inconnue."


# EOF
