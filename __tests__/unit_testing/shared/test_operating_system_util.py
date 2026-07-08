"""Tests for shared/operating_system_util.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from shared.exception_util import UnsupportedOperatingSystemError
from shared.operating_system_util import OperatingSystem, detect_os, open_folder

# ---------------------------------------------------------------------------
# detect_os
# ---------------------------------------------------------------------------


class TestDetectOs:
    def test_detects_windows(self) -> None:
        with patch("platform.system", return_value="Windows"):
            assert detect_os() == OperatingSystem.WINDOWS

    def test_detects_linux(self) -> None:
        with patch("platform.system", return_value="Linux"):
            assert detect_os() == OperatingSystem.LINUX

    def test_detects_macos(self) -> None:
        with patch("platform.system", return_value="Darwin"):
            assert detect_os() == OperatingSystem.MACOS

    def test_returns_unknown_for_unrecognised_os(self) -> None:
        with patch("platform.system", return_value="FreeBSD"):
            assert detect_os() == OperatingSystem.UNKNOWN

    def test_returns_notset_when_empty_string(self) -> None:
        with patch("platform.system", return_value=""):
            assert detect_os() == OperatingSystem.NOTSET


# ---------------------------------------------------------------------------
# open_folder
# ---------------------------------------------------------------------------


class TestOpenFolder:
    def test_calls_startfile_on_windows(self, tmp_path: Path) -> None:
        with patch("platform.system", return_value="Windows"), patch("os.startfile") as mock_startfile:
            open_folder(tmp_path)
            mock_startfile.assert_called_once_with(tmp_path)

    def test_calls_open_on_macos(self, tmp_path: Path) -> None:
        with patch("platform.system", return_value="Darwin"), patch("subprocess.Popen") as mock_popen:
            open_folder(tmp_path)
            mock_popen.assert_called_once_with(["open", tmp_path])

    def test_calls_xdg_open_on_linux(self, tmp_path: Path) -> None:
        with patch("platform.system", return_value="Linux"), patch("subprocess.Popen") as mock_popen:
            open_folder(tmp_path)
            mock_popen.assert_called_once_with(["xdg-open", tmp_path])

    def test_raises_on_unknown_os(self, tmp_path: Path) -> None:
        with patch("platform.system", return_value="FreeBSD"), pytest.raises(UnsupportedOperatingSystemError):
            open_folder(tmp_path)
