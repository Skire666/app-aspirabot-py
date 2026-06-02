"""Tests for shared/path_util.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from shared.path_util import (
    clean_filename_youtube,
    get_current_working_directory,
    make_all_folders_if_not_exists,
)


class TestCleanFilenameYoutube:
    def test_alphanumeric_unchanged(self) -> None:
        assert clean_filename_youtube("hello123") == "hello123"

    def test_removes_forbidden_chars(self) -> None:
        result = clean_filename_youtube("hello/world:test?")
        for char in "/\\:?":
            assert char not in result

    def test_allows_spaces(self) -> None:
        assert " " in clean_filename_youtube("hello world")

    def test_allows_dots(self) -> None:
        result = clean_filename_youtube("file.mp4")
        assert "." in result

    def test_allows_hyphens_and_underscores(self) -> None:
        result = clean_filename_youtube("my-file_name")
        assert "-" in result
        assert "_" in result

    def test_empty_string(self) -> None:
        assert clean_filename_youtube("") == ""

    def test_all_forbidden_returns_empty(self) -> None:
        result = clean_filename_youtube("/\\:*?\"<>|")
        assert result == ""

    def test_mixed_keeps_allowed(self) -> None:
        result = clean_filename_youtube("My Video (2024) - Part 1.mp4")
        assert "My Video" in result
        assert "2024" in result
        assert "Part 1" in result


class TestGetCurrentWorkingDirectory:
    def test_returns_path(self) -> None:
        result = get_current_working_directory()
        assert isinstance(result, Path)

    def test_is_existing_directory(self) -> None:
        result = get_current_working_directory()
        assert result.exists()
        assert result.is_dir()


class TestMakeAllFoldersIfNotExists:
    def test_creates_directory_path(self, tmp_path: Path) -> None:
        target = tmp_path / "new_dir" / "sub_dir"
        make_all_folders_if_not_exists(target, is_file_path=False)
        assert target.is_dir()

    def test_creates_parent_for_file_path(self, tmp_path: Path) -> None:
        target = tmp_path / "sub" / "file.json"
        make_all_folders_if_not_exists(target, is_file_path=True)
        assert target.parent.is_dir()
        assert not target.exists()  # file itself should not be created

    def test_infers_file_from_suffix(self, tmp_path: Path) -> None:
        target = tmp_path / "auto" / "file.json"
        make_all_folders_if_not_exists(target)
        assert target.parent.is_dir()

    def test_infers_dir_when_no_suffix(self, tmp_path: Path) -> None:
        target = tmp_path / "auto_dir"
        make_all_folders_if_not_exists(target)
        assert target.is_dir()

    def test_existing_dir_no_error(self, tmp_path: Path) -> None:
        make_all_folders_if_not_exists(tmp_path, is_file_path=False)
        assert tmp_path.is_dir()

    def test_existing_file_uses_parent(self, tmp_path: Path) -> None:
        existing = tmp_path / "test.txt"
        existing.write_text("data")
        make_all_folders_if_not_exists(existing)
        assert tmp_path.is_dir()

    def test_accepts_string_path(self, tmp_path: Path) -> None:
        target = str(tmp_path / "str_dir" / "nested")
        make_all_folders_if_not_exists(target, is_file_path=False)
        assert Path(target).is_dir()
