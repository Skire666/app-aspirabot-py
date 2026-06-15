# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum

from shared.enums import ErrorSeverityEnum
from shared.error_code import ErrorCode
from shared.exception_util import AspirabotBaseError


class ErrorCodeUDI(ErrorCode, Enum):
    """Error codes for UrlsFolderJsonsModel."""

    # wrong
    UDI_1001 = ("#UDI-1001", "Aucune dossier disponible.", ErrorSeverityEnum.E_ERROR)
    UDI_1003 = ("#UDI-1003", "Le dossier n'existe pas.", ErrorSeverityEnum.E_ERROR)
    UDI_1004 = ("#UDI-1004", "Le dossier ne contient aucun fichier JSON.", ErrorSeverityEnum.E_ERROR)
    UDI_1005 = ("#UDI-1005", "Le regexp pour les fichiers JSON est vide.", ErrorSeverityEnum.E_ERROR)
    UDI_1006 = ("#UDI-1006", "Le regexp pour les fichiers JSON doit terminer par 'json'.", ErrorSeverityEnum.E_ERROR)
    UDI_1007 = ("#UDI-1007", "La clé de mappage est vide.", ErrorSeverityEnum.E_ERROR)
    UDI_1008 = ("#UDI-1008", "Le regexp pour les URLs est vide.", ErrorSeverityEnum.E_ERROR)

    # ???
    UDI_9999 = ("#UDI-9999", "Erreur inconnue.", ErrorSeverityEnum.E_UNKNOWN)

    def __init__(self, code: str, user_message: str, severity: ErrorSeverityEnum) -> None:
        """Initialize the error code with its attributes."""
        self.code = code
        self.user_message = user_message
        self.severity = severity

    @classmethod
    def from_code(cls, code: str) -> ErrorCode:
        """Retourne l'instance de l'ErrorCode correspondant au code donné."""
        for error_code in ErrorCodeUDI:
            if error_code.code == code:
                return error_code
        msg = f"Code d'erreur inconnu : {code}"
        raise AspirabotBaseError(msg)


# EOF
