"""Tests for shared/enums.py."""

from __future__ import annotations

from shared.enums import ExtractTargetEnum, ExtractTextHtmlEnum, StepTypeEnum, TitleModuleEnum, UrlSourceTypeEnum


class TestTitleModuleEnum:
    def test_all_members_have_string_values(self) -> None:
        for member in TitleModuleEnum:
            assert isinstance(member.value, str)
            assert member.value

    def test_known_values(self) -> None:
        assert TitleModuleEnum.E_LOGS.value == "LOGS"
        assert TitleModuleEnum.E_SCENARIOS.value == "SCENARIOS"
        assert TitleModuleEnum.E_WORKFLOW.value == "WORKFLOW"
        assert TitleModuleEnum.E_DEBUG.value == "DEBUG"

    def test_member_count(self) -> None:
        assert len(TitleModuleEnum) == 9


class TestStepTypeEnum:
    def test_unset_member_exists(self) -> None:
        assert StepTypeEnum.E_UNSET.value == "UNSET"

    def test_unknown_member_exists(self) -> None:
        assert StepTypeEnum.E_UNKNOWN.value == "UNKNOWN"

    def test_lookup_by_value(self) -> None:
        assert StepTypeEnum("OPEN_URL") is StepTypeEnum.E_OPEN_URL
        assert StepTypeEnum("CLICK_ON_ELEMENT") is StepTypeEnum.E_CLICK_ON_ELEMENT

    def test_invalid_value_raises(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            StepTypeEnum("NOT_A_REAL_STEP")

    def test_expected_step_types_present(self) -> None:
        expected = {
            "E_OPEN_URL",
            "E_CLOSE_TABS",
            "E_WAIT_FIXED_TIME",
            "E_CLICK_ON_ELEMENT",
            "E_EXTRACT_TEXTS",
            "E_EXTRACT_LINKS",
            "E_JUMP_TO_STEP",
            "E_SECTION_STEPS",
            "E_KILL_BROWSER",
        }
        member_names = {m.name for m in StepTypeEnum}
        assert expected.issubset(member_names)


class TestExtractEnums:
    def test_extract_text_html_inner_text(self) -> None:
        assert ExtractTextHtmlEnum.E_INNER_TEXT.value == "innerText"

    def test_extract_target_all(self) -> None:
        assert ExtractTargetEnum.E_ALL.value == "all"

    def test_extract_target_first(self) -> None:
        assert ExtractTargetEnum.E_FIRST.value == "first"


class TestUrlSourceTypeEnum:
    def test_manual_value(self) -> None:
        assert UrlSourceTypeEnum.E_MANUAL_LIST.value == "MANUAL_LIST"

    def test_folder_value(self) -> None:
        assert UrlSourceTypeEnum.E_FOLDER_RACS.value == "FOLDER_RACS"

    def test_json_value(self) -> None:
        assert UrlSourceTypeEnum.E_FOLDER_JSONS.value == "FOLDER_JSONS"
