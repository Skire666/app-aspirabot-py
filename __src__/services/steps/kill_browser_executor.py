"""IStepExecutor for END_PROCESS."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import time
from typing import cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.kill_browser_params import KillBrowserParams
from shared.enums import ProcessResultEnum, StepTypeEnum
from shared.step_registry import register_step_executor
from shared.time_util import convert_to_sec

_C_ABNORMAL_PAGE_COUNT = 2


class KillBrowserExecutor(IStepExecutor):
    """Executor for the end process scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_KILL_BROWSER

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> ProcessResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(KillBrowserParams, context.step_scraping_data.params)
        try:
            delay = convert_to_sec(p.wait_duration, p.wait_unit)
            if delay > 0:
                time.sleep(delay)
            event_bus.log_step(context, "Arrêt du processus demandé.")
            if len(browser.get_all_pages()) >= _C_ABNORMAL_PAGE_COUNT:
                event_bus.log_step(context, "Excp : Comportement anormal détecté : Plusieurs onglets ouverts.")
                event_bus.log_step(context, "Excp : Fermeture interrompue du navigateur. Investigation nécessaire.")
                self._do_pause(context, event_bus)
            browser.close_all_tabs()
            context.end_process = True
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Excp : {exc}")
            return ProcessResultEnum.E_ERROR
        else:
            return ProcessResultEnum.E_SUCCESS

    @staticmethod
    def _do_pause(context: ScrapingContextModel, event_bus: IScrapingEventBus) -> None:
        """Block until the user resumes or the scraping is cancelled.

        Args:
            context: Current scraping context.
            p: Step parameters.
            event_bus: Event bus for emitting the resume/cancel log entry.
        """
        if callable(context.on_user_wait):
            context.on_user_wait()
        context.pause_event.clear()
        context.pause_event.wait()
        cancelled = context.cancel_event.is_set()
        msg = "Reprise utilisateur détectée" if not cancelled else "Attente annulée par l'utilisateur"
        event_bus.log_step(context, msg)


register_step_executor(KillBrowserExecutor())


# EOF
