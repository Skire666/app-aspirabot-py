# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum

from shared.enums import SeverityEnum
from shared.error_code import ErrorCode
from shared.exception_util import AspirabotBaseError


class ErrorCodeUDE(ErrorCode, Enum):
    """Error codes for UrlsDiscoverEntriesModel."""

    # wrong
    UDE_1001 = ("#UDE-1001", "Aucune entrée disponible.", SeverityEnum.E_ERROR)
    UDE_1003 = ("#UDE-1003", "Aucune sortie définie.", SeverityEnum.E_ERROR)

    # ???
    UDE_9999 = ("#UDE-9999", "Erreur inconnue.", SeverityEnum.E_UNKNOWN)

    def __init__(self, code: str, user_message: str, severity: SeverityEnum) -> None:
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
        msg = f"Code d'erreur inconnu : {code}"
        raise AspirabotBaseError(msg)


# EOF
