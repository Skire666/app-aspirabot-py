"""Tests for shared/time_util.py."""

from __future__ import annotations

import pytest

from shared.exception_util import InvalidDurationError, InvalidTimeUnitError
from shared.time_util import convert_to_ms, convert_to_sec


class TestConvertToMs:
    # --- happy-path unit conversions ---

    def test_seconds_to_ms(self) -> None:
        assert convert_to_ms(1, "s") == 1000

    def test_seconds_alias_sec(self) -> None:
        assert convert_to_ms(2, "sec") == 2000

    def test_seconds_alias_sec_dot(self) -> None:
        assert convert_to_ms(3, "sec.") == 3000

    def test_minutes_to_ms(self) -> None:
        assert convert_to_ms(1, "m") == 60_000

    def test_minutes_alias_min(self) -> None:
        assert convert_to_ms(2, "min") == 120_000

    def test_minutes_alias_min_dot(self) -> None:
        assert convert_to_ms(1, "min.") == 60_000

    def test_milliseconds_identity(self) -> None:
        assert convert_to_ms(500, "ms") == 500

    def test_milliseconds_alias_millisec(self) -> None:
        assert convert_to_ms(250, "millisec") == 250

    def test_milliseconds_alias_millisec_dot(self) -> None:
        assert convert_to_ms(100, "millisec.") == 100

    def test_zero_duration(self) -> None:
        assert convert_to_ms(0, "s") == 0

    # --- error cases ---

    def test_empty_unit_raises(self) -> None:
        with pytest.raises(InvalidTimeUnitError):
            convert_to_ms(1, "")

    def test_unknown_unit_raises(self) -> None:
        with pytest.raises(InvalidTimeUnitError):
            convert_to_ms(1, "hours")

    def test_negative_duration_raises(self) -> None:
        with pytest.raises(InvalidDurationError):
            convert_to_ms(-1, "s")

    def test_very_negative_duration_raises(self) -> None:
        with pytest.raises(InvalidDurationError):
            convert_to_ms(-999, "ms")


class TestConvertToSec:
    # --- happy-path ---

    def test_seconds_identity(self) -> None:
        assert convert_to_sec(1, "s") == pytest.approx(1.0)

    def test_minutes_to_sec(self) -> None:
        assert convert_to_sec(2, "m") == pytest.approx(120.0)

    def test_minutes_alias_min(self) -> None:
        assert convert_to_sec(1, "min") == pytest.approx(60.0)

    def test_minutes_alias_min_dot(self) -> None:
        assert convert_to_sec(1, "min.") == pytest.approx(60.0)

    def test_ms_to_sec(self) -> None:
        assert convert_to_sec(1000, "ms") == pytest.approx(1.0)

    def test_millisec_alias(self) -> None:
        assert convert_to_sec(500, "millisec") == pytest.approx(0.5)

    def test_millisec_dot_alias(self) -> None:
        assert convert_to_sec(250, "millisec.") == pytest.approx(0.25)

    def test_sec_alias(self) -> None:
        assert convert_to_sec(5, "sec") == pytest.approx(5.0)

    def test_sec_dot_alias(self) -> None:
        assert convert_to_sec(10, "sec.") == pytest.approx(10.0)

    def test_zero_duration(self) -> None:
        assert convert_to_sec(0, "s") == pytest.approx(0.0)

    # --- error cases ---

    def test_empty_unit_raises(self) -> None:
        with pytest.raises(InvalidTimeUnitError):
            convert_to_sec(1, "")

    def test_unknown_unit_raises(self) -> None:
        with pytest.raises(InvalidTimeUnitError):
            convert_to_sec(1, "days")

    def test_negative_duration_raises(self) -> None:
        with pytest.raises(InvalidDurationError):
            convert_to_sec(-1, "s")
