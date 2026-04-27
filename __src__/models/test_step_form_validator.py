"""Unit tests for step form domain validation."""

import unittest

from models.step_form_validator import StepFormValidationError, normalize_step_form_value


class StepFormValidatorTests(unittest.TestCase):
    """Covers normalization and validation for raw step payloads."""

    def test_open_url_requires_value(self) -> None:
        with self.assertRaises(StepFormValidationError):
            normalize_step_form_value("open_url", {"url": "   "})

    def test_wait_seconds_normalizes_unit_label(self) -> None:
        value = normalize_step_form_value(
            "wait_seconds",
            {"amount": "5", "unit": "minute"},
        )
        self.assertEqual(value, {"amount": 5, "unit": "minutes"})

    def test_click_element_requires_one_mode(self) -> None:
        with self.assertRaises(StepFormValidationError):
            normalize_step_form_value(
                "click_element",
                {
                    "selector": ".submit",
                    "normal": False,
                    "forced": False,
                    "js_direct": False,
                },
            )

    def test_check_if_image_here_requires_ordered_bounds(self) -> None:
        with self.assertRaises(StepFormValidationError):
            normalize_step_form_value(
                "check_if_image_here",
                {"w1": "10", "w2": "5", "h1": "1", "h2": "2"},
            )

    def test_download_image_rejects_inverted_max(self) -> None:
        with self.assertRaises(StepFormValidationError):
            normalize_step_form_value(
                "download_image",
                {
                    "mode": "all",
                    "min_width": "100",
                    "min_height": "10",
                    "max_width": "50",
                    "max_height": "200",
                },
            )


if __name__ == "__main__":
    unittest.main()
