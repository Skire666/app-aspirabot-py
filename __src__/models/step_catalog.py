"""Step metadata shared by domain and presenters."""

from models.step_scrapping_model import StepType


STEP_TYPE_TO_LABEL: dict[StepType, str] = {
    "open_url": "Ouvrir une URL",
    "wait_seconds": "Attendre X secondes",
    "refresh_page": "Rafraichir page",
    "download_image": "Télécharger une image",
    "check_if_image_here": "Vérifier présence image",
    "click_element": "Cliquer sur un élément",
}

WAIT_UNIT_LABEL_TO_TOKEN: dict[str, str] = {
    "heure": "hours",
    "minute": "minutes",
    "seconde": "seconds",
    "milli-sec": "milliseconds",
}
