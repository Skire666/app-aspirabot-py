# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------


from shared.error_code import ErrorCode


class ErrorCodeEXE(ErrorCode):
    """Error codes for SourcingUrlsService."""

    # wrong
    EXE_1001 = "Aucun scénario sélectionné."
    EXE_1002 = "Aucun profil de lancement sélectionné."
    EXE_1003 = "Aucun typologie sélectionnée pour la source."

    # ???
    EXE_9999 = "Erreur inconnue."


# EOF
