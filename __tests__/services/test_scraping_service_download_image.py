from __future__ import annotations

from pathlib import Path

import pytest
from services.scraping_service import ScrapingService


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


def test_select_image_by_mode_returns_lists(tmp_path: Path) -> None:
    service = ScrapingService(tmp_path)
    images = [
        {"src": "a.jpg", "width": 10, "height": 10},
        {"src": "b.jpg", "width": 20, "height": 5},
        {"src": "c.jpg", "width": 20, "height": 10},
    ]

    assert service._select_image_by_mode(images, "first") == [images[0]]
    assert service._select_image_by_mode(images, "last") == [images[-1]]
    assert service._select_image_by_mode(images, "all") == images
    assert service._select_image_by_mode(images, "largest") == [images[2]]


def test_fetch_and_save_image_skips_duplicates_when_unique_only(tmp_path: Path) -> None:
    service = ScrapingService(tmp_path)
    page = _FakePage("https://example.com/page")
    images = [
        {"src": "/img/a.png"},
        {"src": "/img/a.png"},
        {"src": "/img/b.png"},
    ]

    downloaded = service._fetch_and_save_image(page, images, True)

    assert downloaded == 2
    assert page.context.request.calls == [
        "https://example.com/img/a.png",
        "https://example.com/img/b.png",
    ]
    assert len(list(tmp_path.iterdir())) == 2

    with pytest.raises(ValueError, match="No image was downloaded"):
        service._fetch_and_save_image(page, images, True)

    assert page.context.request.calls == [
        "https://example.com/img/a.png",
        "https://example.com/img/b.png",
    ]


def test_fetch_and_save_image_counts_duplicates_when_allowed(tmp_path: Path) -> None:
    service = ScrapingService(tmp_path)
    page = _FakePage("https://example.com/page")
    images = [
        {"src": "/img/a.png"},
        {"src": "/img/a.png"},
        {"src": "/img/b.png"},
    ]

    downloaded = service._fetch_and_save_image(page, images, False)

    assert downloaded == 3
    assert page.context.request.calls == [
        "https://example.com/img/a.png",
        "https://example.com/img/a.png",
        "https://example.com/img/b.png",
    ]
    assert len(list(tmp_path.iterdir())) == 3
