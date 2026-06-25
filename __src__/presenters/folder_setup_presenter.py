"""Presenter for the first-launch folder setup dialog."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from collections.abc import Callable

from services.startup_service import StartupService
from shared.exception_util import AspirabotBaseError, InvalidFolderScenariosError
from shared.i18n_fra import C_FOLDER_SETUP_CREATE_ERROR, C_FOLDER_SETUP_INVALID_PATH
from view_models.folder_setup_view_model import FolderSetupViewModel

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class FolderSetupPresenter:
    """Wires FolderSetupViewModel actions to StartupService calls.

    On confirm, validates the entered path via the service, closes the dialog,
    and triggers the success callback. On cancel or error, sets the appropriate
    VM Var so the View can display feedback.

    Attributes:
        _vm: The folder-setup ViewModel.
        _service: StartupService used to validate and persist the folder path.
        _on_confirm: Callback invoked after the folder is successfully configured.
        _on_cancel: Callback invoked when the user cancels the dialog.
    """

    def __init__(
        self,
        vm: FolderSetupViewModel,
        service: StartupService,
        on_confirm: Callable[[], None],
        on_cancel: Callable[[], None],
    ) -> None:
        """Wire VM action hooks to local handlers.

        Args:
            vm: The folder-setup ViewModel.
            service: StartupService that owns the validation and persistence logic.
            on_confirm: Called after successful folder configuration.
            on_cancel: Called when the user aborts the setup.
        """
        self._vm = vm
        self._service = service
        self._on_confirm = on_confirm
        self._on_cancel = on_cancel
        self._logger = logging.getLogger(__name__)

        vm.bind_confirm(self._handle_confirm)
        vm.bind_cancel(self._handle_cancel)

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    def _handle_confirm(self) -> None:
        """Validate and persist the entered folder path.

        Calls the service to check syntax, create the directory, and save the
        config. On success, closes the dialog and fires *on_confirm*. On failure,
        writes the error message into *error_var* so the View can display it.
        """
        path = self._vm.path_var.get().strip()
        try:
            self._service.set_folder_scenarios(path)
        except InvalidFolderScenariosError:
            self._vm.error_var.set(C_FOLDER_SETUP_INVALID_PATH)
            return
        except OSError as exc:
            self._logger.error("Impossible de créer le dossier des scénarios : %s", exc, exc_info=True)
            self._vm.error_var.set(C_FOLDER_SETUP_CREATE_ERROR.format(exc=exc))
            return
        except AspirabotBaseError as exc:
            self._logger.error("Erreur lors de la configuration du dossier des scénarios : %s", exc, exc_info=True)
            self._vm.error_var.set(str(exc))
            return
        self._vm.error_var.set("")
        self._vm.close()
        self._on_confirm()

    def _handle_cancel(self) -> None:
        """Close the dialog and fire the cancellation callback."""
        self._vm.close()
        self._on_cancel()


# EOF
