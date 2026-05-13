"""Runtime context passed to each step executor during workflow execution.

Replaces the opaque ``dict[str, Any]`` previously forwarded via
``_build_runtime_params``.  All cross-step state is referenced by name
instead of by string key.

Example:
    >>> import threading
    >>> from pathlib import Path
    >>> ctx = ScrapingContextModel(
    ...     prev_success=True,
    ...     folder=Path("."),
    ...     downloaded_urls=set(),
    ...     step_id_by_index=[],
    ...     step_index_by_id={},
    ...     pause_event=threading.Event(),
    ...     cancel_event=threading.Event(),
    ...     on_user_wait=None,
    ...     step_params={},
    ... )
    >>> ctx.prev_success
    True
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from interfaces.i_url_source_provider import IUrlSourceProvider

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


@dataclass
class ScrapingContextModel:
    """Typed runtime context injected into each step executor.

    Attributes:
        prev_success: Whether the immediately preceding step succeeded.
        folder: Working folder for file-producing steps (download, etc.).
        downloaded_urls: Deduplication set of already-downloaded image URLs.
        step_id_by_index: Ordered list of step IDs for the current workflow.
        step_index_by_id: Reverse map from step_id to zero-based index.
        pause_event: Threading event cleared when the run is paused.
        cancel_event: Threading event set when the run is cancelled.
        on_user_wait: Optional callback fired by WAIT_USER_ACTION steps.
        step_params: Raw step-specific parameter dict from the step model.
        url_source: Optional URL source provider consumed by OPEN_URL steps.
        last_message_step: Output — human-readable result set by the executor.
        pending_jump: Output — jump target (index or step_id) set by the executor.
        end_process: Output — set to True by the executor to stop the workflow.

    Example:
        >>> import threading
        >>> from pathlib import Path
        >>> ctx = ScrapingContextModel(
        ...     prev_success=False,
        ...     folder=Path("."),
        ...     downloaded_urls=set(),
        ...     step_id_by_index=["a", "b"],
        ...     step_index_by_id={"a": 0, "b": 1},
        ...     pause_event=threading.Event(),
        ...     cancel_event=threading.Event(),
        ...     on_user_wait=None,
        ...     step_params={"selector": ".btn"},
        ... )
        >>> ctx.url_source is None
        True
        >>> ctx.end_process
        False
    """

    # Inputs from the orchestrator.
    prev_success: bool
    folder: Path
    downloaded_urls: set[str]
    step_id_by_index: list[str]
    step_index_by_id: dict[str, int]
    pause_event: threading.Event
    cancel_event: threading.Event
    on_user_wait: Callable[[], None] | None

    # Step-specific raw params (used to construct typed param models).
    step_params: dict[str, Any]

    # Optional URL source provider injected by the service before each run.
    url_source: IUrlSourceProvider | None = field(default=None)

    # Output signals written by executors and read back by the orchestrator.
    last_message_step: str = field(default="")
    pending_jump: str | int | None = field(default=None)
    end_process: bool = field(default=False)
