# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.error_code import ErrorCode


class ErrorCodeBRP(ErrorCode):
    """Error codes for UrlsFolderRacsModel."""

    # wrong
    BRP_1001 = "Le contexte de l'onglet n'est plus accessible."
    BRP_1002 = "Navigation interrompue par un autre processus.."
    BRP_1003 = "Problème lors de la résolution du nom de domaine (redirection, site down, ...)."
    BRP_1004 = "La page a déclenché un timeout (réseaux lent, serveur down, déconnecté)."
    BRP_1005 = "Toujours en erreur malgré 3 tentatives (erreur non récupérable)."
    BRP_1006 = "Navigateur fermé ou contexte non accessible (erreur fatale)."
    BRP_1007 = "Le renderer de la page a crashé."
    BRP_1008 = "Gel détecté : opération toujours en cours au-delà du délai de surveillance."

    # ???
    BRP_9999 = "Erreur inconnue."


# EOF
