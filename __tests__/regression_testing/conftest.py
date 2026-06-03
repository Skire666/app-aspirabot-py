"""Shared pytest fixtures for the regression_testing suite."""

from __future__ import annotations

import tkinter as tk

import pytest


@pytest.fixture(scope="session")
def tk_root() -> tk.Tk:
    """Provide a single hidden Tk root for the entire test session."""
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()
