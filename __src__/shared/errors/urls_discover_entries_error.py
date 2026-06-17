# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.error_code import ErrorCode


class ErrorCodeUDE(ErrorCode):
    """Error codes for UrlsDiscoverEntriesModel."""

    # wrong
    UDE_1001 = "Aucune entrée disponible."
    UDE_1003 = "Aucune sortie définie."

    # ???
    UDE_9999 = "Erreur inconnue."


# EOF
