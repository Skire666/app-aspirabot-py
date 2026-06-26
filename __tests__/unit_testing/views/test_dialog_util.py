"""Tests for views/dialog_util.py."""

from __future__ import annotations

from unittest.mock import patch

from views.dialog_util import (
    ask_delete_profile_confirmation,
    ask_delete_scenario_confirmation,
    ask_duplicate_scenario_confirmation,
    ask_launch_scraping_confirmation,
)


class TestAskDuplicateScenarioConfirmation:
    def test_returns_true_when_confirmed(self) -> None:
        with patch("views.dialog_util.messagebox.askyesno", return_value=True):
            assert ask_duplicate_scenario_confirmation() is True

    def test_returns_false_when_denied(self) -> None:
        with patch("views.dialog_util.messagebox.askyesno", return_value=False):
            assert ask_duplicate_scenario_confirmation() is False


class TestAskDeleteScenarioConfirmation:
    def test_returns_true_when_confirmed(self) -> None:
        with patch("views.dialog_util.messagebox.askyesno", return_value=True):
            assert ask_delete_scenario_confirmation() is True

    def test_returns_false_when_denied(self) -> None:
        with patch("views.dialog_util.messagebox.askyesno", return_value=False):
            assert ask_delete_scenario_confirmation() is False


class TestAskDeleteProfileConfirmation:
    def test_returns_true_when_confirmed(self) -> None:
        with patch("views.dialog_util.messagebox.askyesno", return_value=True):
            assert ask_delete_profile_confirmation("My Profile") is True

    def test_passes_profile_name(self) -> None:
        with patch("views.dialog_util.messagebox.askyesno") as mock_dialog:
            mock_dialog.return_value = False
            ask_delete_profile_confirmation("Test Profile")
            args = mock_dialog.call_args[0]
            assert "Test Profile" in str(args)


class TestAskLaunchScrapingConfirmation:
    def test_returns_true_when_confirmed(self) -> None:
        with patch("views.dialog_util.messagebox.askyesno", return_value=True):
            assert ask_launch_scraping_confirmation("Warning!") is True

    def test_returns_false_when_denied(self) -> None:
        with patch("views.dialog_util.messagebox.askyesno", return_value=False):
            assert ask_launch_scraping_confirmation("Warning!") is False
