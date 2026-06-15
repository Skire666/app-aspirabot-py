from enum import Enum

from shared.enums import ErrorSeverityEnum
from shared.error_code import ErrorCode


class ErrorCodeUFR(ErrorCode, Enum):
    """Error codes for UrlsFolderRacsModel."""

    # wrong
    UFR_1001 = ("#UFR-1001", "Aucune dossier disponible.", ErrorSeverityEnum.E_ERROR)
    UFR_1002 = ("#UFR-1002", "Le dossier est invalide.", ErrorSeverityEnum.E_ERROR)
    UFR_1003 = ("#UFR-1003", "Aucun ordre de tri défini.", ErrorSeverityEnum.E_ERROR)
    UFR_1004 = ("#UFR-1004", "L'ordre de tri est invalide.", ErrorSeverityEnum.E_ERROR)
    UFR_1005 = ("#UFR-1005", "Le dossier n'existe pas.", ErrorSeverityEnum.E_ERROR)
    UFR_1006 = ("#UFR-1006", "Le dossier ne contient aucun fichier URL.", ErrorSeverityEnum.E_ERROR)

    # ???
    UFR_9999 = ("#UFR-9999", "Erreur inconnue.", ErrorSeverityEnum.E_UNKNOWN)

    def __init__(self, code: str, user_message: str, severity: ErrorSeverityEnum) -> None:
        """Initialize the error code with its attributes."""
        self.code = code
        self.user_message = user_message
        self.severity = severity

    @classmethod
    def from_code(cls, code: str) -> ErrorCode:
        """Retourne l'instance de l'ErrorCode correspondant au code donné."""
        for error_code in ErrorCodeUFR:
            if error_code.code == code:
                return error_code
        raise ValueError(f"Code d'erreur inconnu: {code}")
