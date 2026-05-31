# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from tkinter import messagebox


@staticmethod
def ask_duplicate_scenario_confirmation() -> bool:
    """Prompts the user for duplication confirmation.

    Returns:
        True if user confirmed the duplication, False otherwise.
    """
    return messagebox.askyesno("Confirmer", "Voulez-vous dupliquer ce scénario ?")


@staticmethod
def ask_delete_scenario_confirmation() -> bool:
    """Prompts the user for deletion confirmation.

    Returns:
        True if user confirmed the deletion, False otherwise.
    """
    return messagebox.askyesno("Confirmer", "Voulez-vous vraiment supprimer ce scénario ?")


def ask_delete_profile_confirmation(profile_name: str) -> bool:
    """Prompts the user for profile deletion confirmation.

    Args:
        profile_name: Display name of the profile shown in the dialog message.

    Returns:
        True if user confirmed the deletion, False otherwise.
    """
    return messagebox.askyesno("Confirmer", f"Voulez-vous vraiment supprimer le profil « {profile_name} » ?")


# EOF
