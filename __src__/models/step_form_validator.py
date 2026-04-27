"""Domain validation for raw step form data.

The view layer only collects raw values. This module is responsible for
converting raw UI payloads into normalized step values used by services/models.
"""

from __future__ import annotations

from typing import Any, cast

from shared.step_types import StepType, StepValue, WAIT_UNIT_LABEL_TO_TOKEN


class StepFormValidationError(ValueError):
    """Error raised when a step form payload is invalid."""


_SUPPORTED_STEP_TYPES: tuple[StepType, ...] = (
    "open_url",
    "wait_seconds",
    "refresh_page",
    "download_image",
    "check_if_image_here",
    "click_element",
)


def normalize_step_form_value(step_type: str, raw_data: Any) -> StepValue:
    """Normalizes and validates a raw step payload from the UI.

    Args:
        step_type: Requested step type.
        raw_data: Raw payload collected from a step form view.

    Returns:
        A normalized payload compatible with StepScrappingModel.value.

    Raises:
        StepFormValidationError: If payload is invalid.
    """
    validated_type = _validate_step_type(step_type)

    if validated_type == "open_url":
        return _normalize_open_url(raw_data)
    if validated_type == "wait_seconds":
        return _normalize_wait_seconds(raw_data)
    if validated_type == "refresh_page":
        return _normalize_refresh_page(raw_data)
    if validated_type == "download_image":
        return _normalize_download_image(raw_data)
    if validated_type == "check_if_image_here":
        return _normalize_check_if_image_here(raw_data)
    if validated_type == "click_element":
        return _normalize_click_element(raw_data)

    raise StepFormValidationError("Type d'étape non supporté.")


def _validate_step_type(step_type: str) -> StepType:
    if step_type in _SUPPORTED_STEP_TYPES:
        return step_type
    raise StepFormValidationError("Type d'étape invalide.")


def _normalize_open_url(raw_data: Any) -> str:
    if isinstance(raw_data, dict):
        payload = cast(dict[str, Any], raw_data)
        value = str(payload.get("url", "")).strip()
    else:
        value = str(raw_data).strip() if raw_data is not None else ""

    if not value:
        raise StepFormValidationError("La valeur URL est obligatoire.")
    return value


def _normalize_wait_seconds(raw_data: Any) -> dict[str, int | str]:
    if isinstance(raw_data, dict):
        payload = cast(dict[str, Any], raw_data)
        raw_amount = payload.get("amount")
        raw_unit = payload.get("unit", "seconds")
    else:
        raw_amount = raw_data
        raw_unit = "seconds"

    amount = _parse_positive_int(raw_amount, "La durée")
    unit = _normalize_wait_unit(raw_unit)
    return {"amount": amount, "unit": unit}


def _normalize_refresh_page(raw_data: Any) -> bool:
    if isinstance(raw_data, dict):
        payload = cast(dict[str, Any], raw_data)
        return bool(payload.get("clear_cache", False))
    return bool(raw_data)


def _normalize_download_image(raw_data: Any) -> dict[str, int | str | bool]:
    if not isinstance(raw_data, dict):
        raise StepFormValidationError("Les options de téléchargement d'image sont obligatoires.")

    payload = cast(dict[str, Any], raw_data)
    mode = str(payload.get("mode", "")).strip().lower()
    if mode not in {"largest", "first", "all"}:
        raise StepFormValidationError("Le mode doit être largest, first ou all.")

    min_width = _parse_non_negative_int(payload.get("min_width"), "La largeur minimale")
    min_height = _parse_non_negative_int(payload.get("min_height"), "La hauteur minimale")
    max_width = _parse_non_negative_int(payload.get("max_width"), "La largeur maximale")
    max_height = _parse_non_negative_int(payload.get("max_height"), "La hauteur maximale")

    if max_width > 0 and max_width < min_width:
        raise StepFormValidationError("La largeur maximale doit être 0 ou >= à la largeur minimale.")
    if max_height > 0 and max_height < min_height:
        raise StepFormValidationError("La hauteur maximale doit être 0 ou >= à la hauteur minimale.")

    return {
        "mode": mode,
        "min_width": min_width,
        "min_height": min_height,
        "max_width": max_width,
        "max_height": max_height,
    }


