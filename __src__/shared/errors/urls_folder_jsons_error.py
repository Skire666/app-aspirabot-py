from enum import Enum

from enums import ErrorSeverityEnum
from shared.error_code import ErrorCode


class ErrorCodeUFJ(Enum, ErrorCode):
    """Error codes for UrlsFolderJsonsModel."""

    # wrong
    UFJ_1001 = ("#UFJ-1001", "Aucune dossier disponible.", ErrorSeverityEnum.E_ERROR)
    UFJ_1002 = ("#UFJ-1002", "Le dossier est invalide.", ErrorSeverityEnum.E_ERROR)
    UFJ_1003 = ("#UFJ-1003", "Aucun ordre de tri défini.", ErrorSeverityEnum.E_ERROR)
    UFJ_1004 = ("#UFJ-1004", "L'ordre de tri est invalide.", ErrorSeverityEnum.E_ERROR)
    UFJ_1005 = ("#UFJ-1005", "Le dossier n'existe pas.", ErrorSeverityEnum.E_ERROR)
    UFJ_1006 = ("#UFJ-1006", "Le dossier ne contient aucun fichier JSON.", ErrorSeverityEnum.E_ERROR)

    # ???
    UFJ_9999 = ("#UFJ-9999", "Erreur inconnue.", ErrorSeverityEnum.E_UNKNOWN)

    def __init__(self, code: str, user_message: str, severity: ErrorSeverityEnum) -> None:
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
        raise ValueError(f"Code d'erreur inconnu: {code}")
