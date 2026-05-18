"""Runtime context passed to each step executor during workflow execution.

Replaces the opaque ``dict[str, Any]`` previously forwarded via
``_build_runtime_params``.  All cross-step state is referenced by name
instead of by string key.

Example:
    >>> import threading
    >>> from pathlib import Path
    >>> ctx = ScrapingContextModel(
    ...     app_config=AppConfigurationModel(),
    ...     folder_export=Path("."),
    ...     downloaded_urls=set(),
    ...     step_id_by_index=[],
    ...     step_index_by_id={},
    ...     pause_event=threading.Event(),
    ...     cancel_event=threading.Event(),
    ...     on_user_wait=None,
    ...     step_params={},
    ... )
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from models.app_configuration_model import AppConfigurationModel
from models.step_scraping_model import StepScrapingModel

if TYPE_CHECKING:
    from interfaces.i_url_source_provider import IUrlSourceProvider

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


@dataclass
class ScrapingContextModel:
    """Typed runtime context injected into each step executor.

    Attributes:
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
        ...     app_config=AppConfigurationModel(),
        ...     folder_export=Path("."),
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
    app_config: AppConfigurationModel
    folder_export: Path
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
    last_result_step: bool = field(default=True)
    last_url_opened: str = field(default="")  # peut être en erreur, pas grave
    last_time_elapsed: float = field(default=0.0)
    pending_jump: str | int | None = field(default=None)
    end_process: bool = field(default=False)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def prepare_step_execution(self, step: StepScrapingModel) -> None:
        """Prepare the context for a new step execution.

        Args:
            step: The step about to be executed.
        """
        self._time_started = time.time()
        self.step_params = step.params
        self.last_result_step = True
        self.last_message_step = ""
        self.last_time_elapsed = 0.0
        self.pending_jump = None
        self.end_process = False

    def set_result_execution(self, is_success: bool, message: str) -> None:
        """Set the result of the step execution and update related state.

        Args:
            is_success: True when the step completed without error.
            message: Human-readable result message.
        """
        self.last_result_step = is_success
        if not self.last_message_step:
            self.last_message_step = message
        self.last_time_elapsed = time.time() - self._time_started
