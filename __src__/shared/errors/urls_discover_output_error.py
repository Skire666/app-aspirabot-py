# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum

from shared.enums import SeverityEnum
from shared.error_code import ErrorCode
from shared.exception_util import AspirabotBaseError


class ErrorCodeUDO(ErrorCode, Enum):
    """Error codes for UrlsFolderJsonsModel."""

    # wrong
    UDO_1001 = ("#UDO-1001", "Aucune dossier [OUT] disponible.", SeverityEnum.E_ERROR)
    UDO_1003 = ("#UDO-1003", "Dossier [OUT] n'existe pas.", SeverityEnum.E_ERROR)
    UDO_1004 = ("#UDO-1004", "Dossier [OUT] ne contient aucun fichier JSON.", SeverityEnum.E_WARNING)
    UDO_1005 = ("#UDO-1005", "Regexp [OUT] des fichiers JSON est vide.", SeverityEnum.E_ERROR)
    UDO_1006 = ("#UDO-1006", "Regexp [OUT] des fichiers JSON doit terminer par '.json'.", SeverityEnum.E_ERROR)
    UDO_1007 = ("#UDO-1007", "Clé de mappage [OUT] est vide.", SeverityEnum.E_ERROR)
    UDO_1008 = ("#UDO-1008", "Regexp pour les URLs [OUT] est vide.", SeverityEnum.E_ERROR)

    # ???
    UDO_9999 = ("#UDO-9999", "Erreur inconnue.", SeverityEnum.E_UNKNOWN)

    def __init__(self, code: str, user_message: str, severity: SeverityEnum) -> None:
        """Initialize the error code with its attributes."""
        self.code = code
        self.user_message = user_message
        self.severity = severity

    @classmethod
    def from_code(cls, code: str) -> ErrorCode:
        """Retourne l'instance de l'ErrorCode correspondant au code donné."""
        for error_code in ErrorCodeUDO:
            if error_code.code == code:
                return error_code
        msg = f"Code d'erreur inconnu : {code}"
        raise AspirabotBaseError(msg)


# EOF
