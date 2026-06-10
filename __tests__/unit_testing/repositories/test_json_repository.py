"""Tests for repositories/json_repository.py."""

from __future__ import annotations

import json
from datetime import date, datetime, time
from pathlib import Path

import pytest

from repositories.json_repository import JsonFileRepository, _JsonEncoder, _decode_hook


# ---------------------------------------------------------------------------
# _JsonEncoder
# ---------------------------------------------------------------------------


class TestJsonEncoder:
    def _encode(self, obj: object) -> object:
        return json.loads(json.dumps(obj, cls=_JsonEncoder))

    def test_datetime_encoded_as_tagged_object(self) -> None:
        dt = datetime(2024, 6, 1, 12, 30, 0)
        result = self._encode(dt)
        assert result["__type__"] == "datetime"
        assert "2024-06-01" in result["value"]

    def test_date_encoded_as_tagged_object(self) -> None:
        d = date(2024, 6, 1)
        result = self._encode(d)
        assert result["__type__"] == "date"
        assert result["value"] == "2024-06-01"

    def test_time_encoded_as_tagged_object(self) -> None:
        t = time(14, 30, 0)
        result = self._encode(t)
        assert result["__type__"] == "time"
        assert "14:30" in result["value"]

    def test_enum_encoded_as_string(self) -> None:
        from shared.enums import StepTypeEnum

        result = self._encode(StepTypeEnum.E_OPEN_URL)
        assert result == "OPEN_URL"

    def test_plain_dict_unchanged(self) -> None:
        result = self._encode({"key": "value", "number": 42})
        assert result == {"key": "value", "number": 42}

    def test_nested_datetime(self) -> None:
        dt = datetime(2024, 1, 15)
        result = self._encode({"ts": dt})
        assert result["ts"]["__type__"] == "datetime"


# ---------------------------------------------------------------------------
# _decode_hook
# ---------------------------------------------------------------------------


class TestDecodeHook:
    def test_datetime_tag_decoded(self) -> None:
        raw = {"__type__": "datetime", "value": "2024-06-01T12:30:00"}
        result = _decode_hook(raw)
        assert isinstance(result, datetime)
        assert result.year == 2024

    def test_date_tag_decoded(self) -> None:
        raw = {"__type__": "date", "value": "2024-06-01"}
        result = _decode_hook(raw)
        assert isinstance(result, date)
        assert result.month == 6

    def test_time_tag_decoded(self) -> None:
        raw = {"__type__": "time", "value": "14:30:00"}
        result = _decode_hook(raw)
        assert isinstance(result, time)
        assert result.hour == 14

    def test_plain_dict_unchanged(self) -> None:
        raw = {"key": "value"}
        result = _decode_hook(raw)
        assert result == {"key": "value"}

    def test_unknown_type_tag_unchanged(self) -> None:
        raw = {"__type__": "unknown", "value": "x"}
        result = _decode_hook(raw)
        assert result == {"__type__": "unknown", "value": "x"}


# ---------------------------------------------------------------------------
# JsonFileRepository
# ---------------------------------------------------------------------------


class TestJsonFileRepositoryReadFromPath:
    def test_non_existing_file_returns_empty_dict(self, tmp_path: Path) -> None:
        repo = JsonFileRepository()
        result = repo.read_from_path(tmp_path / "missing.json")
        assert result == {}

    def test_reads_existing_json(self, tmp_path: Path) -> None:
        file = tmp_path / "data.json"
        file.write_text(json.dumps({"hello": "world"}), encoding="utf-8")
        repo = JsonFileRepository()
        result = repo.read_from_path(file)
        assert result == {"hello": "world"}

    def test_returns_deep_copy(self, tmp_path: Path) -> None:
        file = tmp_path / "data.json"
        file.write_text(json.dumps({"list": [1, 2, 3]}), encoding="utf-8")
        repo = JsonFileRepository()
        first = repo.read_from_path(file)
        first["list"].append(99)
        second = repo.read_from_path(file)
        assert 99 not in second["list"]

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        from shared.exception_util import JsonFileRepositoryError

        file = tmp_path / "bad.json"
        file.write_text("not json {{{", encoding="utf-8")
        repo = JsonFileRepository()
        with pytest.raises(JsonFileRepositoryError):
            repo.read_from_path(file)

    def test_datetime_round_trip(self, tmp_path: Path) -> None:
        repo = JsonFileRepository()
        file = tmp_path / "ts.json"
        dt = datetime(2024, 6, 1, 12, 0, 0)
        repo.write_from_dict(file, {"ts": dt})
        result = repo.read_from_path(file)
        assert isinstance(result["ts"], datetime)
        assert result["ts"].year == 2024


