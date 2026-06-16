# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum

from shared.enums import SeverityEnum
from shared.error_code import ErrorCode
from shared.exception_util import AspirabotBaseError


class ErrorCodeLAM(ErrorCode, Enum):
    """Error codes for SourcingUrlsService."""

    # wrong§
    LAM_1001 = ("#LAM-1001", "Aucun type de source défini.", SeverityEnum.E_ERROR)
    LAM_1002 = ("#LAM-1002", "L'ID du scénario est vide.", SeverityEnum.E_ERROR)

    # ???
    LAM_9999 = ("#LAM-9999", "Erreur inconnue.", SeverityEnum.E_UNKNOWN)

    def __init__(self, code: str, user_message: str, severity: SeverityEnum) -> None:
        """Initialize the error code with its attributes."""
        self.code = code
        self.user_message = user_message
        self.severity = severity

    @classmethod
    def from_code(cls, code: str) -> ErrorCode:
        """Retourne l'instance de l'ErrorCode correspondant au code donné."""
        for error_code in ErrorCodeLAM:
            if error_code.code == code:
                return error_code
        msg = f"Code d'erreur inconnu : {code}"
        raise AspirabotBaseError(msg)


# EOF
