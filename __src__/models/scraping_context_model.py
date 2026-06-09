"""Runtime context passed to each step executor during workflow execution.

Replaces the opaque ``dict[str, Any]`` previously forwarded via
``_build_runtime_params``.  All cross-step state is referenced by name
instead of by string key.
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
from typing import TYPE_CHECKING, Any, cast

from models.app_configuration_model import AppConfigurationModel
from models.step_scraping_model import StepScrapingModel
from shared.enums import StepExecutionResultEnum

if TYPE_CHECKING:
    from interfaces.i_url_source_provider import IUrlSourceProvider

# -----------------------------------------------------------------------------
# Model
# -----------------------------------------------------------------------------


@dataclass
class ExtractedItem:
    """One extracted mapping entry: key name, selector/source, extracted values, comment."""

    key: str
    input: str
    values: list[str] = field(default_factory=list)
    comment: str = field(default="")


@dataclass
class ExtractedData:
    """All extracted items as a flat ordered list."""

    items: list[ExtractedItem] = field(default_factory=list)

    def to_list(self) -> list[dict[str, Any]]:
        """Serialize to a list of dicts for JSON export."""
        return [
            {"key": item.key, "input": item.input, "values": item.values, "comment": item.comment}
            for item in self.items
        ]

    @classmethod
    def import_from_data_json(cls, data: list[Any]) -> ExtractedData:
        """Reconstruct an ExtractedData instance from a list produced by to_list().

        Args:
            data: Raw list loaded from a JSON file produced by to_list().

        Returns:
            A fully reconstructed ExtractedData instance; empty when data is invalid.
        """
        result: list[ExtractedItem] = []
        for raw in data:
            if not isinstance(raw, dict):
                continue
            raw_typed = cast(dict[str, object], raw)
            raw_values = raw_typed.get("values")
            typed_values: list[object] = cast(list[object], raw_values) if isinstance(raw_values, list) else []
            result.append(
                ExtractedItem(
                    key=str(raw_typed.get("key") or ""),
                    input=str(raw_typed.get("input") or ""),
                    values=[str(v) for v in typed_values],
                    comment=str(raw_typed.get("comment") or ""),
                )
            )
        return cls(items=result)


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
        pending_jump: Output — jump target (index or step_id) set by the executor.
        end_process: Output — set to True by the executor to stop the workflow.
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
    log_messages: list[str] = field(default_factory=list)

    # date extracted
    extracted_data: ExtractedData | None = field(default=None)

    # Optional URL source scenario injected by the service before each run.
    url_source: IUrlSourceProvider | None = field(default=None)

    # Output signals written by executors and read back by the orchestrator.
    last_result_step: StepExecutionResultEnum = field(default=StepExecutionResultEnum.E_UNSET)
    last_url_opened: str = field(default="")  # peut être en erreur, pas grave
    last_time_elapsed: float = field(default=0.0)
    pending_jump: str | int | None = field(default=None)
    end_process: bool = field(default=False)
    browser_stats: tuple[int, str] = field(default=(0, "—"))

    # ------------------------------------------------------------------
    # Methods
    # ------------------------------------------------------------------

    def __init__(self, model_config: AppConfigurationModel) -> None:
        """Initialize the scraping context from the application configuration.

        Args:
            model_config: Application configuration providing export and runtime settings.
        """
        self.app_config = model_config
        self.folder_export = Path()
        self.downloaded_urls = set()
        self.extracted_data = ExtractedData()
        self.step_id_by_index = []
        self.step_index_by_id = {}
        self.pause_event = threading.Event()
        self.cancel_event = threading.Event()
        self.on_user_wait = None

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

        self.last_result_step = StepExecutionResultEnum.E_SUCCESS
        self.log_messages = []
        self.pending_jump = None
        self.end_process = False
        self.downloaded_urls = set()
        self.extracted_data = ExtractedData()
        self.browser_stats = (0, "—")

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
        self.last_time_elapsed = 0.0
        self.pending_jump = None
        self.end_process = False

    def set_result_execution(self, result: StepExecutionResultEnum) -> None:
        """Set the result of the step execution and update related state.

        Args:
            result: The execution result enum value.
        """
        self.last_result_step = result
        self.last_time_elapsed = time.time() - self._time_started + 0.001  # add 1ms to avoid zero values

    def push_extracted_values(self, mapping_key: str, inp: str, com: str, vals: list[str]) -> None:
        """Push extracted values into the context's extracted_data dict.

        Args:
            mapping_key: The key under which to store the extracted values.
            inp: The input value used to find the elements.
            com: A user-provided comment for the extracted values.
            vals: The list of extracted string values to store.
        """
        if self.extracted_data is None:
            self.extracted_data = ExtractedData()

        self.extracted_data.items.append(ExtractedItem(key=mapping_key, input=inp, values=vals, comment=com))

    def last_step_was_success(self) -> bool:
        """Helper to check if the last step execution was a success."""
        return self.last_result_step in {
            StepExecutionResultEnum.E_SKIPPED,
            StepExecutionResultEnum.E_SUCCESS,
            StepExecutionResultEnum.E_WARNING,
        }

    def reset_exported_data(self) -> None:
        """Clear all extracted data from the context.

        Clear extracted data after export to prevent duplicate exports
        """
        self.extracted_data = ExtractedData()


# EOF
