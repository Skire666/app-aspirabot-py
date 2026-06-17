"""Tkinter confirmation dialogs shared between scenario and profile presenters."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from tkinter import messagebox

from shared.i18n_fra import (
    C_DIALOG_CONFIRM_TITLE,
    C_DIALOG_DELETE_PROFILE_MSG,
    C_DIALOG_DELETE_SCENARIO_MSG,
    C_DIALOG_DUPLICATE_SCENARIO_MSG,
)


def ask_duplicate_scenario_confirmation() -> bool:
    """Prompts the user for duplication confirmation.

    Returns:
        True if user confirmed the duplication, False otherwise.
    """
    return messagebox.askyesno(C_DIALOG_CONFIRM_TITLE, C_DIALOG_DUPLICATE_SCENARIO_MSG)


def ask_delete_scenario_confirmation() -> bool:
    """Prompts the user for deletion confirmation.

    Returns:
        True if user confirmed the deletion, False otherwise.
    """
    return messagebox.askyesno(C_DIALOG_CONFIRM_TITLE, C_DIALOG_DELETE_SCENARIO_MSG)


def ask_delete_profile_confirmation(profile_name: str) -> bool:
    """Prompts the user for profile deletion confirmation.

    Args:
        profile_name: Display name of the profile shown in the dialog message.

    Returns:
        True if user confirmed the deletion, False otherwise.
    """
    return messagebox.askyesno(C_DIALOG_CONFIRM_TITLE, C_DIALOG_DELETE_PROFILE_MSG.format(profile_name=profile_name))


def ask_launch_scraping_confirmation(warning_msg: str) -> bool:
    """Prompts the user for launching scraping confirmation.

    Returns:
        True if user confirmed the launch, False otherwise.
    """
    return messagebox.askyesno(
        C_DIALOG_CONFIRM_TITLE, f"{warning_msg}\n\nÊtes-vous sûr de vouloir lancer le scraping ?"
    )


# EOF
