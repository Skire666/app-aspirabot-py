"""Tests for shared/datetime_util.py."""

from __future__ import annotations

import re
from datetime import datetime

import pytest

from shared.datetime_util import (
    dict_with_key_to_optional_datetime,
    get_time_now_hh_mm_ss,
    get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff,
)


class TestGetTimeNowHhMmSs:
    def test_returns_string(self) -> None:
        result = get_time_now_hh_mm_ss()
        assert isinstance(result, str)

    def test_matches_hh_mm_ss_format(self) -> None:
        result = get_time_now_hh_mm_ss()
        assert re.fullmatch(r"\d{2}:\d{2}:\d{2}", result), f"Unexpected format: {result}"

    def test_hours_in_valid_range(self) -> None:
        result = get_time_now_hh_mm_ss()
        hh, mm, ss = (int(x) for x in result.split(":"))
        assert 0 <= hh <= 23
        assert 0 <= mm <= 59
        assert 0 <= ss <= 59


class TestGetTimestampFileFormat:
    def test_returns_string(self) -> None:
        result = get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff()
        assert isinstance(result, str)

    def test_matches_expected_pattern(self) -> None:
        result = get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff()
        pattern = r"\d{4}-\d{2}-\d{2}_\d{2}h\d{2}m\d{2}s\d+"
        assert re.fullmatch(pattern, result), f"Unexpected format: {result}"


class TestDictWithKeyToOptionalDatetime:
    def test_key_absent_returns_none(self) -> None:
        assert dict_with_key_to_optional_datetime({}, "ts") is None

    def test_key_with_none_returns_none(self) -> None:
        assert dict_with_key_to_optional_datetime({"ts": None}, "ts") is None

    def test_key_with_valid_iso_string(self) -> None:
        d = {"ts": "2024-01-15 10:30:00"}
        result = dict_with_key_to_optional_datetime(d, "ts")
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_key_with_datetime_object(self) -> None:
        dt = datetime(2024, 6, 1, 12, 0, 0)
        d = {"ts": dt}
        result = dict_with_key_to_optional_datetime(d, "ts")
        assert result is dt

    def test_key_with_invalid_string_returns_none(self) -> None:
        d = {"ts": "not-a-date"}
        result = dict_with_key_to_optional_datetime(d, "ts")
        assert result is None

    def test_key_with_integer_returns_none(self) -> None:
        d = {"ts": 12345}
        result = dict_with_key_to_optional_datetime(d, "ts")
        assert result is None

    def test_iso_with_microseconds(self) -> None:
        d = {"ts": "2024-06-01 14:30:45.123456"}
        result = dict_with_key_to_optional_datetime(d, "ts")
        assert isinstance(result, datetime)
        assert result.microsecond == 123456
