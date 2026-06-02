"""Extra coverage for repositories/json_repository.py — line 51 and lines 165-167."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from repositories.json_repository import JsonFileRepository, _decode_hook
from shared.exception_util import JsonFileRepositoryError


class TestDecodeHookNonDictPassthrough:
    """Line 51: non-dict values returned unchanged by _decode_hook."""

    def test_string_passthrough(self) -> None:
        result = json.loads('"hello"', object_hook=_decode_hook)
        assert result == "hello"

    def test_integer_passthrough(self) -> None:
        result = json.loads("42", object_hook=_decode_hook)
        assert result == 42


class TestWriteFromDictOsError:
    """Lines 165-167: OSError during Path.open raises JsonFileRepositoryError."""

    def test_os_error_raises_json_file_repository_error(self, tmp_path: Path) -> None:
        file = tmp_path / "output.json"
        repo = JsonFileRepository()

        # Path.open is called by the repository — patch it to simulate an OS failure
        with patch("pathlib.Path.open", side_effect=OSError("permission denied")):
            with pytest.raises(JsonFileRepositoryError) as exc_info:
                repo.write_from_dict(file, {"k": "v"})

        assert "permission denied" in str(exc_info.value)
