# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum

from shared.enums import SeverityEnum
from shared.error_code import ErrorCode
from shared.exception_util import AspirabotBaseError


class ErrorCodeUDI(ErrorCode, Enum):
    """Error codes for UrlsFolderJsonsModel."""

    # wrong
    UDI_1001 = ("#UDI-1001", "Aucune dossier [IN] disponible.", SeverityEnum.E_ERROR)
    UDI_1003 = ("#UDI-1003", "Dossier [IN] n'existe pas.", SeverityEnum.E_ERROR)
    UDI_1004 = ("#UDI-1004", "Dossier [IN] ne contient aucun fichier JSON.", SeverityEnum.E_ERROR)
    UDI_1005 = ("#UDI-1005", "Regexp [IN] des fichiers JSON est vide.", SeverityEnum.E_ERROR)
    UDI_1006 = ("#UDI-1006", "Regexp [IN] des fichiers JSON doit terminer par '.json'.", SeverityEnum.E_ERROR)
    UDI_1007 = ("#UDI-1007", "Clé de mappage [IN] est vide.", SeverityEnum.E_ERROR)
    UDI_1008 = ("#UDI-1008", "Regexp des URLs [IN] est vide.", SeverityEnum.E_ERROR)

    # ???
    UDI_9999 = ("#UDI-9999", "Erreur inconnue.", SeverityEnum.E_UNKNOWN)

    def __init__(self, code: str, user_message: str, severity: SeverityEnum) -> None:
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
