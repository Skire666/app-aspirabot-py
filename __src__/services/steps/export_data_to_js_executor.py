"""IStepExecutor for CLICK_ON_ELEMENT."""

from __future__ import annotations

from typing import override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.export_data_to_js_params import ExportDataToJsParams
from repositories.json_repository import JsonFileRepository
from services.workflow_service import register_step_executor
from shared.datetime_util import get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff
from shared.enums import StepTypeEnum
from shared.exception_util import ExportFolderNotConfiguredError, NoDataToExportError
from shared.i18n_fra import ERROR_TEMPLATES

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


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
    def execute_logical(self, _: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = ExportDataToJsParams.from_dict(context.step_scraping_data.params)

        # Nothing to write — skip without logging noise.
        if not context.extracted_data or not context.extracted_data.urls:
            raise NoDataToExportError()

        # Guard against unset export folder (default Path() resolves to ".").
        if str(context.folder_export) in {".", ""}:
            raise ExportFolderNotConfiguredError()

        # Build timestamped destination path and delegate write to the repository.
        timestamp = get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff()
        dest = context.folder_export / f"{p.prefix_file}_{timestamp}.json"

        self._json_repo.write_from_dict(dest, context.extracted_data.to_dict())

        context.last_message_step = f"Export vers fichier JSON. Préfixe : {p.prefix_file}."

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = ExportDataToJsParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)

        # if prefix_file est vide ou ne contient que des espaces
        if not p.prefix_file.strip():
            return [ERROR_TEMPLATES["export_data_to_js_prefix_file_required"].format(step=index_display)]
        return []


register_step_executor(ExportDataToJsExecutor())
