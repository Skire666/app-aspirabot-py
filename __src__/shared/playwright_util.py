import glob
import os
import pathlib
import subprocess


def find_chromium_executable():
    """Cherche chrome.exe dans le dossier browsers path, sans dépendre d'un numéro de build hardcodé.

    Retourne le chemin trouvé, ou None.
    """
    browsers_path = os.environ["PLAYWRIGHT_BROWSERS_PATH"]

    if not pathlib.Path(browsers_path).is_dir():
        return None

    # Cherche tous les dossiers "chromium-*" (ex: chromium-1228, chromium-1187, etc.)
    pattern = os.path.join(browsers_path, "chromium-*", "chrome-win64", "chrome.exe")
    matches = glob.glob(pattern)

    if matches:
        # S'il y en a plusieurs (anciennes versions non nettoyées), prend la plus récente
        matches.sort(key=os.path.getmtime, reverse=True)
        return matches[0]

    return None


def is_chromium_installed():
    return find_chromium_executable() is not None


def install_chromium(log_callback=None):
    from playwright._impl._driver import compute_driver_executable

    driver_executable, driver_cli = compute_driver_executable()

    process = subprocess.Popen(
        [driver_executable, driver_cli, "install", "chromium"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    for line in process.stdout:
        if log_callback:
            log_callback(line.strip())
    process.wait()
    if process.returncode != 0:
        raise RuntimeError("Échec de l'installation de Chromium")


def setup_environment_playwright():
    if not is_chromium_installed():
        # can throw
        install_chromium()
