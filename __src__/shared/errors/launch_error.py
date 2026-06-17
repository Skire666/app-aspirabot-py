# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------


from shared.error_code import ErrorCode


class ErrorCodeLAM(ErrorCode):
    """Error codes for SourcingUrlsService."""

    # wrong
    LAM_1001 = "Aucun type de source sélectionné parmis les choix."
    LAM_1002 = "L'ID du scénario est vide."
    LAM_1003 = "Le dossier d'export est vide."
    LAM_1004 = "Le dossier d'export possède des caractères interdits."
    LAM_1005 = "Le dossier d'export ne peux pas être '.' ou './'"
    LAM_1006 = "Le dossier d'export ne peux pas commencer par '/'"

    # ???
    LAM_9999 = "Erreur inconnue."


# EOF
