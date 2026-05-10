"""Central registry for all step type implementations.

Executor and form-definition instances register themselves here at module
import time.  Orchestrators (ScrapingService, WorkflowService,
StepInlineFormPanel, StepItemRenderer) query the registry by StepType
without depending on any concrete step class.

Bootstrap: import ``models.steps``, ``services.steps``, and ``views.steps``
before querying the registry.  Each package ``__init__.py`` imports all
concrete classes, which triggers registration.

Example:
    >>> from shared.step_registry import get_executor
    >>> executor = get_executor(StepType.WAIT_ELEMENT)
    >>> executor.step_type()
    <StepType.WAIT_ELEMENT: 'WAIT_ELEMENT'>
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING

from shared.exception_util import FormNotRegisteredError

if TYPE_CHECKING:
    from interfaces.i_step_form_def import IStepFormDef
    from models.step_scraping_model import StepType

# ---------------------------------------------------------------------------
# Internal storage
# ---------------------------------------------------------------------------

# Populated at import time by each concrete executor / form-def module.
_forms: dict[StepType, IStepFormDef] = {}

# ---------------------------------------------------------------------------
# Registration helpers (called by concrete classes at module level)
# ---------------------------------------------------------------------------


def register_form(form: IStepFormDef) -> None:
    """Registers a form-definition instance in the view registry.

    Args:
        form: Concrete IStepFormDef instance.

    Returns:
        None.

    Raises:
        None.
    """
    _forms[form.step_type()] = form


# ---------------------------------------------------------------------------
# Lookup helpers (called by orchestrators at runtime)
# ---------------------------------------------------------------------------


def get_form(step_type: StepType) -> IStepFormDef:
    """Returns the registered form definition for the given step type.

    Args:
        step_type: The StepType to look up.

    Returns:
        The IStepFormDef instance registered for that type.

    Raises:
        ValueError: When no form def has been registered for the type.
    """
    form = _forms.get(step_type)
    if form is None:
        raise FormNotRegisteredError(step_type)
    return form
