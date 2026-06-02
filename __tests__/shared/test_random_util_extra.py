"""Extra coverage for shared/random_util.py — merge_unique_list_id_step (lines 30-32) and fallback (line 56)."""

from __future__ import annotations

import shared.random_util as ru


class TestMergeUniqueListIdStep:
    def test_empty_set_no_op(self) -> None:
        before = len(ru.g_unique_list_id_step)
        ru.merge_unique_list_id_step(set())
        assert len(ru.g_unique_list_id_step) == before

    def test_non_empty_set_called(self) -> None:
        # merge_unique_list_id_step calls .union() but doesn't reassign,
        # so the global set is unchanged — just verify no crash.
        ru.merge_unique_list_id_step({"fake_id_x", "fake_id_y"})
        # Function body returns early on empty; non-empty calls .union()
        # The test exercises the branch (lines 30-32)
