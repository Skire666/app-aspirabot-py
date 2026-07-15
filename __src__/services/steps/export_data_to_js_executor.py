"""IStepExecutor for EXPORT_DATA_TO_CSV."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from pathlib import Path
from typing import cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.export_data_to_csv_params import ExportDataToCsvParams
from repositories.csv_repository import CsvRepository
from shared.enums import ProcessResultEnum, StepTypeEnum
from shared.exception_util import ExportFolderNotConfiguredError, NoDataToExportError
from shared.path_util import can_write
from shared.step_registry import register_step_executor

# Separator used to flatten a field's multiple extracted values into one CSV cell.
_C_VALUES_SEPARATOR = " | "


class ExportDataToCsvExecutor(IStepExecutor):
    """Executor for the export data to CSV step."""

    def __init__(self) -> None:
        """Initialise the executor with its CSV row-level service."""
        self._csv_repository = CsvRepository()
        self._logger = logging.getLogger(__name__)

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_EXPORT_DATA_TO_CSV

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> ProcessResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(ExportDataToCsvParams, context.step_scraping_data.params)
        try:
            if not context.extracted_data:
                raise NoDataToExportError()  # noqa: TRY301
            if str(context.folder_export) in {".", ""}:
                raise ExportFolderNotConfiguredError()  # noqa: TRY301

            # write
            context.precompute_strategy_quality()

            # test before write
            dest: Path = context.folder_export / f"{p.csv_filename}.csv"
            if not can_write(dest):
                dest = context.folder_export / f"{p.csv_filename}.csv2"
                event_bus.log_step(context, "ERROR : Impossible de remplacer le fichier CSV (try 2)")
                if not can_write(dest):
                    dest = context.folder_export / f"{p.csv_filename}.csv3"
                    event_bus.log_step(context, "ERROR : Impossible de remplacer le fichier CSV (try 3)")
            self._csv_repository.write_file(dest, context.extracted_data)

            # debug
            event_bus.log_step(context, f"Fichier CSV : '{p.csv_filename}'.csv")
            event_bus.log_step(context, f"Chemin complet : '{dest}'")
            context.reset_exported_data()
        except Exception as exc:
            self._logger.exception("An error occurred while exporting data to CSV.")
            event_bus.log_step(context, f"Excp : {exc}")
            return ProcessResultEnum.E_ERROR
        else:
            return ProcessResultEnum.E_SUCCESS


register_step_executor(ExportDataToCsvExecutor())


# EOF
