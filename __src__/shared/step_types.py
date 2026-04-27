"""Cross-cutting step type aliases and UI constants shared across all layers.

These definitions are shared between domain, presenter, and view layers.
No business logic lives here — only type contracts and pure data constants.
"""

from typing import Literal

StepType = Literal[
    "open_url",
    "wait_seconds",
    "refresh_page",
    "download_image",
    "check_if_image_here",
    "click_element",
]
StepValue = str | int | bool | dict[str, int | str | bool] | None

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
