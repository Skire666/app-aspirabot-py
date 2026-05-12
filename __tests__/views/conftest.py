"""Shared Tkinter fixtures for all view tests.

A single session-scoped Tk root is created once and reused across all tests
to avoid the conflict that arises when multiple Tk() instances are created
and destroyed in sequence within the same process.
"""

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