class TestJsonFileRepositoryWriteFromDict:
    def test_creates_file(self, tmp_path: Path) -> None:
        file = tmp_path / "output.json"
        repo = JsonFileRepository()
        repo.write_from_dict(file, {"x": 1})
        assert file.exists()

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        file = tmp_path / "sub" / "nested" / "out.json"
        repo = JsonFileRepository()
        repo.write_from_dict(file, {"k": "v"})
        assert file.exists()

    def test_content_is_readable_json(self, tmp_path: Path) -> None:
        file = tmp_path / "out.json"
        repo = JsonFileRepository()
        data = {"name": "Alice", "age": 30}
        repo.write_from_dict(file, data)
        loaded = json.loads(file.read_text(encoding="utf-8"))
        assert loaded["name"] == "Alice"
        assert loaded["age"] == 30

    def test_write_then_read_round_trip(self, tmp_path: Path) -> None:
        file = tmp_path / "rt.json"
        repo = JsonFileRepository()
        original = {"items": [1, 2, 3], "flag": True}
        repo.write_from_dict(file, original)
        result = repo.read_from_path(file)
        assert result == original

    def test_write_invalidates_cache(self, tmp_path: Path) -> None:
        file = tmp_path / "cache.json"
        repo = JsonFileRepository()
        repo.write_from_dict(file, {"v": 1})
        first = repo.read_from_path(file)
        repo.write_from_dict(file, {"v": 2})
        second = repo.read_from_path(file)
        assert second["v"] == 2
        assert first["v"] == 1


class TestJsonFileRepositoryReadListFromPathRo:
    def test_absent_file_returns_empty_list(self, tmp_path: Path) -> None:
        repo = JsonFileRepository()
        result = repo.read_list_from_path_ro(tmp_path / "missing.json")
        assert result == []

    def test_reads_existing_list(self, tmp_path: Path) -> None:
        file = tmp_path / "data.json"
        file.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        repo = JsonFileRepository()
        result = repo.read_list_from_path_ro(file)
        assert result == [1, 2, 3]

    def test_returns_same_object_on_cache_hit(self, tmp_path: Path) -> None:
        file = tmp_path / "data.json"
        file.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        repo = JsonFileRepository()
        first = repo.read_list_from_path_ro(file)
        second = repo.read_list_from_path_ro(file)
        assert first is second

    def test_known_mtime_hits_cache_without_extra_stat(self, tmp_path: Path) -> None:
        file = tmp_path / "data.json"
        file.write_text(json.dumps(["a", "b"]), encoding="utf-8")
        repo = JsonFileRepository()
        # Prime the cache with the real mtime.
        mtime = file.stat().st_mtime_ns
        first = repo.read_list_from_path_ro(file, known_mtime_ns=mtime)
        # Same mtime → cache hit, same reference.
        second = repo.read_list_from_path_ro(file, known_mtime_ns=mtime)
        assert first is second
        assert first == ["a", "b"]

    def test_stale_mtime_reloads_from_disk(self, tmp_path: Path) -> None:
        file = tmp_path / "data.json"
        file.write_text(json.dumps([1]), encoding="utf-8")
        repo = JsonFileRepository()
        first = repo.read_list_from_path_ro(file)
        assert first == [1]
        # Overwrite: cache is invalidated by write_from_dict.
        repo.write_from_dict(file, [2])
        second = repo.read_list_from_path_ro(file)
        assert second == [2]

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        from shared.exception_util import JsonFileRepositoryError

        file = tmp_path / "bad.json"
        file.write_text("not json {{{", encoding="utf-8")
        repo = JsonFileRepository()
        with pytest.raises(JsonFileRepositoryError):
            repo.read_list_from_path_ro(file)
