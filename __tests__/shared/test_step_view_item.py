"""Tests for shared/step_view_item.py."""

from __future__ import annotations

from datetime import datetime

import pytest

from shared.enums import StepTypeEnum
from shared.step_view_item import StepViewItem


def _make_item(**kwargs: object) -> StepViewItem:
    defaults: dict[str, object] = {
        "step_id": "abc1",
        "step_type": StepTypeEnum.E_OPEN_URL,
        "is_active": True,
        "modified_date": datetime(2024, 1, 1),
        "params_dict": {},
        "label": "01 — Open URL",
    }
    defaults.update(kwargs)
    return StepViewItem(**defaults)  # type: ignore[arg-type]


class TestStepViewItemConstruction:
    def test_basic_construction(self) -> None:
        item = _make_item()
        assert item.step_id == "abc1"
        assert item.step_type is StepTypeEnum.E_OPEN_URL
        assert item.is_active is True

    def test_params_dict_stored(self) -> None:
        params = {"url_mode": "<<SOURCE>>", "timeout_duration": 30}
        item = _make_item(params_dict=params)
        assert item.params_dict == params

    def test_label_stored(self) -> None:
        item = _make_item(label="02 — Click")
        assert item.label == "02 — Click"

    def test_modified_date_stored(self) -> None:
        dt = datetime(2024, 6, 15, 12, 0, 0)
        item = _make_item(modified_date=dt)
        assert item.modified_date == dt


class TestStepViewItemImmutability:
    def test_frozen_rejects_attribute_set(self) -> None:
        item = _make_item()
        with pytest.raises((AttributeError, TypeError)):
            item.step_id = "new_id"  # type: ignore[misc]

    def test_frozen_rejects_is_active_set(self) -> None:
        item = _make_item()
        with pytest.raises((AttributeError, TypeError)):
            item.is_active = False  # type: ignore[misc]


class TestStepViewItemEquality:
    def test_equal_items(self) -> None:
        dt = datetime(2024, 1, 1)
        a = _make_item(step_id="x1", modified_date=dt)
        b = _make_item(step_id="x1", modified_date=dt)
        assert a == b

    def test_different_step_id(self) -> None:
        dt = datetime(2024, 1, 1)
        a = _make_item(step_id="x1", modified_date=dt)
        b = _make_item(step_id="x2", modified_date=dt)
        assert a != b

    def test_different_step_type(self) -> None:
        a = _make_item(step_type=StepTypeEnum.E_OPEN_URL)
        b = _make_item(step_type=StepTypeEnum.E_CLICK_ON_ELEMENT)
        assert a != b
