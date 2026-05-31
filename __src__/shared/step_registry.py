"""Central registry for all step type implementations.

Executor, form-definition, and params-builder instances register themselves
here at module import time.  Orchestrators (ScrapingService, WorkflowService,
StepInlineFormPanel, StepItemRenderer, StepScrapingModel) query the registry
by StepType without depending on any concrete step class.

Bootstrap: import ``models.steps``, ``presenters.steps``, ``services.steps``,
and ``views.steps`` before querying the registry.  Each package
``__init__.py`` imports all concrete classes, which triggers registration.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from shared.enums import StepTypeEnum
from shared.exception_util import (
    ExecutorNotRegisteredError,
    FormNotRegisteredError,
    NoExecutorsRegisteredError,
    ParamsBuilderNotRegisteredError,
)

if TYPE_CHECKING:
    from interfaces.i_step_executor import IStepExecutor
    from interfaces.i_step_form_def import IStepFormDef
    from interfaces.i_step_params import IStepParams

# -----------------------------------------------------------------------------
# Internal storage
# -----------------------------------------------------------------------------

# Populated at import time by each concrete executor module.
_executors: dict[StepTypeEnum, IStepExecutor] = {}

# Populated at import time by each concrete form-def module.
_forms: dict[StepTypeEnum, IStepFormDef] = {}

# Populated at import time by each per-step presenter module.
_params_builders: dict[StepTypeEnum, Callable[[dict[str, Any]], IStepParams]] = {}

# -----------------------------------------------------------------------------
# Registration helpers (called by concrete classes at module level)
# -----------------------------------------------------------------------------


def register_step_executor(executor: IStepExecutor) -> None:
    """Register an executor instance in the service registry.

    Args:
        executor: Concrete IStepExecutor instance.

    Returns:
        None.

    Raises:
        None.
    """
    _executors[executor.step_type()] = executor


def register_form(form: IStepFormDef) -> None:
    """Register a form-definition instance in the view registry.

    Args:
        form: Concrete IStepFormDef instance.

    Returns:
        None.

    Raises:
        None.
    """
    _forms[form.step_type()] = form


def register_params_builder(step_type: StepTypeEnum, builder: Callable[[dict[str, Any]], IStepParams]) -> None:
    """Register a params-builder callable for the given step type.

    The builder receives the raw ``dict[str, Any]`` stored in JSON and
    returns a fully typed ``IStepParams`` instance.  Called once per step
    type at module import time by the per-step presenter module.

    Args:
        step_type: The StepTypeEnum this builder handles.
        builder: Callable that maps a raw params dict to a typed IStepParams.

    Returns:
        None.

    Raises:
        None.
    """
    _params_builders[step_type] = builder


# -----------------------------------------------------------------------------
# Lookup helpers (called by orchestrators at runtime)
# -----------------------------------------------------------------------------


def get_step_executor(step_type: StepTypeEnum) -> IStepExecutor:
    """Return the registered executor for the given step type.

    Args:
        step_type: The StepTypeEnum to look up.

    Returns:
        The IStepExecutor instance registered for that type.

    Raises:
        NoExecutorsRegisteredError: When the executor registry is empty.
        ExecutorNotRegisteredError: When no executor matches the step type.
    """
    if not _executors:
        raise NoExecutorsRegisteredError()
    executor = _executors.get(step_type)
    if executor is None:
        raise ExecutorNotRegisteredError(step_type)
    return executor


def get_form(step_type: StepTypeEnum) -> IStepFormDef:
    """Return the registered form definition for the given step type.

    Args:
        step_type: The StepTypeEnum to look up.

    Returns:
        The IStepFormDef instance registered for that type.

    Raises:
        FormNotRegisteredError: When no form def has been registered for the type.
    """
    form = _forms.get(step_type)
    if form is None:
        raise FormNotRegisteredError(step_type)
    return form


def build_params(step_type: StepTypeEnum, data: dict[str, Any]) -> IStepParams:
    """Deserialise a raw params dict into a typed IStepParams instance.

    Delegates to the builder registered by the per-step presenter module.
    Must be called after ``presenters.steps`` has been imported.

    Args:
        step_type: The StepTypeEnum identifying the concrete params class.
        data: Raw parameter dict as stored in JSON.

    Returns:
        A fully populated IStepParams instance with named typed properties.

    Raises:
        ParamsBuilderNotRegisteredError: When no builder has been registered
            for the given step type.
    """
    builder = _params_builders.get(step_type)
    if builder is None:
        raise ParamsBuilderNotRegisteredError(step_type)
    return builder(data)


# EOF
