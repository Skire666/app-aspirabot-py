"""Protocol describing the contract of step form views."""

from __future__ import annotations

from typing import Any, Protocol


class BaseStepFormView(Protocol):
    """Interface implemented by all step form widgets."""

    def get_data(self) -> dict[str, Any]:
        """Returns raw form data as entered by the user."""
        ...

    def grid(self, *args: Any, **kwargs: Any) -> Any:
        """Places the widget in a grid layout."""
        ...