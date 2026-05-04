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

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from interfaces.i_step_executor import IStepExecutor
    from interfaces.i_step_form_def import IStepFormDef
    from models.step_scraping_model import StepType

## ---------------------------------------------------------------------------
## Internal storage
## ---------------------------------------------------------------------------

# Populated at import time by each concrete executor / form-def module.
_executors: dict[StepType, IStepExecutor] = {}
_forms: dict[StepType, IStepFormDef] = {}

## ---------------------------------------------------------------------------
## Registration helpers (called by concrete classes at module level)
## ---------------------------------------------------------------------------


def register_executor(executor: IStepExecutor) -> None:
    """Registers an executor instance in the service registry.

    Args:
        executor: Concrete IStepExecutor instance.

    Returns:
        None.

    Raises:
        None.
    """
    _executors[executor.step_type()] = executor


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

## ---------------------------------------------------------------------------
## Lookup helpers (called by orchestrators at runtime)
## ---------------------------------------------------------------------------


def get_executor(step_type: StepType) -> IStepExecutor:
    """Returns the registered executor for the given step type.

    Args:
        step_type: The StepType to look up.

    Returns:
        The IStepExecutor instance registered for that type.

    Raises:
        ValueError: When no executor has been registered for the type.
    """
    executor = _executors.get(step_type)
    if executor is None:
        raise ValueError(f"No executor registered for step type: {step_type}")
    return executor


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
        raise ValueError(f"No form registered for step type: {step_type}")
    return form


def get_default_params(step_type: StepType) -> dict[str, Any]:
    """Returns the default parameter dict for the given step type.

    Args:
        step_type: The StepType to query.

    Returns:
        A plain dict of default parameter values.

    Raises:
        ValueError: When no executor has been registered for the type.
    """
    return get_executor(step_type).default_params_dict()


def get_all_labels() -> dict[StepType, str]:
    """Returns a mapping of every registered StepType to its French label.

    Returns:
        Dict of {StepType: label} for all registered form definitions.

    Raises:
        None.
    """
    return {st: f.label() for st, f in _forms.items()}
