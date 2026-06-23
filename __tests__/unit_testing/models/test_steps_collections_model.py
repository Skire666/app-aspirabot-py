"""Tests for models/steps_collections_model.py."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from models.step_scraping_model import StepScrapingModel
from models.steps_collections_model import StepsCollections
from shared.enums import StepTypeEnum


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_step(step_type: StepTypeEnum = StepTypeEnum.E_SCROLL_DOWN, step_id: str = "s1") -> StepScrapingModel:
    step = MagicMock(spec=StepScrapingModel)
    step.step_type = step_type
    step.step_id = step_id
    step.params = None
    return step


def _make_steps(*pairs: tuple[StepTypeEnum, str]) -> list[StepScrapingModel]:
    return [_make_step(t, sid) for t, sid in pairs]


def _minimal_valid() -> list[StepScrapingModel]:
    """Minimal structurally valid workflow: OPEN_URL → KILL_BROWSER."""
    return [
        _make_step(StepTypeEnum.E_OPEN_URL, "open"),
        _make_step(StepTypeEnum.E_KILL_BROWSER, "kill"),
    ]


# ---------------------------------------------------------------------------
# Collection protocol
# ---------------------------------------------------------------------------


class TestCollectionProtocol:
    def test_len_empty(self) -> None:
        sc = StepsCollections([])
        assert len(sc) == 0

    def test_len_nonempty(self) -> None:
        sc = StepsCollections(_minimal_valid())
        assert len(sc) == 2

    def test_iter(self) -> None:
        steps = _minimal_valid()
        sc = StepsCollections(steps)
        assert list(sc) == steps

    def test_getitem(self) -> None:
        steps = _minimal_valid()
        sc = StepsCollections(steps)
        assert sc[0] is steps[0]
        assert sc[1] is steps[1]

    def test_setitem_replaces_and_updates_cache(self) -> None:
        sc = StepsCollections(_minimal_valid())
        new_step = _make_step(StepTypeEnum.E_SCROLL_DOWN, "new")
        sc[0] = new_step
        assert sc[0] is new_step
        assert sc.count_type_step(StepTypeEnum.E_SCROLL_DOWN) == 1

    def test_eq_with_steps_collections(self) -> None:
        steps = _minimal_valid()
        sc1 = StepsCollections(steps)
        sc2 = StepsCollections(steps)
        assert sc1 == sc2

    def test_eq_with_list(self) -> None:
        steps = _minimal_valid()
        sc = StepsCollections(steps)
        assert sc == steps

    def test_eq_not_equal(self) -> None:
        sc1 = StepsCollections(_minimal_valid())
        sc2 = StepsCollections([_make_step()])
        assert sc1 != sc2

    def test_eq_not_implemented_for_other_types(self) -> None:
        sc = StepsCollections([])
        assert sc.__eq__(42) is NotImplemented


# ---------------------------------------------------------------------------
# CRUD mutations
# ---------------------------------------------------------------------------


class TestCrud:
    def test_append_adds_to_end(self) -> None:
        sc = StepsCollections([])
        step = _make_step(StepTypeEnum.E_SCROLL_DOWN, "x")
        sc.append(step)
        assert sc[0] is step
        assert len(sc) == 1

    def test_append_updates_type_cache(self) -> None:
        sc = StepsCollections([])
        sc.append(_make_step(StepTypeEnum.E_OPEN_URL, "o"))
        assert sc.count_type_step(StepTypeEnum.E_OPEN_URL) == 1

    def test_insert_after_correct_position(self) -> None:
        steps = _minimal_valid()
        sc = StepsCollections(steps)
        new = _make_step(StepTypeEnum.E_SCROLL_DOWN, "mid")
        sc.insert_after(0, new)
        assert sc[1] is new
        assert len(sc) == 3

    def test_insert_after_updates_cache(self) -> None:
        sc = StepsCollections(_minimal_valid())
        sc.insert_after(0, _make_step(StepTypeEnum.E_SCROLL_DOWN, "s"))
        assert sc.count_type_step(StepTypeEnum.E_SCROLL_DOWN) == 1

    def test_delete_at_removes_step(self) -> None:
        sc = StepsCollections(_minimal_valid())
        sc.delete_at(0)
        assert len(sc) == 1
        assert sc.count_type_step(StepTypeEnum.E_OPEN_URL) == 0

    def test_swap_exchanges_steps(self) -> None:
        steps = _minimal_valid()
        sc = StepsCollections(steps)
        a, b = sc[0], sc[1]
        sc.swap(0, 1)
        assert sc[0] is b
        assert sc[1] is a

    def test_clear_empties_list_and_cache(self) -> None:
        sc = StepsCollections(_minimal_valid())
        sc.clear()
        assert len(sc) == 0
        assert sc.count_type_step(StepTypeEnum.E_OPEN_URL) == 0

    def test_load_replaces_content(self) -> None:
        sc = StepsCollections(_minimal_valid())
        new_steps = [_make_step(StepTypeEnum.E_SCROLL_DOWN, "s")]
        sc.load(new_steps)
        assert len(sc) == 1
        assert sc.count_type_step(StepTypeEnum.E_SCROLL_DOWN) == 1
        assert sc.count_type_step(StepTypeEnum.E_OPEN_URL) == 0

    def test_reset_clears_list(self) -> None:
        sc = StepsCollections(_minimal_valid())
        sc.reset()
        assert len(sc) == 0
        assert sc.count_type_step(StepTypeEnum.E_OPEN_URL) == 0

    def test_reorder_by_ids(self) -> None:
        steps = _minimal_valid()
        sc = StepsCollections(steps)
        sc.reorder_by_ids(["kill", "open"])
        assert sc[0].step_id == "kill"
        assert sc[1].step_id == "open"

    def test_reorder_by_ids_ignores_unknown(self) -> None:
        sc = StepsCollections(_minimal_valid())
        sc.reorder_by_ids(["kill", "nonexistent", "open"])
        assert len(sc) == 2


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------


class TestQueryHelpers:
    def test_as_list_returns_copy(self) -> None:
        sc = StepsCollections(_minimal_valid())
        copy = sc.as_list()
        copy.clear()
        assert len(sc) == 2

    def test_find_index_by_id_found(self) -> None:
        sc = StepsCollections(_minimal_valid())
        assert sc.find_index_by_id("kill") == 1

    def test_find_index_by_id_not_found(self) -> None:
        sc = StepsCollections(_minimal_valid())
        assert sc.find_index_by_id("nope") is None

    def test_build_context_ids(self) -> None:
        sc = StepsCollections(_minimal_valid())
        ctx = sc.build_context_ids()
        assert ctx == {"open": 0, "kill": 1}

    def test_find_by_id_found(self) -> None:
        steps = _minimal_valid()
        sc = StepsCollections(steps)
        found = sc.find_by_id("open")
        assert found is steps[0]

    def test_find_by_id_not_found(self) -> None:
        sc = StepsCollections(_minimal_valid())
        assert sc.find_by_id("unknown") is None

    def test_count_type_step(self) -> None:
        sc = StepsCollections(_minimal_valid())
        assert sc.count_type_step(StepTypeEnum.E_OPEN_URL) == 1
        assert sc.count_type_step(StepTypeEnum.E_SCROLL_DOWN) == 0

    def test_count_mapping_key_empty_string_returns_zero(self) -> None:
        sc = StepsCollections(_minimal_valid())
        assert sc.count_mapping_key("") == 0

    def test_count_mapping_key_whitespace_returns_zero(self) -> None:
        sc = StepsCollections(_minimal_valid())
        assert sc.count_mapping_key("   ") == 0

    def test_count_mapping_key_counts_matching_steps(self) -> None:
        extract = _make_step(StepTypeEnum.E_EXTRACT_TEXTS, "e1")
        extract.params = MagicMock()
        extract.params.mapping = "mykey"
        sc = StepsCollections([extract])
        assert sc.count_mapping_key("mykey") == 1

    def test_count_mapping_key_ignores_non_extract_types(self) -> None:
        scroll = _make_step(StepTypeEnum.E_SCROLL_DOWN, "s")
        scroll.params = MagicMock()
        scroll.params.mapping = "mykey"
        sc = StepsCollections([scroll])
        assert sc.count_mapping_key("mykey") == 0


# ---------------------------------------------------------------------------
# end_is_kill_browser
# ---------------------------------------------------------------------------


class TestEndIsKillBrowser:
    def test_true_when_last_is_kill(self) -> None:
        sc = StepsCollections(_minimal_valid())
        assert sc.end_is_kill_browser() is True

    def test_false_when_last_is_not_kill(self) -> None:
        sc = StepsCollections([_make_step(StepTypeEnum.E_OPEN_URL, "o")])
        assert sc.end_is_kill_browser() is False

    def test_false_when_empty(self) -> None:
        sc = StepsCollections([])
        assert sc.end_is_kill_browser() is False


# ---------------------------------------------------------------------------
# Consecutive jump / restart checks
# ---------------------------------------------------------------------------


class TestConsecutiveChecks:
    def test_no_consecutive_jump_when_less_than_two(self) -> None:
        sc = StepsCollections([_make_step(StepTypeEnum.E_JUMP_TO_STEP, "j")])
        assert sc.has_consecutive_jump_to_step() is False

    def test_no_consecutive_jump_when_separated(self) -> None:
        sc = StepsCollections([
            _make_step(StepTypeEnum.E_JUMP_TO_STEP, "j1"),
            _make_step(StepTypeEnum.E_SCROLL_DOWN, "s"),
            _make_step(StepTypeEnum.E_JUMP_TO_STEP, "j2"),
        ])
        assert sc.has_consecutive_jump_to_step() is False

    def test_consecutive_jump_detected(self) -> None:
        sc = StepsCollections([
            _make_step(StepTypeEnum.E_JUMP_TO_STEP, "j1"),
            _make_step(StepTypeEnum.E_JUMP_TO_STEP, "j2"),
        ])
        assert sc.has_consecutive_jump_to_step() is True

    def test_no_consecutive_restart_when_less_than_two(self) -> None:
        sc = StepsCollections([_make_step(StepTypeEnum.E_RESTART_TO_BEGINNING, "r")])
        assert sc.has_consecutive_restart_to_beginning() is False

    def test_consecutive_restart_detected(self) -> None:
        sc = StepsCollections([
            _make_step(StepTypeEnum.E_RESTART_TO_BEGINNING, "r1"),
            _make_step(StepTypeEnum.E_RESTART_TO_BEGINNING, "r2"),
        ])
        assert sc.has_consecutive_restart_to_beginning() is True

    def test_no_consecutive_restart_when_separated(self) -> None:
        sc = StepsCollections([
            _make_step(StepTypeEnum.E_RESTART_TO_BEGINNING, "r1"),
            _make_step(StepTypeEnum.E_SCROLL_DOWN, "s"),
            _make_step(StepTypeEnum.E_RESTART_TO_BEGINNING, "r2"),
        ])
        assert sc.has_consecutive_restart_to_beginning() is False


# ---------------------------------------------------------------------------
# Duplicate step ID
# ---------------------------------------------------------------------------


class TestDuplicateStepId:
    def test_no_duplicates(self) -> None:
        sc = StepsCollections(_minimal_valid())
        assert sc.had_duplicate_step_id() is False

    def test_duplicate_detected(self) -> None:
        sc = StepsCollections([
            _make_step(StepTypeEnum.E_OPEN_URL, "same"),
            _make_step(StepTypeEnum.E_KILL_BROWSER, "same"),
        ])
        assert sc.had_duplicate_step_id() is True


# ---------------------------------------------------------------------------
# had_open_url_at_the_beginning
# ---------------------------------------------------------------------------


class TestHadOpenUrlAtBeginning:
    def test_true_when_first_is_open_url(self) -> None:
        sc = StepsCollections(_minimal_valid())
        assert sc.had_open_url_at_the_beginning() is True

    def test_false_when_first_is_not_open_url(self) -> None:
        sc = StepsCollections([_make_step(StepTypeEnum.E_SCROLL_DOWN, "s")])
        assert sc.had_open_url_at_the_beginning() is False

    def test_false_when_empty(self) -> None:
        sc = StepsCollections([])
        assert sc.had_open_url_at_the_beginning() is False

    def test_true_when_section_then_open_url(self) -> None:
        sc = StepsCollections([
            _make_step(StepTypeEnum.E_SECTION_STEPS, "sec"),
            _make_step(StepTypeEnum.E_OPEN_URL, "open"),
            _make_step(StepTypeEnum.E_KILL_BROWSER, "kill"),
        ])
        assert sc.had_open_url_at_the_beginning() is True


# ---------------------------------------------------------------------------
# had_restart_to_beginning_after_open_url
# ---------------------------------------------------------------------------


class TestHadRestartAfterOpenUrl:
    def test_true_when_no_restart_steps(self) -> None:
        sc = StepsCollections(_minimal_valid())
        assert sc.had_restart_to_beginning_after_open_url() is True

    def test_true_when_restart_after_open_url(self) -> None:
        sc = StepsCollections([
            _make_step(StepTypeEnum.E_OPEN_URL, "open"),
            _make_step(StepTypeEnum.E_RESTART_TO_BEGINNING, "r"),
            _make_step(StepTypeEnum.E_KILL_BROWSER, "kill"),
        ])
        assert sc.had_restart_to_beginning_after_open_url() is True

    def test_false_when_restart_before_open_url(self) -> None:
        sc = StepsCollections([
            _make_step(StepTypeEnum.E_RESTART_TO_BEGINNING, "r"),
            _make_step(StepTypeEnum.E_OPEN_URL, "open"),
        ])
        assert sc.had_restart_to_beginning_after_open_url() is False


# ---------------------------------------------------------------------------
# has_export_step_when_extract_step
# ---------------------------------------------------------------------------


class TestExportWhenExtract:
    def test_true_when_neither_extract_nor_export(self) -> None:
        sc = StepsCollections(_minimal_valid())
        assert sc.has_export_step_when_extract_step() is True

    def test_false_when_extract_without_export(self) -> None:
        sc = StepsCollections([
            _make_step(StepTypeEnum.E_OPEN_URL, "open"),
            _make_step(StepTypeEnum.E_EXTRACT_TEXTS, "ext"),
            _make_step(StepTypeEnum.E_KILL_BROWSER, "kill"),
        ])
        assert sc.has_export_step_when_extract_step() is False

    def test_true_when_extract_and_export(self) -> None:
        sc = StepsCollections([
            _make_step(StepTypeEnum.E_OPEN_URL, "open"),
            _make_step(StepTypeEnum.E_EXTRACT_TEXTS, "ext"),
            _make_step(StepTypeEnum.E_EXPORT_DATA_TO_JS, "exp"),
            _make_step(StepTypeEnum.E_KILL_BROWSER, "kill"),
        ])
        assert sc.has_export_step_when_extract_step() is True

    def test_false_when_export_without_extract(self) -> None:
        sc = StepsCollections([
            _make_step(StepTypeEnum.E_OPEN_URL, "open"),
            _make_step(StepTypeEnum.E_EXPORT_DATA_TO_JS, "exp"),
            _make_step(StepTypeEnum.E_KILL_BROWSER, "kill"),
        ])
        assert sc.has_export_step_when_extract_step() is False


# ---------------------------------------------------------------------------
# Cache management
# ---------------------------------------------------------------------------


class TestCacheManagement:
    def test_remove_from_cache_removes_last_of_type(self) -> None:
        sc = StepsCollections(_minimal_valid())
        sc.delete_at(0)
        assert sc.count_type_step(StepTypeEnum.E_OPEN_URL) == 0

    def test_remove_from_cache_keeps_other_types(self) -> None:
        sc = StepsCollections(_minimal_valid())
        sc.delete_at(0)
        assert sc.count_type_step(StepTypeEnum.E_KILL_BROWSER) == 1

    def test_add_multiple_of_same_type_counts_correctly(self) -> None:
        sc = StepsCollections([])
        sc.append(_make_step(StepTypeEnum.E_SCROLL_DOWN, "a"))
        sc.append(_make_step(StepTypeEnum.E_SCROLL_DOWN, "b"))
        assert sc.count_type_step(StepTypeEnum.E_SCROLL_DOWN) == 2
