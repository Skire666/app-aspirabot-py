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
    LAM_1007 = "Le compteur des erreurs globales est <= 0."
    LAM_1008 = "Le compteur des erreurs pour la step unitaire est <= 0."
    LAM_1009 = "La sélection pour la step unitaire est vide."
    LAM_1010 = "Le regexp de transformation d'URL n'est pas défini."
    LAM_1011 = "Le préfixe de transformation d'URL n'est pas défini."
    LAM_1012 = "L'URL de préchauffage doit commencer par 'http'"
    LAM_1013 = "L'URL de préchauffage fait moins de 4 caractères"

    # ???
    LAM_9999 = "Erreur inconnue."


# EOF
