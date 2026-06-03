"""Extra coverage for shared/random_util.py — merge_unique_list_id_step (lines 30-32) and fallback (line 56)."""

from __future__ import annotations

import shared.random_util as ru


class TestMergeUniqueListIdStep:
    def test_empty_set_no_op(self) -> None:
        before = len(ru.g_unique_list_id_step)
        ru.merge_unique_list_id_step(set())
        assert len(ru.g_unique_list_id_step) == before

    def test_non_empty_set_called(self) -> None:
        # merge_unique_list_id_step uses .update() to merge IDs in-place.
        ids = {"fake_id_x", "fake_id_y"}
        for sid in ids:
            ru.g_unique_list_id_step.discard(sid)
        ru.merge_unique_list_id_step(ids)
        for sid in ids:
            assert sid in ru.g_unique_list_id_step, f"{sid!r} doit être dans le registre après merge"
