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
from typing import TYPE_CHECKING

from models.app_configuration_model import AppConfigurationModel
from models.step_scraping_model import StepScrapingModel
from models.steps_collections_model import StepsCollections
from models.youtube_infos_video_model import YoutubeInfosVideoModel
from repositories.csv_repository import CsvRepository
from shared.constants import C_COLUMN_DATE_CREATED, C_COLUMN_DATE_MODIFIED, C_COLUMN_PRIMARY_KEY, C_COLUMN_SOURCE
from shared.datetime_util import get_datetime_now_yyyy_mm_dd_hh_mm_ss
from shared.enums import ExtractTargetEnum, StepExecutionResultEnum, StepTypeEnum
from shared.typing.csv_table import CsvTable

if TYPE_CHECKING:
    from interfaces.i_url_source_provider import IUrlSourceProvider

# -----------------------------------------------------------------------------
# Model
# -----------------------------------------------------------------------------


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
    extracted_data: CsvTable | None = field(default=None)

    # Optional URL source scenario injected by the service before each run.
    url_source: IUrlSourceProvider | None = field(default=None)

    # Output signals written by executors and read back by the orchestrator.
    next_error_is_handled: bool = field(default=False)
    last_result_step: StepExecutionResultEnum = field(default=StepExecutionResultEnum.E_UNSET)
    last_url_opened: str = field(default="")  # peut être en erreur, pas grave
    last_time_elapsed: float = field(default=0.0)
    pending_jump: str | int | None = field(default=None)
    end_process: bool = field(default=False)
    browser_stats: tuple[int, str] = field(default=(0, "—"))

    # ------------------------------------------------------------------
    # Methods
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        """Initialize the scraping context from the application configuration."""
        self.app_config = AppConfigurationModel.get_instance()
        self.folder_export = Path()
        self.downloaded_urls = set()
        self.extracted_data = None
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
        self.browser_stats = (0, "—")

        # Build fast-lookup maps used by JUMP_TO_STEP resolution.
        self.step_id_by_index = [step.step_id for step in steps]
        self.step_index_by_id = {step.step_id: idx for idx, step in enumerate(steps)}

    def prepare_extracted_data(self, steps: list[StepScrapingModel]) -> None:
        """Prepare the extracted data table with headers from all steps.

        Args:
            steps: The list of steps in the workflow, used to build the CSV header.
        """
        ls_collection = StepsCollections(steps)
        if ls_collection.count_type_step(StepTypeEnum.E_EXPORT_DATA_TO_CSV) >= 1:
            filename = ls_collection.get_name_of_file_csv()
            csv_repository = CsvRepository()
            fullpath = self.folder_export / f"{filename}.csv"
            if csv_repository.file_exists(fullpath):
                self.extracted_data = csv_repository.read_file(fullpath)
            else:
                base_headers = {C_COLUMN_PRIMARY_KEY, C_COLUMN_DATE_CREATED, C_COLUMN_DATE_MODIFIED, C_COLUMN_SOURCE}
                self.extracted_data = CsvTable(header=base_headers)
                csv_repository.create_file(fullpath, base_headers)
        else:
            self.extracted_data = None

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
        self.extracted_data = None

    def last_result_is_error(self) -> bool:
        """Check if the last result indicates an error."""
        return self.last_result_step in {StepExecutionResultEnum.E_ERROR, StepExecutionResultEnum.E_FATAL}

    # ------------------------------------------------------------------
    # Push extracted data into the context's extracted_data table.
    # ------------------------------------------------------------------

    def push_links_extracted(self, links: list[str]) -> None:
        """Push extracted links into the context's extracted data table.

        Args:
            links: List of extracted link strings.
        """
        assert self.extracted_data is not None

        date_now = get_datetime_now_yyyy_mm_dd_hh_mm_ss()
        for link in links:
            index = self.extracted_data.find_row_index(C_COLUMN_PRIMARY_KEY, link)
            if index is None:
                dc = {C_COLUMN_PRIMARY_KEY: link, C_COLUMN_DATE_CREATED: date_now}
                self.extracted_data.add_row(dc)
            else:
                self.extracted_data.update_cell(index, C_COLUMN_DATE_MODIFIED, date_now)

    def push_texts_extracted(self, mapping: str, texts: list[str], target: ExtractTargetEnum) -> None:
        """Push extracted texts into the context's extracted data table.

        Args:
            mapping: The mapping key for the extracted texts.
            texts: List of extracted text strings.
        """
        assert self.extracted_data is not None

        # push
        index = self.extracted_data.find_row_index(C_COLUMN_PRIMARY_KEY, self.last_url_opened)
        date_now = get_datetime_now_yyyy_mm_dd_hh_mm_ss()
        value_flatten = texts if target == ExtractTargetEnum.E_ALL else texts[0]
        print(f"DEBUG: push_texts_extracted - value_flatten: {value_flatten}")
        flt = self.extracted_data.flatten_value(value_flatten)
        if index is None:  # not found...
            dc = {
                C_COLUMN_PRIMARY_KEY: self.last_url_opened,
                mapping: flt,
                C_COLUMN_DATE_CREATED: date_now,
                C_COLUMN_SOURCE: "texts",
            }
            self.extracted_data.add_row(dc)
        else:
            self.extracted_data.update_cell(index, mapping, flt)
            self.extracted_data.update_cell(index, C_COLUMN_DATE_MODIFIED, date_now)
            self.extracted_data.update_cell(index, C_COLUMN_SOURCE, "texts")

    def push_vars_extracted(self, mapping: str, value: str) -> None:
        """Push a single extracted variable into the context's extracted data table."""
        assert self.extracted_data is not None

        # push
        index = self.extracted_data.find_row_index(C_COLUMN_PRIMARY_KEY, self.last_url_opened)
        flt = self.extracted_data.flatten_value(value)
        date_now = get_datetime_now_yyyy_mm_dd_hh_mm_ss()
        if index is None:  # not found...
            dc = {
                C_COLUMN_PRIMARY_KEY: self.last_url_opened,
                mapping: flt,
                C_COLUMN_DATE_CREATED: date_now,
                C_COLUMN_SOURCE: "vars",
            }
            self.extracted_data.add_row(dc)
        else:
            self.extracted_data.update_cell(index, mapping, flt)
            self.extracted_data.update_cell(index, C_COLUMN_DATE_MODIFIED, date_now)
            self.extracted_data.update_cell(index, C_COLUMN_SOURCE, "vars")

    def push_ytdlp_extracted(self, ytdlp_data: YoutubeInfosVideoModel) -> None:
        """Push extracted YouTube data into the context's extracted data table."""
        assert self.extracted_data is not None

        # push
        index = self.extracted_data.find_row_index(C_COLUMN_PRIMARY_KEY, self.last_url_opened)
        casted = ytdlp_data.to_dict()
        date_now = get_datetime_now_yyyy_mm_dd_hh_mm_ss()

        for key, value in casted.items():
            casted[key] = self.extracted_data.flatten_value(value)

        if index is None:  # not found...
            casted[C_COLUMN_PRIMARY_KEY] = self.last_url_opened
            casted[C_COLUMN_DATE_CREATED] = date_now
            casted[C_COLUMN_SOURCE] = "ytdlp"

            self.extracted_data.add_row(casted)
        else:
            # update
            for key, value in casted.items():
                self.extracted_data.update_cell(index, key, value)
            self.extracted_data.update_cell(index, C_COLUMN_DATE_MODIFIED, date_now)
            self.extracted_data.update_cell(index, C_COLUMN_SOURCE, "ytdlp")


# EOF
