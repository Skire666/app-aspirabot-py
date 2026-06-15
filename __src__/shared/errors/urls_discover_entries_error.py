# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum

from shared.enums import ErrorSeverityEnum
from shared.error_code import ErrorCode


class ErrorCodeUDE(ErrorCode, Enum):
    """Error codes for UrlsDiscoverEntriesModel."""

    # wrong
    UDE_1001 = ("#UDE-1001", "Aucune entrée disponible.", ErrorSeverityEnum.E_ERROR)
    UDE_1003 = ("#UDE-1003", "Aucune sortie définie.", ErrorSeverityEnum.E_ERROR)

    # ???
    UDE_9999 = ("#UDE-9999", "Erreur inconnue.", ErrorSeverityEnum.E_UNKNOWN)

    def __init__(self, code: str, user_message: str, severity: ErrorSeverityEnum) -> None:
        """Initialize the error code with its attributes."""
        self.code = code
        self.user_message = user_message
        self.severity = severity

    @classmethod
    def from_code(cls, code: str) -> ErrorCode:
        """Retourne l'instance de l'ErrorCode correspondant au code donné."""
        for error_code in ErrorCodeUDE:
            if error_code.code == code:
                return error_code
        raise ValueError(f"Code d'erreur inconnu: {code}")


# EOF
