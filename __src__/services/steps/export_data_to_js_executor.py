"""IStepExecutor for EXPORT_DATA_TO_JS."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.export_data_to_js_params import ExportDataToJsParams
from repositories.json_repository import JsonFileRepository
from shared.datetime_util import get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff
from shared.enums import StepExecutionResultEnum, StepTypeEnum
from shared.exception_util import ExportFolderNotConfiguredError, NoDataToExportError
from shared.step_registry import register_step_executor


class ExportDataToJsExecutor(IStepExecutor):
    """Executor for the export data to JavaScript step."""

    def __init__(self) -> None:
        """Initialise the executor with its JSON file repository."""
        self._json_repo = JsonFileRepository()

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_EXPORT_DATA_TO_JS

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> StepExecutionResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(ExportDataToJsParams, context.step_scraping_data.params)
        try:
            if not context.extracted_data or not context.extracted_data.items:
                raise NoDataToExportError()  # noqa: TRY301
            if str(context.folder_export) in {".", ""}:
                raise ExportFolderNotConfiguredError()  # noqa: TRY301
            timestamp = get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff()
            dest = context.folder_export / f"{p.prefix_file}_{timestamp}.json"
            self._json_repo.write_from_dict(dest, context.extracted_data.to_list())
            event_bus.log_step(context, f"Export vers fichier JSON. Préfixe : {p.prefix_file}.")
            context.reset_exported_data()
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Excp : {exc}")
            return StepExecutionResultEnum.E_ERROR
        else:
            return StepExecutionResultEnum.E_SUCCESS


register_step_executor(ExportDataToJsExecutor())


# EOF
