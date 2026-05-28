"""Runtime context passed to each step executor during workflow execution.

Replaces the opaque ``dict[str, Any]`` previously forwarded via
``_build_runtime_params``.  All cross-step state is referenced by name
instead of by string key.

Example:
    >>> import threading
    >>> from pathlib import Path
    >>> ctx = ScrapingContextModel(...)
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------
# Model
# -----------------------------------------------------------------------------


@dataclass
class KeyData:
    """CSS selector, comment, and extracted string values for one mapping key."""

    css_selector: str
    comment: str
    values: list[str] = field(default_factory=list)


@dataclass
class UrlData:
    """Extracted key data indexed by mapping key name for one URL."""

    keys: dict[str, KeyData] = field(default_factory=dict)


@dataclass
class ExtractedData:
    """All extracted data, indexed by URL then by mapping key."""

    urls: dict[str, UrlData] = field(default_factory=dict)

    def to_dict(self) -> dict[str, dict[str, dict[str, Any]]]:
        """Serialize to a plain dict for JSON export."""
        return {
            url: {
                key: {"css_selector": val_kd.css_selector, "comment": val_kd.comment, "values": val_kd.values}
                for key, val_kd in val_ud.keys.items()
            }
            for url, val_ud in self.urls.items()
        }


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
        url_source: Optional URL source scenario consumed by OPEN_URL steps.
        last_message_step: Output — human-readable result set by the executor.
        pending_jump: Output — jump target (index or step_id) set by the executor.
        end_process: Output — set to True by the executor to stop the workflow.

    Example:
        >>> import threading
        >>> from pathlib import Path
        >>> ctx = ScrapingContextModel(...)
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
    step_scraping_data: StepScrapingModel | None = field(default=None)

    # date extracted
    extracted_data: ExtractedData | None = field(default=None)

    # Optional URL source scenario injected by the service before each run.
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

    def reset_before_new_process(self, steps: list[StepScrapingModel]) -> None:
        """Reset all runtime state before starting a new workflow process.

        Args:
            steps: The list of steps in the workflow, used to build step ID/index maps.
        """
        if self.url_source is not None:
            self.url_source.reset()

        self.last_result_step = True
        self.pending_jump = None
        self.end_process = False
        self.downloaded_urls = set()
        self.extracted_data = ExtractedData()
        self.last_message_step = ""

        # Build fast-lookup maps used by JUMP_TO_STEP resolution.
        self.step_id_by_index = [step.step_id for step in steps]
        self.step_index_by_id = {step.step_id: idx for idx, step in enumerate(steps)}

    def prepare_step_execution(self, step: StepScrapingModel) -> None:
        """Prepare the context for a new step execution.

        Args:
            step: The step about to be executed.
        """
        self._time_started = time.time()
        self.step_scraping_data = step
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

    def push_extracted_values(self, mapping_key: str, sel: str, com: str, vals: list[str]) -> None:
        """Push extracted values into the context's extracted_data dict.

        Args:
            mapping_key: The key under which to store the extracted values.
            sel: The CSS selector used to find the elements.
            com: A user-provided comment for the extracted values.
            vals: The list of extracted string values to store.
        """
        url = self.last_url_opened or "no_url"

        if url not in self.extracted_data.urls:
            self.extracted_data.urls[url] = UrlData()

        self.extracted_data.urls[url].keys[mapping_key] = KeyData(css_selector=sel, comment=com, values=vals)
        # TODO PCO : je réacrase tout, et en vrai, c'est pas plus mal
        # a voir si je dois merge les values en cas d'existant


# EOF