def _normalize_check_if_image_here(raw_data: Any) -> dict[str, int | str | bool]:
    if not isinstance(raw_data, dict):
        raise StepFormValidationError("Les bornes d'image sont obligatoires.")

    payload = cast(dict[str, Any], raw_data)
    w1 = _parse_int(payload.get("w1"), "W1")
    w2 = _parse_int(payload.get("w2"), "W2")
    h1 = _parse_int(payload.get("h1"), "H1")
    h2 = _parse_int(payload.get("h2"), "H2")

    if w1 >= w2:
        raise StepFormValidationError("W1 doit être strictement inférieur à W2.")
    if h1 >= h2:
        raise StepFormValidationError("H1 doit être strictement inférieur à H2.")

    return {
        "w1": w1,
        "w2": w2,
        "h1": h1,
        "h2": h2,
    }


def _normalize_click_element(raw_data: Any) -> dict[str, int | str | bool]:
    if isinstance(raw_data, str):
        selector = raw_data.strip()
        if not selector:
            raise StepFormValidationError("Le sélecteur CSS est obligatoire.")
        return {
            "selector": selector,
            "normal": True,
            "forced": False,
            "js_direct": False,
            "verify_present": False,
        }

    if not isinstance(raw_data, dict):
        raise StepFormValidationError("La configuration de clic est obligatoire.")

    config = cast(dict[str, Any], raw_data)
    selector = str(config.get("selector", "")).strip()
    if not selector:
        raise StepFormValidationError("Le sélecteur CSS est obligatoire.")

    normal = bool(config.get("normal", False))
    forced = bool(config.get("forced", False))
    js_direct = bool(config.get("js_direct", False))
    verify_present = bool(config.get("verify_present", False))

    if not (normal or forced or js_direct):
        raise StepFormValidationError("Sélectionnez au moins un mode de clic (Normal, Forced ou JS Direct).")

    return {
        "selector": selector,
        "normal": normal,
        "forced": forced,
        "js_direct": js_direct,
        "verify_present": verify_present,
    }


def _normalize_wait_unit(raw_unit: Any) -> str:
    unit_token = str(raw_unit).strip().lower()

    # Accept UI labels and backend tokens for edit/backward compatibility.
    if unit_token in WAIT_UNIT_LABEL_TO_TOKEN:
        return WAIT_UNIT_LABEL_TO_TOKEN[unit_token]

    unit_aliases: dict[str, str] = {
        "h": "hours",
        "hour": "hours",
        "hours": "hours",
        "heure": "hours",
        "heures": "hours",
        "m": "minutes",
        "min": "minutes",
        "minute": "minutes",
        "minutes": "minutes",
        "s": "seconds",
        "sec": "seconds",
        "second": "seconds",
        "seconds": "seconds",
        "seconde": "seconds",
        "secondes": "seconds",
        "ms": "milliseconds",
        "millisecond": "milliseconds",
        "milliseconds": "milliseconds",
        "milli-sec": "milliseconds",
    }
    normalized = unit_aliases.get(unit_token)
    if normalized is None:
        raise StepFormValidationError("Unité de durée invalide.")
    return normalized


def _parse_positive_int(raw_value: Any, label: str) -> int:
    value = _parse_int(raw_value, label)
    if value <= 0:
        raise StepFormValidationError(f"{label} doit être un entier positif.")
    return value


def _parse_non_negative_int(raw_value: Any, label: str) -> int:
    value = _parse_int(raw_value, label)
    if value < 0:
        raise StepFormValidationError(f"{label} doit être un entier >= 0.")
    return value


def _parse_int(raw_value: Any, label: str) -> int:
    if isinstance(raw_value, bool):
        raise StepFormValidationError(f"{label} doit être un entier.")

    if isinstance(raw_value, int):
        return raw_value

    raw_text = str(raw_value).strip() if raw_value is not None else ""
    if not raw_text:
        raise StepFormValidationError(f"{label} est obligatoire.")

    if raw_text.startswith("-"):
        if raw_text[1:].isdigit():
            return int(raw_text)
        raise StepFormValidationError(f"{label} doit être un entier.")

    if raw_text.isdigit():
        return int(raw_text)

    raise StepFormValidationError(f"{label} doit être un entier.")
