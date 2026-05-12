"""Tests for download image step logic (previously in ScrapingService)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from interfaces.i_web_browser_service import IWebBrowserService
from services.steps.download_image_executor import DownloadImageExecutor, _select_by_mode

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class _FakeResponse:
    def __init__(self, ok: bool, body: bytes = b"data", status: int = 200) -> None:
        self.ok = ok
        self._body = body
        self.status = status

    def body(self) -> bytes:
        return self._body


class _FakeRequest:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get(self, url: str, headers: dict[str, str]) -> _FakeResponse:
        self.calls.append(url)
        return _FakeResponse(True, body=url.encode("utf-8"))


class _FakeContext:
    def __init__(self) -> None:
        self.request = _FakeRequest()


class _FakePage:
    def __init__(self, url: str) -> None:
        self.url = url
        self.context = _FakeContext()

    def evaluate(self, script: str) -> str:
        return "Fake UA"

    def evaluate_handle(self, script: str) -> Any:
        return None


def _make_browser(page: _FakePage) -> IWebBrowserService:
    """Build a minimal mock browser service returning the given fake page."""
    browser = MagicMock(spec=IWebBrowserService)
    browser.get_current_page.return_value = page
    return browser


# ---------------------------------------------------------------------------
# Tests for _select_by_mode (module-level helper, now in executor module)
# ---------------------------------------------------------------------------


def test_select_by_mode_first() -> None:
    images = [
        {"src": "a.jpg", "width": 10, "height": 10},
        {"src": "b.jpg", "width": 20, "height": 5},
        {"src": "c.jpg", "width": 20, "height": 10},
    ]
    assert _select_by_mode(images, "first") == [images[0]]


def test_select_by_mode_last() -> None:
    images = [
        {"src": "a.jpg", "width": 10, "height": 10},
        {"src": "b.jpg", "width": 20, "height": 5},
        {"src": "c.jpg", "width": 20, "height": 10},
    ]
    assert _select_by_mode(images, "last") == [images[-1]]


def test_select_by_mode_all() -> None:
    images = [
        {"src": "a.jpg", "width": 10, "height": 10},
        {"src": "b.jpg", "width": 20, "height": 5},
        {"src": "c.jpg", "width": 20, "height": 10},
    ]
    assert _select_by_mode(images, "all") == images


# ---------------------------------------------------------------------------
# Tests for execute_logical (integration via executor + mock browser)
# ---------------------------------------------------------------------------


def _make_params(
    tmp_path: Path,
    *,
    mode: str = "all",
    unique_only: bool = True,
    w_min: int = 0,
    w_max: int = 9999,
    h_min: int = 0,
    h_max: int = 9999,
) -> dict[str, Any]:
    return {
        "mode": mode,
        "unique_only": unique_only,
        "width_min": w_min,
        "width_max": w_max,
        "height_min": h_min,
        "height_max": h_max,
        "_folder": tmp_path,
        "_downloaded_urls": set(),
    }


def _fake_page_with_images(base_url: str, srcs: list[str]) -> _FakePage:
    """Return a FakePage whose evaluate() returns image metadata for given srcs."""
    page = _FakePage(base_url)
    img_data = [{"src": s, "width": 100, "height": 100} for s in srcs]
    page.evaluate = lambda _script: img_data
    return page


def test_execute_logical_skips_duplicates_when_unique_only(tmp_path: Path) -> None:
    srcs = ["/img/a.png", "/img/a.png", "/img/b.png"]
    page = _fake_page_with_images("https://example.com/page", srcs)
    images = [{"src": s, "width": 100, "height": 100} for s in srcs]

    # Mock evaluate_script_with_safe_retry on the browser service directly.
    browser = _make_browser(page)
    browser.evaluate_script_with_safe_retry.return_value = images

    executor = DownloadImageExecutor()
    params = _make_params(tmp_path, mode="all", unique_only=True)
    executor.execute_logical(browser, params)

    # Two unique URLs: a.png and b.png → 2 files saved.
    saved_files = list(tmp_path.iterdir())
    assert len(saved_files) == 2
    assert page.context.request.calls == [
        "https://example.com/img/a.png",
        "https://example.com/img/b.png",
    ]


def test_execute_logical_counts_duplicates_when_not_unique(tmp_path: Path) -> None:
    srcs = ["/img/a.png", "/img/a.png", "/img/b.png"]
    page = _fake_page_with_images("https://example.com/page", srcs)
    images = [{"src": s, "width": 100, "height": 100} for s in srcs]

    # Mock evaluate_script_with_safe_retry on the browser service directly.
    browser = _make_browser(page)
    browser.evaluate_script_with_safe_retry.return_value = images

    executor = DownloadImageExecutor()
    params = _make_params(tmp_path, mode="all", unique_only=False)
    executor.execute_logical(browser, params)

    saved_files = list(tmp_path.iterdir())
    assert len(saved_files) == 3
    assert page.context.request.calls == [
        "https://example.com/img/a.png",
        "https://example.com/img/a.png",
        "https://example.com/img/b.png",
    ]
