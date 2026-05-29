"""Contract for step execution and validation in the service layer.

Each concrete step type owns exactly one implementation of this interface,
named ``<StepName>Executor``.  It registers itself in the step registry at
import time.  The service orchestrators query the registry and invoke this
contract without knowing any concrete step type by name.

Example:
    >>> executor = WaitElementExecutor()
    >>> executor.step_type()
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps_context_model import StepsContext
from shared.enums import StepTypeEnum

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

    Example:
        >>> executor = ConcreteExecutor()
        >>> errors = executor.validate_model(model, 0, StepsContext.from_list([]))
        >>> bool(errors)
        True
    """

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the StepTypeEnum this executor handles.

        Returns:
            The matching StepTypeEnum enum member.
        """
        ...

    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step using the browser service and the runtime context.

        Step-specific parameters are read from ``context.step_params`` (via a
        typed param model).  Cross-step runtime state is read from the typed
        attributes of ``context``.  Output signals are written back to
        ``context.last_message_step``, ``context.pending_jump``, or
        ``context.end_process``.

        Args:
            browser: The active browser service instance.
            context: Runtime context carrying step params, orchestrator state,
                and mutable output-signal slots.

        Raises:
            PlaywrightError: On browser-level failure.
            TimeoutError: When a wait step exceeds its deadline.
            FileNotFoundError: When a required file is missing.
        """
        ...

    def validate_model(
        self,
        model: StepScrapingModel,
        step_index: int,
        steps_context: StepsContext,
    ) -> list[str]:
        """Validate step parameters and return human-readable error messages.

        Args:
            model: The step model containing typed params to validate.
            step_index: Zero-based position of the step in the workflow.
            steps_context: Read-only snapshot of the full workflow, used for
                cross-step checks such as jump-target resolution.

        Returns:
            A list of French error strings; empty when the params are valid.
        """
        ...
