# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.error_code import ErrorCode


class ErrorCodeUML(ErrorCode):
    """Error codes for UrlsManualListModel."""

    # wrong
    UML_1001 = "Aucune URL disponible."
    UML_1002 = "Une ou plusieurs URLs possèdent 3 caractères ou moins."

    # ???
    UML_9999 = "Erreur inconnue."


# EOF
