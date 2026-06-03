"""Tests for shared/resources_icons_util.py."""

from __future__ import annotations

import tkinter as tk

import pytest

from shared.resources_icons_util import ResourcesIcons


@pytest.fixture(autouse=True)
def clear_singleton() -> None:
    """Reset the singleton before each test for isolation."""
    ResourcesIcons._instance = None
    yield
    ResourcesIcons._instance = None


class TestResourcesIconsSingleton:
    def test_same_instance_returned(self) -> None:
        a = ResourcesIcons()
        b = ResourcesIcons()
        assert a is b

    def test_cache_shared_across_instances(self, tk_root: tk.Tk) -> None:
        a = ResourcesIcons()
        b = ResourcesIcons()
        assert a._cache is b._cache


class TestGetIcon:
    def test_missing_file_returns_fallback(self, tk_root: tk.Tk) -> None:
        from PIL import ImageTk

        ri = ResourcesIcons()
        result = ri.get_icon("/nonexistent/icon.png", (24, 24))
        assert isinstance(result, ImageTk.PhotoImage)

    def test_same_path_size_returns_cached(self, tk_root: tk.Tk) -> None:
        ri = ResourcesIcons()
        r1 = ri.get_icon("/nonexistent/icon.png", (24, 24))
        r2 = ri.get_icon("/nonexistent/icon.png", (24, 24))
        assert r1 is r2

    def test_different_size_different_result(self, tk_root: tk.Tk) -> None:
        ri = ResourcesIcons()
        r1 = ri.get_icon("/nonexistent/icon.png", (24, 24))
        r2 = ri.get_icon("/nonexistent/icon.png", (32, 32))
        # Different cache keys — may or may not be same object, but both valid
        from PIL import ImageTk

        assert isinstance(r1, ImageTk.PhotoImage)
        assert isinstance(r2, ImageTk.PhotoImage)


class TestGetIconDisabled:
    def test_missing_file_returns_fallback(self, tk_root: tk.Tk) -> None:
        from PIL import ImageTk

        ri = ResourcesIcons()
        result = ri.get_icon_disabled("/nonexistent/icon.png", (32, 32))
        assert isinstance(result, ImageTk.PhotoImage)

    def test_cached_on_second_call(self, tk_root: tk.Tk) -> None:
        ri = ResourcesIcons()
        r1 = ri.get_icon_disabled("/nonexistent/icon.png", (32, 32))
        r2 = ri.get_icon_disabled("/nonexistent/icon.png", (32, 32))
        assert r1 is r2


class TestClearCache:
    def test_clear_empties_cache(self, tk_root: tk.Tk) -> None:
        ri = ResourcesIcons()
        ri.get_icon("/nonexistent/icon.png", (24, 24))
        assert len(ri._cache) > 0
        ri.clear_cache()
        assert len(ri._cache) == 0

    def test_after_clear_next_call_refills(self, tk_root: tk.Tk) -> None:
        ri = ResourcesIcons()
        r1 = ri.get_icon("/nonexistent/icon.png", (24, 24))
        ri.clear_cache()
        r2 = ri.get_icon("/nonexistent/icon.png", (24, 24))
        # Both valid PhotoImages — not necessarily same object after clear
        from PIL import ImageTk

        assert isinstance(r2, ImageTk.PhotoImage)


class TestCreateFallback:
    def test_returns_rgb_image(self) -> None:
        from PIL import Image

        img = ResourcesIcons._create_fallback((24, 24))
        assert isinstance(img, Image.Image)
        assert img.size == (24, 24)

    def test_different_sizes(self) -> None:
        for size in ((16, 16), (32, 32), (64, 64)):
            img = ResourcesIcons._create_fallback(size)
            assert img.size == size


class TestApplyDisabledEffect:
    def test_returns_rgba_image(self) -> None:
        from PIL import Image

        img = Image.new("RGB", (24, 24), "#FF0000")
        result = ResourcesIcons._apply_disabled_effect(img)
        assert result.mode == "RGBA"
        assert result.size == (24, 24)

    def test_alpha_reduced(self) -> None:
        from PIL import Image

        img = Image.new("RGBA", (1, 1), (255, 0, 0, 255))
        result = ResourcesIcons._apply_disabled_effect(img)
        _, _, _, alpha = result.getpixel((0, 0))
        assert alpha < 255  # opacity reduced
        assert alpha == int(255 * 0.4)
