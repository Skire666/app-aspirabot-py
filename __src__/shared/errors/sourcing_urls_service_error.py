# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum

from shared.enums import ErrorSeverityEnum
from shared.error_code import ErrorCode
from shared.exception_util import AspirabotBaseError


class ErrorCodeSUS(ErrorCode, Enum):
    """Error codes for SourcingUrlsService."""

    # wrong
    SUS_1001 = ("#SUS-1001", "Aucun profil de lancement défini.", ErrorSeverityEnum.E_ERROR)
    SUS_1002 = ("#SUS-1002", "Le type de source d'URLs n'est pas supporté.", ErrorSeverityEnum.E_ERROR)
    SUS_1003 = ("#SUS-1003", "Le chemin d'export est vide.", ErrorSeverityEnum.E_ERROR)
    SUS_1004 = ("#SUS-1004", "Le chemin d'export est invalide.", ErrorSeverityEnum.E_ERROR)
    SUS_1005 = ("#SUS-1005", "La liste des URLs à consommer est vide.", ErrorSeverityEnum.E_ERROR)
    SUS_1006 = ("#SUS-1006", "La 1ère URL à consommer est vide.", ErrorSeverityEnum.E_ERROR)
    SUS_1007 = ("#SUS-1007", "La 1ère URL à consommer possède 3 caractères ou moins.", ErrorSeverityEnum.E_ERROR)

    # ???
    SUS_9999 = ("#SUS-9999", "Erreur inconnue.", ErrorSeverityEnum.E_UNKNOWN)

    def __init__(self, code: str, user_message: str, severity: ErrorSeverityEnum) -> None:
        """Initialize the error code with its attributes."""
        self.code = code
        self.user_message = user_message
        self.severity = severity

    @classmethod
    def from_code(cls, code: str) -> ErrorCode:
        """Retourne l'instance de l'ErrorCode correspondant au code donné."""
        for error_code in ErrorCodeSUS:
            if error_code.code == code:
                return error_code
        msg = f"Code d'erreur inconnu : {code}"
        raise AspirabotBaseError(msg)


# EOF
