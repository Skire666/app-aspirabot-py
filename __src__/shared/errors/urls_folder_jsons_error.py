# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum

from shared.enums import SeverityEnum
from shared.error_code import ErrorCode
from shared.exception_util import AspirabotBaseError


class ErrorCodeUFJ(ErrorCode, Enum):
    """Error codes for UrlsFolderJsonsModel."""

    # wrong
    UFJ_1001 = ("#UFJ-1001", "Aucune dossier disponible.", SeverityEnum.E_ERROR)
    UFJ_1002 = ("#UFJ-1002", "Le dossier est invalide.", SeverityEnum.E_ERROR)
    UFJ_1003 = ("#UFJ-1003", "Aucun ordre de tri défini.", SeverityEnum.E_ERROR)
    UFJ_1004 = ("#UFJ-1004", "L'ordre de tri est invalide.", SeverityEnum.E_ERROR)
    UFJ_1005 = ("#UFJ-1005", "Le dossier n'existe pas.", SeverityEnum.E_ERROR)
    UFJ_1006 = ("#UFJ-1006", "Le dossier ne contient aucun fichier JSON.", SeverityEnum.E_ERROR)

    # ???
    UFJ_9999 = ("#UFJ-9999", "Erreur inconnue.", SeverityEnum.E_UNKNOWN)

    def __init__(self, code: str, user_message: str, severity: SeverityEnum) -> None:
        """Initialize the error code with its attributes."""
        self.code = code
        self.user_message = user_message
        self.severity = severity

    @classmethod
    def from_code(cls, code: str) -> ErrorCode:
        """Retourne l'instance de l'ErrorCode correspondant au code donné."""
        for error_code in ErrorCodeUFJ:
            if error_code.code == code:
                return error_code
        msg = f"Code d'erreur inconnu : {code}"
        raise AspirabotBaseError(msg)


# EOF
