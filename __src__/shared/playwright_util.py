# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
import os
import pathlib
import subprocess

from shared.exception_util import ChromiumInstallationFailedError


def find_chromium_executable() -> str | None:
    """Cherche chrome.exe dans le dossier browsers path, sans dépendre d'un numéro de build hardcodé.

    Retourne le chemin trouvé, ou None.
    """
    browsers_path = os.environ["PLAYWRIGHT_BROWSERS_PATH"]

    if not pathlib.Path(browsers_path).is_dir():
        return None

    # Cherche tous les dossiers "chromium-*" (ex: chromium-1228, chromium-1187, etc.)
    matches = list(pathlib.Path(browsers_path).glob("chromium-*/chrome-win64/chrome.exe"))

    if matches:
        # S'il y en a plusieurs (anciennes versions non nettoyées), prend la plus récente
        matches.sort(key=os.path.getmtime, reverse=True)
        return str(matches[0])

    return None


def is_chromium_installed() -> bool:
    """Indique si un exécutable Chromium a déjà été détecté dans le dossier browsers path."""
    return find_chromium_executable() is not None


def install_chromium(log_callback: logging.Logger) -> None:
    """Installe Chromium via Playwright CLI.

    Args:
        log_callback: Logger utilisé pour relayer, ligne par ligne, la sortie du CLI.

    Raises:
        ChromiumInstallationFailedError: Si le CLI Playwright se termine en erreur.
    """
    from playwright._impl._driver import compute_driver_executable

    driver_executable, driver_cli = compute_driver_executable()

    process = subprocess.Popen(
        [driver_executable, driver_cli, "install", "chromium"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    stdout = process.stdout
    if stdout:
        for line in stdout:
            log_callback.info(line.strip())
    process.wait()
    if process.returncode != 0:
        raise ChromiumInstallationFailedError()


def setup_environment_playwright() -> None:
    """Configure l'environnement pour Playwright, en s'assurant que Chromium est installé."""
    if not is_chromium_installed():
        logger = logging.getLogger(__name__)
        install_chromium(logger)


# EOF
