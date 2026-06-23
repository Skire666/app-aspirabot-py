"""Regression tests — models/extracted_data_model.py.

Freezes the dict-like public API of ExtractedData:
  - is_empty() contract (empty vs non-empty)
  - get() with missing key returns default
  - __iter__() yields keys in insertion order
  - Overwriting an existing key replaces the item
  - keys(), values(), items() are consistent with each other
  - to_dict() structure contract
"""

from __future__ import annotations

import pytest

from models.extracted_data_model import ExtractedData, ExtractedItem


# ---------------------------------------------------------------------------
# is_empty
# ---------------------------------------------------------------------------


class TestIsEmpty:
    def test_empty_on_init(self) -> None:
        ed = ExtractedData()
        assert ed.is_empty() is True, "ExtractedData must be empty immediately after construction"

    def test_not_empty_after_append(self) -> None:
        ed = ExtractedData()
        ed.append_item("k", ".sel", ["v"], "")
        assert ed.is_empty() is False, "ExtractedData must not be empty after appending an item"

    def test_not_empty_after_multiple_appends(self) -> None:
        ed = ExtractedData()
        ed.append_item("k1", "s1", ["a"], "")
        ed.append_item("k2", "s2", ["b"], "")
        assert ed.is_empty() is False


# ---------------------------------------------------------------------------
# get() — missing / present keys
# ---------------------------------------------------------------------------


class TestGet:
    def test_get_missing_key_returns_default_none(self) -> None:
        ed = ExtractedData()
        result = ed.get("missing")
        assert result is None, "get() must return None for an absent key by default"

    def test_get_missing_key_with_explicit_default(self) -> None:
        ed = ExtractedData()
        sentinel = ExtractedItem(input="x", values=[], comment="")
        result = ed.get("missing", sentinel)
        assert result is sentinel

    def test_get_existing_key_returns_item(self) -> None:
        ed = ExtractedData()
        ed.append_item("title", ".h1", ["Hello"], "a note")
        item = ed.get("title")
        assert item is not None
        assert item.values == ["Hello"]
        assert item.input == ".h1"
        assert item.comment == "a note"


# ---------------------------------------------------------------------------
# __iter__ — insertion order preserved
# ---------------------------------------------------------------------------


class TestIter:
    def test_iter_empty(self) -> None:
        ed = ExtractedData()
        assert list(ed) == [], "__iter__ on empty ExtractedData must yield nothing"

    def test_iter_yields_keys_in_insertion_order(self) -> None:
        ed = ExtractedData()
        ed.append_item("first", "s1", [], "")
        ed.append_item("second", "s2", [], "")
        ed.append_item("third", "s3", [], "")
        assert list(ed) == ["first", "second", "third"], (
            "__iter__ must yield keys in insertion order"
        )


# ---------------------------------------------------------------------------
# Overwrite behaviour
# ---------------------------------------------------------------------------


class TestOverwrite:
    def test_overwrite_existing_key_replaces_item(self) -> None:
        ed = ExtractedData()
        ed.append_item("price", ".old-sel", ["$50"], "old comment")
        ed.append_item("price", ".new-sel", ["$99"], "new comment")
        assert len(list(ed.keys())) == 1, "overwriting must not add a second entry"
        item = ed["price"]
        assert item.input == ".new-sel", "overwrite must replace the input selector"
        assert item.values == ["$99"], "overwrite must replace the values"

    def test_overwrite_preserves_order_at_original_position(self) -> None:
        ed = ExtractedData()
        ed.append_item("a", "s", [], "")
        ed.append_item("b", "s", [], "")
        ed.append_item("a", "s2", ["new"], "")
        # dict.__setitem__ replaces in-place in CPython 3.7+, preserving order
        keys = list(ed)
        assert keys[0] == "a"
        assert keys[1] == "b"


# ---------------------------------------------------------------------------
# keys() / values() / items() — consistent views
# ---------------------------------------------------------------------------


class TestViews:
    def test_keys_values_items_consistent(self) -> None:
        ed = ExtractedData()
        ed.append_item("x", "sx", ["vx"], "cx")
        ed.append_item("y", "sy", ["vy"], "cy")

        keys = list(ed.keys())
        values = list(ed.values())
        items = list(ed.items())

        assert keys == ["x", "y"]
        assert len(values) == 2
        assert values[0].input == "sx"
        assert values[1].input == "sy"
        assert items[0] == ("x", ed["x"])
        assert items[1] == ("y", ed["y"])


# ---------------------------------------------------------------------------
# to_dict — structure contract
# ---------------------------------------------------------------------------


class TestToDict:
    def test_to_dict_preserves_all_fields(self) -> None:
        ed = ExtractedData()
        ed.append_item("link", "a.nav", ["http://a.com", "http://b.com"], "nav links")
        d = ed.to_dict()
        assert "link" in d
        entry = d["link"]
        assert entry["input"] == "a.nav"
        assert entry["values"] == ["http://a.com", "http://b.com"]
        assert entry["comment"] == "nav links"

    def test_to_dict_multiple_keys(self) -> None:
        ed = ExtractedData()
        ed.append_item("k1", "s1", ["v1"], "c1")
        ed.append_item("k2", "s2", ["v2"], "c2")
        d = ed.to_dict()
        assert set(d.keys()) == {"k1", "k2"}

    def test_to_dict_empty_values_list(self) -> None:
        ed = ExtractedData()
        ed.append_item("empty", ".none", [], "")
        d = ed.to_dict()
        assert d["empty"]["values"] == []


# ---------------------------------------------------------------------------
# __contains__ contract
# ---------------------------------------------------------------------------


class TestContains:
    def test_contains_present_key(self) -> None:
        ed = ExtractedData()
        ed.append_item("mykey", "s", ["v"], "")
        assert "mykey" in ed

    def test_contains_absent_key(self) -> None:
        ed = ExtractedData()
        assert "mykey" not in ed

    def test_getitem_raises_key_error_for_missing(self) -> None:
        ed = ExtractedData()
        with pytest.raises(KeyError):
            _ = ed["missing_key"]
