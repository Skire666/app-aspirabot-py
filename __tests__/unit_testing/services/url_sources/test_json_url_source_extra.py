"""Extra coverage for json_url_source.py — buffered preview, mtime_desc sort, pending_urls path."""

from __future__ import annotations

import json
from pathlib import Path

from services.url_sources.json_url_source import JsonUrlSourceProvider
from shared.enums import UrlSortOrderEnum


def _write_json(folder: Path, name: str, data: object) -> Path:
    f = folder / name
    f.write_text(json.dumps(data), encoding="utf-8")
    return f


class TestPreviewWithBufferedUrl:
    """Cover lines 138-143: when _buffered is not _SENTINEL in preview_url_listed."""

    def test_preview_includes_buffered_url(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "a.json", ["http://a.com", "http://b.com"])
        p = JsonUrlSourceProvider(str(tmp_path))

        # Trigger has_next to fill the buffer
        assert p.load_url_if_available()

        # _buffered is now set to "http://a.com"
        preview = p.preview_url_listed()

        # The buffered URL should appear first in the preview
        assert "http://a.com" in preview

    def test_preview_includes_pending_urls(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "a.json", ["http://a.com", "http://b.com", "http://c.com"])
        p = JsonUrlSourceProvider(str(tmp_path))

        # Fill buffer + pending
        assert p.load_url_if_available()
        preview = p.preview_url_listed()

        assert "http://a.com" in preview
        assert "http://b.com" in preview
        assert "http://c.com" in preview


class TestMtimeDescSortOrder:
    """Cover line 200: E_MTIME_DESC sort order in _discover_files."""

    def test_mtime_desc_sort(self, tmp_path: Path) -> None:
        import time

        # Create files with different mtimes
        f1 = _write_json(tmp_path, "old.json", ["http://old.com"])
        time.sleep(0.05)
        f2 = _write_json(tmp_path, "new.json", ["http://new.com"])

        p = JsonUrlSourceProvider(str(tmp_path), UrlSortOrderEnum.E_MTIME_DESC)

        # Newest first → http://new.com should come out first
        first = p.pop_url()
        assert first == "http://new.com"


class TestExhaustedDisplayText:
    """Cover line 168: 'plus aucune URL' in display_progress_tuple_text."""

    def test_exhausted_shows_no_more_url(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "a.json", ["http://a.com"])
        p = JsonUrlSourceProvider(str(tmp_path))
        p.pop_url()
        # Advance through all files
        assert not p.load_url_if_available()
        text = p.display_progress_tuple_text()
        assert "plus aucune" in text


class TestPendingUrlsPath:
    """Cover line 217: _buffered = _pending_urls.pop() — consuming within _fill_one_url_if_empty."""

    def test_multiple_urls_from_pending(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "a.json", ["http://x.com", "http://y.com", "http://z.com"])
        p = JsonUrlSourceProvider(str(tmp_path))

        urls = []
        while p.load_url_if_available():
            urls.append(p.pop_url())

        assert urls == ["http://x.com", "http://y.com", "http://z.com"]
