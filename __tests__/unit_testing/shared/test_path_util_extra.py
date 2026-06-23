"""Additional tests for shared/path_util.py — folder_exists, count_files, path_has_valid_syntax, list_files."""

from __future__ import annotations

from pathlib import Path

import pytest

from shared.exception_util import InvalidDirectoryPathError
from shared.path_util import (
    count_files_in_folder,
    folder_exists,
    list_files,
    path_has_valid_syntax,
)


# ---------------------------------------------------------------------------
# folder_exists
# ---------------------------------------------------------------------------


class TestFolderExists:
    def test_returns_true_for_existing_directory(self, tmp_path: Path) -> None:
        assert folder_exists(tmp_path) is True

    def test_returns_false_for_nonexistent_path(self, tmp_path: Path) -> None:
        assert folder_exists(tmp_path / "nonexistent") is False

    def test_returns_false_for_file_path(self, tmp_path: Path) -> None:
        f = tmp_path / "file.txt"
        f.write_text("data")
        assert folder_exists(f) is False

    def test_accepts_string_path(self, tmp_path: Path) -> None:
        assert folder_exists(str(tmp_path)) is True


# ---------------------------------------------------------------------------
# count_files_in_folder
# ---------------------------------------------------------------------------


class TestCountFilesInFolder:
    def test_returns_zero_for_nonexistent_folder(self, tmp_path: Path) -> None:
        assert count_files_in_folder(tmp_path / "nonexistent", ".json") == 0

    def test_counts_matching_extension(self, tmp_path: Path) -> None:
        (tmp_path / "a.json").write_text("{}")
        (tmp_path / "b.json").write_text("{}")
        (tmp_path / "c.txt").write_text("x")
        assert count_files_in_folder(tmp_path, ".json") == 2

    def test_extension_without_dot_is_handled(self, tmp_path: Path) -> None:
        (tmp_path / "a.json").write_text("{}")
        assert count_files_in_folder(tmp_path, "json") == 1

    def test_returns_zero_when_no_matching_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.txt").write_text("x")
        assert count_files_in_folder(tmp_path, ".json") == 0

    def test_counts_url_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.url").write_text("x")
        (tmp_path / "b.url").write_text("x")
        assert count_files_in_folder(tmp_path, ".url") == 2


# ---------------------------------------------------------------------------
# path_has_valid_syntax
# ---------------------------------------------------------------------------


class TestPathHasValidSyntax:
    def test_empty_string_is_invalid(self) -> None:
        assert path_has_valid_syntax("") is False

    @pytest.mark.parametrize("valid_path", [
        "exports",
        "exports\\my_folder",
        "C:\\Users\\exports",
        "my-folder_name",
        "folder.with.dots",
        "sub\\sub2\\sub3",
    ])
    def test_valid_paths(self, valid_path: str) -> None:
        assert path_has_valid_syntax(valid_path) is True

    @pytest.mark.parametrize("invalid_path", [
        "invalid<path>",
        "path:with:colons",
        "path|pipe",
        "path*star",
        'path"quote',
        "path?question",
    ])
    def test_invalid_chars_are_rejected(self, invalid_path: str) -> None:
        assert path_has_valid_syntax(invalid_path) is False

    def test_trailing_space_is_invalid(self) -> None:
        assert path_has_valid_syntax("folder ") is False

    def test_trailing_dot_is_invalid(self) -> None:
        assert path_has_valid_syntax("folder.") is False

    def test_reserved_name_con_is_invalid(self) -> None:
        assert path_has_valid_syntax("CON") is False

    def test_reserved_name_nul_is_invalid(self) -> None:
        assert path_has_valid_syntax("NUL") is False

    def test_reserved_name_com1_is_invalid(self) -> None:
        assert path_has_valid_syntax("COM1") is False

    def test_reserved_name_lpt1_is_invalid(self) -> None:
        assert path_has_valid_syntax("LPT1") is False

    def test_dot_component_is_allowed(self) -> None:
        assert path_has_valid_syntax(".") is True

    def test_double_dot_component_is_allowed(self) -> None:
        assert path_has_valid_syntax("..") is True

    def test_path_exceeding_max_length_is_invalid(self) -> None:
        long_path = "a" * 256
        assert path_has_valid_syntax(long_path) is False

    def test_valid_drive_letter_path(self) -> None:
        assert path_has_valid_syntax("C:\\folder") is True


# ---------------------------------------------------------------------------
# list_files
# ---------------------------------------------------------------------------


class TestListFiles:
    def test_returns_files_with_extension(self, tmp_path: Path) -> None:
        (tmp_path / "a.json").write_text("{}")
        (tmp_path / "b.json").write_text("{}")
        (tmp_path / "c.txt").write_text("x")
        result = list_files(str(tmp_path), ".json")
        assert len(result) == 2

    def test_returns_empty_list_when_no_matching_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.txt").write_text("x")
        result = list_files(str(tmp_path), ".json")
        assert result == []

    def test_each_entry_is_tuple_of_path_and_datetime(self, tmp_path: Path) -> None:
        from datetime import datetime
        (tmp_path / "a.json").write_text("{}")
        result = list_files(str(tmp_path), ".json")
        assert len(result) == 1
        path, dt = result[0]
        assert isinstance(path, Path)
        assert isinstance(dt, datetime)

    def test_raises_for_nonexistent_directory(self, tmp_path: Path) -> None:
        with pytest.raises(InvalidDirectoryPathError):
            list_files(str(tmp_path / "nonexistent"), ".json")

    def test_extension_without_dot(self, tmp_path: Path) -> None:
        (tmp_path / "a.json").write_text("{}")
        result = list_files(str(tmp_path), "json")
        assert len(result) == 1
