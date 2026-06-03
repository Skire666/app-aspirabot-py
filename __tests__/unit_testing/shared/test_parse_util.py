"""Tests for shared/parse_util.py."""

from __future__ import annotations

from unittest.mock import MagicMock

from shared.parse_util import safe_int_from_dict, safe_int_from_str


class TestSafeIntFromStr:
    def test_valid_integer_string(self) -> None:
        assert safe_int_from_str("42", 0) == 42

    def test_negative_integer_string(self) -> None:
        assert safe_int_from_str("-10", 0) == -10

    def test_zero_string(self) -> None:
        assert safe_int_from_str("0", 99) == 0

    def test_non_numeric_returns_default(self) -> None:
        assert safe_int_from_str("abc", 7) == 7

    def test_empty_string_returns_default(self) -> None:
        assert safe_int_from_str("", -1) == -1

    def test_float_string_returns_default(self) -> None:
        # "3.14" is not a valid int string
        assert safe_int_from_str("3.14", 0) == 0

    def test_none_returns_default(self) -> None:
        assert safe_int_from_str(None, 5) == 5  # type: ignore[arg-type]

    def test_whitespace_returns_default(self) -> None:
        assert safe_int_from_str("  ", -1) == -1


class TestSafeIntFromDict:
    def _make_var(self, value: str) -> MagicMock:
        var = MagicMock()
        var.get.return_value = value
        return var

    def test_valid_key_returns_int(self) -> None:
        widgets = {"duration": self._make_var("10")}
        assert safe_int_from_dict(widgets, "duration", 0) == 10

    def test_missing_key_returns_default(self) -> None:
        assert safe_int_from_dict({}, "duration", 99) == 99

    def test_key_present_but_non_numeric_returns_default(self) -> None:
        widgets = {"duration": self._make_var("abc")}
        assert safe_int_from_dict(widgets, "duration", 5) == 5

    def test_key_present_but_empty_returns_default(self) -> None:
        widgets = {"duration": self._make_var("")}
        assert safe_int_from_dict(widgets, "duration", 3) == 3

    def test_negative_value(self) -> None:
        widgets = {"timeout": self._make_var("-5")}
        assert safe_int_from_dict(widgets, "timeout", 0) == -5

    def test_zero_value(self) -> None:
        widgets = {"count": self._make_var("0")}
        assert safe_int_from_dict(widgets, "count", 99) == 0
