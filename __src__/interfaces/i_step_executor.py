"""Contract for step execution and validation in the service layer.

Each concrete step type owns exactly one implementation of this interface,
named ``<StepName>Executor``.  It registers itself in the step registry at
import time.  The service orchestrators query the registry and invoke this
contract without knowing any concrete step type by name.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from interfaces.i_scraping_event_bus import IScrapingEventBus
from models.scraping_context_model import ScrapingContextModel
from shared.enums import ProcessResultEnum, StepTypeEnum

if TYPE_CHECKING:
    from interfaces.i_web_browser_service import IWebBrowserService

# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------


class IStepExecutor(Protocol):
    """Service-layer contract for one step type.

    Implementations handle both Playwright execution and parameter validation.
    Step-specific parameters are accessed via ``context.step_params`` and
    converted to typed param models.  Cross-step runtime state (previous
    result, folder, events, …) is accessed via named attributes on
    ``ScrapingContextModel``.  Output signals (last message, jump target,
    end-process flag) are written back to the same context object.

    Executors receive a ``IWebBrowserService`` instance instead of a raw page.
    When page access is needed, call ``browser.get_current_page()``. When
    multi-tab management is needed, call ``browser.get_all_pages()``.
    """

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the StepTypeEnum this executor handles.

        Returns:
            The matching StepTypeEnum enum member.
        """
        ...

    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> ProcessResultEnum:
        """Execute the step using the browser service and the runtime context.

        Args:
            browser: The active browser service instance.
            context: Runtime context carrying step params, orchestrator state,
                and mutable output-signal slots.
            event_bus: Event bus for emitting intermediate log entries via
                ``log_step()``.  Lifecycle methods on the bus are reserved for
                ``ScrapingService`` and must not be called from executors.

        Returns:
            ``SUCCESS`` — step completed fully.
            ``WARNING`` — completed with a non-critical anomaly; workflow continues.
            ``ERROR``   — step failed; workflow continues to next step.
            ``FATAL``   — step failed; workflow stops immediately.

        Raises:
            PlaywrightError: On browser-level failure.
            TimeoutError: When a wait step exceeds its deadline.
            FileNotFoundError: When a required file is missing.
        """
        ...


# EOF
