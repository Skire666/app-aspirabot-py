# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum


class ErrorDataEnum(Enum):
    """Sub-category for data validation errors."""

    E_UNSET = "UNSET"  # valeur par défaut
    E_MISSING = "MISSING"  # donnée absente
    E_TYPE = "TYPE"  # mauvais type
    E_FORMAT = "FORMAT"  # mauvais format/pattern
    E_RANGE = "RANGE"  # hors bornes
    E_INCONSISTENCY = "INCONSISTENCY"  # contradiction entre champs
    E_DUPLICATE = "DUPLICATE"  # valeur en double
    E_PERMISSION = "PERMISSION"  # accès non autorisé
    E_STALE = "STALE"  # donnée périmée
    E_UNKNOWN = "UNKNOWN"  # type d'erreur inconnu


# EOF
