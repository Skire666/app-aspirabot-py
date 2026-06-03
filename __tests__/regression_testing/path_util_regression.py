"""Regression tests — shared/path_util.py.

Freezes:
- clean_filename_youtube: keeps allowed chars, strips forbidden ones.
- get_current_working_directory: returns a valid Path object.
- make_all_folders_if_not_exists: all four inference branches (explicit file,
  explicit dir, existing path, path with suffix, path without suffix).
"""

from __future__ import annotations

import string
from pathlib import Path

import pytest

from shared.path_util import clean_filename_youtube, get_current_working_directory, make_all_folders_if_not_exists


# ---------------------------------------------------------------------------
# clean_filename_youtube
# ---------------------------------------------------------------------------


class TestCleanFilenameYoutube:
    def test_ascii_letters_digits_kept(self) -> None:
        assert clean_filename_youtube("abc123") == "abc123"

    def test_allowed_specials_kept(self) -> None:
        assert clean_filename_youtube("a-b_c. ()") == "a-b_c. ()"

    def test_forbidden_chars_removed(self) -> None:
        result = clean_filename_youtube("hello/world:foo?bar")
        assert "/" not in result
        assert ":" not in result
        assert "?" not in result
        assert "hello" in result
        assert "world" in result

    def test_empty_string_returns_empty(self) -> None:
        assert clean_filename_youtube("") == ""

    def test_all_forbidden_returns_empty(self) -> None:
        assert clean_filename_youtube("/:*?\"<>|") == ""

    def test_unicode_stripped(self) -> None:
        result = clean_filename_youtube("café résumé")
        assert "é" not in result
        assert "café" not in result

    @pytest.mark.parametrize("ch", list(string.ascii_letters + string.digits + "-_. ()"))
    def test_each_allowed_char_survives(self, ch: str) -> None:
        assert clean_filename_youtube(ch) == ch, f"Char {ch!r} should survive cleaning"


# ---------------------------------------------------------------------------
# get_current_working_directory
# ---------------------------------------------------------------------------


class TestGetCurrentWorkingDirectory:
    def test_returns_path_instance(self) -> None:
        result = get_current_working_directory()
        assert isinstance(result, Path)

    def test_returned_path_is_absolute(self) -> None:
        result = get_current_working_directory()
        assert result.is_absolute()

    def test_returned_path_exists(self) -> None:
        result = get_current_working_directory()
        assert result.exists()


# ---------------------------------------------------------------------------
# make_all_folders_if_not_exists
# ---------------------------------------------------------------------------


class TestMakeAllFoldersIfNotExists:
    def test_explicit_file_path_creates_parent(self, tmp_path: Path) -> None:
        """is_file_path=True must create the parent of a non-existent file."""
        target = tmp_path / "sub" / "data.json"
        make_all_folders_if_not_exists(target, is_file_path=True)
        assert target.parent.is_dir(), "Parent directory must exist after call"
        assert not target.exists(), "File itself must not be created"

    def test_explicit_dir_path_creates_directory(self, tmp_path: Path) -> None:
        """is_file_path=False must create the directory itself."""
        target = tmp_path / "my.dir.with.dots"
        make_all_folders_if_not_exists(target, is_file_path=False)
        assert target.is_dir()

    def test_infer_directory_from_existing_dir(self, tmp_path: Path) -> None:
        """When path already exists as a directory, it must remain as-is."""
        make_all_folders_if_not_exists(tmp_path)
        assert tmp_path.is_dir()

    def test_infer_file_from_suffix_creates_parent(self, tmp_path: Path) -> None:
        """Non-existent path with suffix → inferred as file, parent created."""
        target = tmp_path / "nested" / "report.csv"
        make_all_folders_if_not_exists(target)
        assert target.parent.is_dir()
        assert not target.exists()

    def test_infer_directory_from_no_suffix(self, tmp_path: Path) -> None:
        """Non-existent path without suffix → inferred as directory, created."""
        target = tmp_path / "new_folder"
        make_all_folders_if_not_exists(target)
        assert target.is_dir()

    def test_existing_file_creates_nothing_extra(self, tmp_path: Path) -> None:
        """When path already exists as a file, no error and parent stays unchanged."""
        existing_file = tmp_path / "existing.txt"
        existing_file.touch()
        make_all_folders_if_not_exists(existing_file)
        assert existing_file.exists()

    def test_string_path_accepted(self, tmp_path: Path) -> None:
        """Function must accept str as well as Path."""
        target = str(tmp_path / "from_str" / "file.txt")
        make_all_folders_if_not_exists(target, is_file_path=True)
        assert Path(target).parent.is_dir()

    def test_nested_deep_path_created(self, tmp_path: Path) -> None:
        target = tmp_path / "a" / "b" / "c" / "d"
        make_all_folders_if_not_exists(target, is_file_path=False)
        assert target.is_dir()
