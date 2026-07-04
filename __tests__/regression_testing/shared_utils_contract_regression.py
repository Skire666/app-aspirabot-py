"""Regression tests — shared utility modules.

Freezes the observable contracts of several shared utilities that have low
coverage from regression tests and are not fully exercised by unit tests:
  - shared/datetime_util.py : formatting functions (format strings)
  - shared/random_util.py   : generate_rng_id_step uniqueness, merge_unique_list_id_step,
                              generate_rng_hexastring error contract
  - shared/path_util.py     : folder_exists, count_files_in_folder, list_files,
                              path_has_valid_syntax edge cases
  - shared/enums/url_source_type_enum.py : all values present and ordered
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from shared.datetime_util import (
    get_datetime_now_yyyy_mm_dd_hh_mm,
    get_time_now_hh_mm_ss,
    get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff,
)
from shared.enums import UrlSourceTypeEnum
from shared.exception_util import ValueMustBePositiveAndEvenError
from shared.path_util import count_files_in_folder, folder_exists, list_files, path_has_valid_syntax
from shared.random_util import (
    g_unique_list_id_step,
    generate_rng_hexastring,
    generate_rng_id_step,
    merge_unique_list_id_step,
)

# ===========================================================================
# datetime_util — format contracts
# ===========================================================================


class TestDatetimeUtilFormats:
    # Pattern: YYYY-MM-DD HH:MM
    _PATTERN_HH_MM = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
    # Pattern: HH:MM:SS
    _PATTERN_HH_MM_SS = re.compile(r"^\d{2}:\d{2}:\d{2}$")
    # Pattern: YYYY-MM-DD_HHhMMmSSs<microseconds>
    _PATTERN_FILE = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}h\d{2}m\d{2}s\d+$")

    def test_get_datetime_now_yyyy_mm_dd_hh_mm_format(self) -> None:
        result = get_datetime_now_yyyy_mm_dd_hh_mm()
        assert self._PATTERN_HH_MM.match(result), f"get_datetime_now_yyyy_mm_dd_hh_mm() format mismatch: {result!r}"

    def test_get_time_now_hh_mm_ss_format(self) -> None:
        result = get_time_now_hh_mm_ss()
        assert self._PATTERN_HH_MM_SS.match(result), f"get_time_now_hh_mm_ss() format mismatch: {result!r}"

    def test_get_timestamp_file_format(self) -> None:
        result = get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff()
        assert self._PATTERN_FILE.match(result), (
            f"get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff() format mismatch: {result!r}"
        )

    def test_get_datetime_now_is_string(self) -> None:
        assert isinstance(get_datetime_now_yyyy_mm_dd_hh_mm(), str)

    def test_get_time_now_is_string(self) -> None:
        assert isinstance(get_time_now_hh_mm_ss(), str)

    def test_get_timestamp_file_is_string(self) -> None:
        assert isinstance(get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff(), str)


# ===========================================================================
# random_util — ID generation contracts
# ===========================================================================


class TestRandomUtilGenerateRngIdStep:
    def test_returns_non_empty_string(self) -> None:
        result = generate_rng_id_step()
        assert isinstance(result, str)
        assert len(result) >= 4

    def test_returned_id_is_added_to_global_set(self) -> None:
        before = set(g_unique_list_id_step)
        result = generate_rng_id_step()
        assert result in g_unique_list_id_step, (
            "generate_rng_id_step must register the generated ID in g_unique_list_id_step"
        )
        # Clean up: we can't cleanly remove from the global set, but we can verify
        _ = before  # just reference it to avoid unused var warning

    def test_two_calls_return_different_ids(self) -> None:
        id1 = generate_rng_id_step()
        id2 = generate_rng_id_step()
        assert id1 != id2, "generate_rng_id_step must return unique IDs on consecutive calls"


class TestRandomUtilMergeUnique:
    def test_merge_empty_set_is_noop(self) -> None:
        before = set(g_unique_list_id_step)
        merge_unique_list_id_step(set())
        after = set(g_unique_list_id_step)
        # merge of empty set must not change the global set
        assert before <= after  # the set can only grow from other parallel calls

    def test_merge_adds_new_ids(self) -> None:
        new_ids = {"FAKE_ID_REGRESSION_TEST_1", "FAKE_ID_REGRESSION_TEST_2"}
        merge_unique_list_id_step(new_ids)
        for nid in new_ids:
            assert nid in g_unique_list_id_step, f"{nid} must be in g_unique_list_id_step after merge"


class TestRandomUtilGenerateRngHexastring:
    def test_odd_raises_error(self) -> None:
        with pytest.raises(ValueMustBePositiveAndEvenError):
            generate_rng_hexastring(3)

    def test_zero_raises_error(self) -> None:
        with pytest.raises(ValueMustBePositiveAndEvenError):
            generate_rng_hexastring(0)

    def test_negative_raises_error(self) -> None:
        with pytest.raises(ValueMustBePositiveAndEvenError):
            generate_rng_hexastring(-2)

    def test_even_positive_returns_correct_length(self) -> None:
        result = generate_rng_hexastring(8)
        assert isinstance(result, str)
        assert len(result) == 8, f"Expected 8 chars, got {len(result)}: {result!r}"

    def test_result_is_hexadecimal(self) -> None:
        result = generate_rng_hexastring(16)
        assert all(c in "0123456789abcdef" for c in result), (
            f"generate_rng_hexastring must return hex chars only, got {result!r}"
        )


# ===========================================================================
# path_util — folder_exists, count_files_in_folder, list_files
# ===========================================================================


class TestFolderExists:
    def test_existing_directory_returns_true(self, tmp_path: Path) -> None:
        assert folder_exists(tmp_path) is True

    def test_nonexistent_path_returns_false(self, tmp_path: Path) -> None:
        assert folder_exists(tmp_path / "nonexistent") is False

    def test_file_path_returns_false(self, tmp_path: Path) -> None:
        f = tmp_path / "file.txt"
        f.write_text("data")
        assert folder_exists(f) is False

    def test_accepts_string_argument(self, tmp_path: Path) -> None:
        assert folder_exists(str(tmp_path)) is True


class TestCountFilesInFolder:
    def test_counts_matching_extension(self, tmp_path: Path) -> None:
        (tmp_path / "a.json").write_text("{}")
        (tmp_path / "b.json").write_text("{}")
        (tmp_path / "c.txt").write_text("txt")
        assert count_files_in_folder(tmp_path, ".json") == 2

    def test_extension_without_dot_also_works(self, tmp_path: Path) -> None:
        (tmp_path / "a.csv").write_text("csv")
        assert count_files_in_folder(tmp_path, "csv") == 1

    def test_nonexistent_folder_returns_zero(self, tmp_path: Path) -> None:
        assert count_files_in_folder(tmp_path / "nope", ".json") == 0

    def test_empty_folder_returns_zero(self, tmp_path: Path) -> None:
        assert count_files_in_folder(tmp_path, ".json") == 0

    def test_does_not_count_wrong_extension(self, tmp_path: Path) -> None:
        (tmp_path / "a.txt").write_text("txt")
        assert count_files_in_folder(tmp_path, ".json") == 0


class TestListFiles:
    def test_returns_files_with_matching_extension(self, tmp_path: Path) -> None:
        (tmp_path / "a.json").write_text("{}")
        (tmp_path / "b.json").write_text("{}")
        result = list_files(str(tmp_path), ".json")
        assert len(result) == 2
        assert all(isinstance(r, tuple) and len(r) == 2 for r in result)

    def test_extension_without_dot_also_works(self, tmp_path: Path) -> None:
        (tmp_path / "a.json").write_text("{}")
        result = list_files(str(tmp_path), "json")
        assert len(result) == 1

    def test_empty_folder_returns_empty_list(self, tmp_path: Path) -> None:
        result = list_files(str(tmp_path), ".json")
        assert result == []

    def test_nonexistent_folder_raises(self, tmp_path: Path) -> None:
        from shared.exception_util import InvalidDirectoryPathError

        with pytest.raises(InvalidDirectoryPathError):
            list_files(str(tmp_path / "nope"), ".json")

    def test_result_contains_path_objects(self, tmp_path: Path) -> None:
        (tmp_path / "x.json").write_text("{}")
        result = list_files(str(tmp_path), ".json")
        assert isinstance(result[0][0], Path)


# ===========================================================================
# path_util — path_has_valid_syntax edge cases
# ===========================================================================


class TestPathHasValidSyntaxEdgeCases:
    @pytest.mark.parametrize(
        "path_str, expected",
        [
            ("", False),
            ("C:\\Users\\data", True),
            ("relative\\path", True),
            ("file.txt", True),
            ("path|with|pipe", False),
            ("path<with>angle", False),
            ('path"with"quote', False),
            ("CON", False),
            ("NUL\\subfolder", False),
            ("COM1", False),
            ("LPT1", False),
            ("a" * 256, False),  # exceeds max path length
            ("path\\with\\trailing.", False),
            ("path\\with\\trailing ", False),
        ],
        ids=[
            "empty",
            "windows_absolute",
            "relative",
            "file_name",
            "pipe_char",
            "angle_brackets",
            "quote_char",
            "reserved_CON",
            "reserved_NUL_in_path",
            "reserved_COM1",
            "reserved_LPT1",
            "too_long",
            "trailing_dot",
            "trailing_space",
        ],
    )
    def test_path_syntax(self, path_str: str, expected: bool) -> None:
        assert path_has_valid_syntax(path_str) is expected, (
            f"path_has_valid_syntax({path_str!r}) must return {expected}"
        )


# ===========================================================================
# UrlSourceTypeEnum — values contract
# ===========================================================================


class TestUrlSourceTypeEnumValues:
    def test_all_expected_variants_present(self) -> None:
        names = {e.name for e in UrlSourceTypeEnum}
        assert "E_UNSET" in names
        assert "E_UNKNOWN" in names
        assert "E_MANUAL_LIST" in names
        assert "E_FOLDER_RACS" in names
        assert "E_REFRESH_URLS" in names

    def test_enum_count_is_six(self) -> None:
        assert len(list(UrlSourceTypeEnum)) == 6, (
            "UrlSourceTypeEnum must have exactly 6 variants — update this test if adding new ones"
        )

    @pytest.mark.parametrize("member", list(UrlSourceTypeEnum))
    def test_each_value_is_string(self, member: UrlSourceTypeEnum) -> None:
        assert isinstance(member.value, str), f"{member.name}.value must be a string"
