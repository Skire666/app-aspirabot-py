# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum

from shared.enums import ErrorSeverityEnum
from shared.error_code import ErrorCode
from shared.exception_util import AspirabotBaseError


class ErrorCodeUML(ErrorCode, Enum):
    """Error codes for UrlsManualListModel."""

    # wrong
    UML_1001 = ("#UML-1001", "Aucune URL disponible.", ErrorSeverityEnum.E_ERROR)
    UML_1002 = ("#UML-1002", "Une ou plusieurs URLs possèdent 3 caractères ou moins.", ErrorSeverityEnum.E_ERROR)

    # ???
    UML_9999 = ("#UML-9999", "Erreur inconnue.", ErrorSeverityEnum.E_UNKNOWN)

    def __init__(self, code: str, user_message: str, severity: ErrorSeverityEnum) -> None:
        """Initialize the error code with its attributes."""
        self.code = code
        self.user_message = user_message
        self.severity = severity

    @classmethod
    def from_code(cls, code: str) -> ErrorCode:
        """Retourne l'instance de l'ErrorCode correspondant au code donné."""
        for error_code in ErrorCodeUML:
            if error_code.code == code:
                return error_code
        msg = f"Code d'erreur inconnu : {code}"
        raise AspirabotBaseError(msg)


# EOF
