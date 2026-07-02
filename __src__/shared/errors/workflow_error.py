# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.error_code import ErrorCode


class ErrorCodeWKF(ErrorCode):
    """Error codes for WorkflowService structure validation."""

    WKF_1001 = "L'étape de type 'E_OPEN_URL' est requise (1 seule)."
    WKF_1002 = "L'étape de type 'E_KILL_BROWSER' est requise (1 seule)."
    WKF_1003 = "La dernière étape doit être de type 'E_KILL_BROWSER'."
    WKF_1004 = "Il y a 2 étapes 'E_JUMP_TO_STEP' consécutives."
    WKF_1005 = "Il y a des étapes avec des identifiants dupliqués."
    WKF_1006 = "L'étape 'E_OPEN_URL' est à placer au début (sections ignorées)."
    WKF_1007 = "Il y a 2 étapes 'E_RESTART_TO_BEGINNING' consécutives."
    WKF_1008 = "L'étape 'E_RESTART_TO_BEGINNING' est à placer après l'étape 'E_OPEN_URL'"
    WKF_1009 = "Une étape 'EXPORT***' est requise avec les étapes de type 'EXTRACT***'"
    WKF_1010 = "Il y a 2 étapes 'EXPORT***'. 1 seule max. autorisées."
    WKF_9999 = "Erreur inconnue."


# EOF
