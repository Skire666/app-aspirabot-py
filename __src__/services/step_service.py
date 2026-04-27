"""Service layer for scraping workflow step management."""

from typing import Any, cast

from models.step_scrapping_model import StepScrappingModel
from shared.step_types import STEP_TYPE_TO_LABEL, StepType, StepValue


class StepService:
    """Handles workflow-step validation and transformation logic."""

    _TYPE_LABELS: dict[StepType, str] = dict(STEP_TYPE_TO_LABEL)

    def get_supported_types(self) -> list[StepType]:
        """Returns step types supported by the application."""
        return [
            "open_url",
            "wait_seconds",
            "refresh_page",
            "download_image",
            "check_if_image_here",
            "click_element",
        ]

    def get_label_for_type(self, step_type: StepType) -> str:
        """Returns the UI label associated with a step type."""
        return self._TYPE_LABELS[step_type]

    def create_step(self, step_type: str, value: Any) -> StepScrappingModel:
        """Creates and validates a step instance from user input.

        Args:
            step_type: Requested step type.
            value: Raw user payload from the form.

        Returns:
            A validated step model.

        Raises:
            ValueError: If type or value are invalid.
        """
        validated_type = self._validate_type(step_type)
        normalized_value = self._validate_value(validated_type, value)
        return StepScrappingModel(step_type=validated_type, value=normalized_value)

    def serialize_steps(self, steps: list[StepScrappingModel]) -> list[dict[str, Any]]:
        """Serializes a list of step models into JSON payloads."""
        return [step.to_dict() for step in steps]

    def deserialize_steps(self, steps_data: Any) -> list[StepScrappingModel]:
        """Deserializes raw payload into validated step models.

        Args:
            steps_data: Raw value loaded from JSON.

        Returns:
            A list of validated workflow steps.
        """
        if not isinstance(steps_data, list):
            return []

        normalized_steps: list[StepScrappingModel] = []
        for raw_step in cast(list[Any], steps_data):
            if not isinstance(raw_step, dict):
                continue

            raw_step_data = cast(dict[str, Any], raw_step)

            try:
                step_type = self._validate_type(raw_step_data.get("type"))
                step_value = self._validate_value(step_type, raw_step_data.get("value"))
            except ValueError:
                continue

            normalized_steps.append(StepScrappingModel(step_type=step_type, value=step_value))

        return normalized_steps

    def to_view_rows(self, steps: list[StepScrappingModel]) -> list[str]:
        """Builds human-readable labels for the workflow list UI."""
        rows: list[str] = []
        for index, step in enumerate(steps, start=1):
            label = self.get_label_for_type(step.step_type)
            if step.step_type == "open_url":
                rows.append(f"{index}. {label} -> {step.value}")
            elif step.step_type == "wait_seconds":
                if isinstance(step.value, dict):
                    wait_config = step.value
                    amount = int(wait_config.get("amount", 0))
                    unit = str(wait_config.get("unit", "seconds"))
                else:
                    amount = int(step.value) if isinstance(step.value, int) else 0
                    unit = "seconds"

                unit_label_map = {
                    "hours": "h",
                    "minutes": "min",
                    "seconds": "s",
                    "milliseconds": "ms",
                }
                unit_label = unit_label_map.get(unit, "s")
                rows.append(f"{index}. {label} -> {amount} {unit_label}")
            elif step.step_type == "refresh_page":
                refresh_with_cache_clear = bool(step.value)
                refresh_mode = "avec vidage cache" if refresh_with_cache_clear else "simple"
                rows.append(f"{index}. {label} -> {refresh_mode}")
            elif step.step_type == "download_image":
                config = step.value if isinstance(step.value, dict) else {}
                mode = str(config.get("mode", ""))
                min_width = int(config.get("min_width", 0))
                min_height = int(config.get("min_height", 0))
                max_width = int(config.get("max_width", 0))
                max_height = int(config.get("max_height", 0))
                if mode == "largest":
                    rows.append(
                        f"{index}. {label} -> la plus grande (min {min_width}x{min_height}, max {max_width}x{max_height})"
                    )
                elif mode == "first":
                    rows.append(
                        f"{index}. {label} -> la première (min {min_width}x{min_height}, max {max_width}x{max_height})"
                    )
                else:
                    rows.append(
                        f"{index}. {label} -> toutes (min {min_width}x{min_height}, max {max_width}x{max_height})"
                    )
            elif step.step_type == "check_if_image_here":
                config = step.value if isinstance(step.value, dict) else {}
                w1 = int(config.get("w1", 0))
                w2 = int(config.get("w2", 0))
                h1 = int(config.get("h1", 0))
                h2 = int(config.get("h2", 0))
                rows.append(f"{index}. {label} -> W:{w1}<X<{w2}, H:{h1}<Y<{h2}")
            elif step.step_type == "click_element":
                if isinstance(step.value, dict):
                    click_config = step.value
                    selector = str(click_config.get("selector", "")).strip()
                    modes: list[str] = []
                    if bool(click_config.get("normal", False)):
                        modes.append("normal")
                    if bool(click_config.get("forced", False)):
                        modes.append("forced")
                    if bool(click_config.get("js_direct", False)):
                        modes.append("js direct")
                    if not modes:
                        modes.append("normal")
                    rows.append(f"{index}. {label} -> {selector} [{', '.join(modes)}]")
                else:
                    rows.append(f"{index}. {label} -> {step.value}")
            else:
                rows.append(f"{index}. {label} -> {step.value}")
        return rows

    def to_view_items(self, steps: list[StepScrappingModel]) -> list[dict[str, Any]]:
        """Builds structured items consumable by the Tkinter workflow view."""
        rows = self.to_view_rows(steps)
        items: list[dict[str, Any]] = []
        for index, step in enumerate(steps):
            items.append(
                {
                    "label": rows[index],
                    "type": step.step_type,
                    "value": step.value,
                }
            )
        return items

    def _validate_type(self, step_type: Any) -> StepType:
        """Validates and narrows a raw step type value."""
        if step_type in {
            "open_url",
            "wait_seconds",
            "refresh_page",
            "download_image",
            "check_if_image_here",
            "click_element",
        }:
            return step_type
        raise ValueError("Unsupported step type")

    def _validate_value(self, step_type: StepType, value: Any) -> StepValue:
        """Validates and normalizes a raw step value according to step type."""
        if step_type == "open_url":
            text_value = str(value).strip() if value is not None else ""
            if not text_value:
                raise ValueError("URL value is required")
            return text_value

        if step_type == "click_element":
            # Backward compatibility: old payloads store only selector as string.
            if isinstance(value, str):
                selector = value.strip()
                if not selector:
                    raise ValueError("CSS selector is required")
                return {
                    "selector": selector,
                    "normal": True,
                    "forced": False,
                    "js_direct": False,
                    "verify_present": False,
                }

            if not isinstance(value, dict):
                raise ValueError("Click element options are required")

            click_config = cast(dict[str, Any], value)
            selector = str(click_config.get("selector", "")).strip()
            if not selector:
                raise ValueError("CSS selector is required")

            normal = bool(click_config.get("normal", False))
            forced = bool(click_config.get("forced", False))
            js_direct = bool(click_config.get("js_direct", False))
            verify_present = bool(click_config.get("verify_present", False))

            if not (normal or forced or js_direct):
                raise ValueError("At least one click mode must be selected")

            return {
                "selector": selector,
                "normal": normal,
                "forced": forced,
                "js_direct": js_direct,
                "verify_present": verify_present,
            }

        if step_type == "wait_seconds":
            if isinstance(value, dict):
                wait_config = cast(dict[str, Any], value)
                duration = self._parse_int(wait_config.get("amount"), "Wait duration")
                unit = self._normalize_wait_unit(wait_config.get("unit", "seconds"))
            else:
                if isinstance(value, bool):
                    raise ValueError("Wait duration must be a positive integer")

                if isinstance(value, int):
                    duration = value
                elif isinstance(value, str):
                    stripped_value = value.strip()
                    if not stripped_value:
                        raise ValueError("Wait duration is required")
                    if not stripped_value.isdigit():
                        raise ValueError("Wait duration must be a positive integer")
                    duration = int(stripped_value)
                else:
                    raise ValueError("Wait duration must be a positive integer")

                unit = "seconds"

            if duration <= 0:
                raise ValueError("Wait duration must be greater than zero")

            return {
                "amount": duration,
                "unit": unit,
            }

        if step_type == "refresh_page":
            return self._parse_refresh_bool(value)

        if step_type == "download_image":
            if not isinstance(value, dict):
                raise ValueError("Image download options are required")

            image_config = cast(dict[str, Any], value)

            mode = image_config.get("mode")
            if mode not in {"largest", "first", "all"}:
                raise ValueError("Download mode must be 'largest', 'first' or 'all'")

            # Keep width/height thresholds for every mode.
            min_width = self._parse_non_negative_int(image_config.get("min_width", 0), "Minimum width")
            min_height = self._parse_non_negative_int(image_config.get("min_height", 0), "Minimum height")
            max_width = self._parse_non_negative_int(image_config.get("max_width", 0), "Maximum width")
            max_height = self._parse_non_negative_int(image_config.get("max_height", 0), "Maximum height")

            if max_width > 0 and max_width < min_width:
                raise ValueError("Maximum width must be 0 (disabled) or greater than or equal to minimum width")
            if max_height > 0 and max_height < min_height:
                raise ValueError("Maximum height must be 0 (disabled) or greater than or equal to minimum height")

            return {
                "mode": str(mode),
                "min_width": min_width,
                "min_height": min_height,
                "max_width": max_width,
                "max_height": max_height,
            }

        if step_type == "check_if_image_here":
            if not isinstance(value, dict):
                raise ValueError("Image size range options are required")

            size_config = cast(dict[str, Any], value)

            w1 = self._parse_int(size_config.get("w1"), "W1")
            w2 = self._parse_int(size_config.get("w2"), "W2")
            h1 = self._parse_int(size_config.get("h1"), "H1")
            h2 = self._parse_int(size_config.get("h2"), "H2")

            if w1 >= w2:
                raise ValueError("W1 must be strictly less than W2")
            if h1 >= h2:
                raise ValueError("H1 must be strictly less than H2")

            return {
                "w1": w1,
                "w2": w2,
                "h1": h1,
                "h2": h2,
            }

        raise ValueError("Unsupported step type")

    def _parse_refresh_bool(self, value: Any) -> bool:
        """Parses refresh options from bool-compatible inputs."""
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, int):
            return value != 0
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"", "false", "0", "no", "non"}:
                return False
            if normalized in {"true", "1", "yes", "oui"}:
                return True
        raise ValueError("Refresh option must be a boolean value")

    def _parse_int(self, value: Any, field_name: str) -> int:
        """Parses a required integer value from string or int inputs."""
        if isinstance(value, bool):
            raise ValueError(f"{field_name} must be an integer")
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                raise ValueError(f"{field_name} is required")
            if raw.startswith("-"):
                signless = raw[1:]
                if signless.isdigit():
                    return int(raw)
                raise ValueError(f"{field_name} must be an integer")
            if raw.isdigit():
                return int(raw)
            raise ValueError(f"{field_name} must be an integer")
        raise ValueError(f"{field_name} must be an integer")

    def _normalize_wait_unit(self, value: Any) -> str:
        """Normalizes wait unit names to canonical storage tokens."""
        unit = str(value).strip().lower()
        unit_aliases = {
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

        normalized = unit_aliases.get(unit)
        if normalized is None:
            raise ValueError("Unsupported wait unit")
        return normalized

    def _parse_non_negative_int(self, value: Any, field_name: str) -> int:
        """Parses a non-negative integer value and validates lower bound."""
        parsed = self._parse_int(value, field_name)
        if parsed < 0:
            raise ValueError(f"{field_name} must be greater than or equal to 0")
        return parsed
