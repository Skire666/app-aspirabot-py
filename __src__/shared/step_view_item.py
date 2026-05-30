"""View-safe snapshot of a workflow step for the DragDropList renderer.

Owned by the view layer.  Built by the Presenter from a StepScrapingModel
before any rendering call.  Contains only stdlib and shared-layer types —
no domain models, no Tkinter.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from shared.enums import StepTypeEnum

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class StepViewItem:
    """Immutable, view-safe representation of one workflow step.

    Created once per render pass by StepsListPresenter._build_view_items().
    The Presenter maps StepScrapingModel → StepViewItem before any call to
    IStepsListCrudView or IStepsListGestionView, keeping domain models out of
    the view layer entirely.

    Attributes:
        step_id: Stable unique identifier of the step.
        step_type: Enum member used to look up the registered IStepFormDef.
        is_active: Whether the step is enabled during execution.
        modified_date: Timestamp of the last modification.
        params_dict: Serialised parameter snapshot (from IStepParams.to_dict()).
            Passed directly to IStepFormDef.load_params_step_to_widget() so
            that method never touches a domain model.
        label: Pre-computed French display label for the DragDropList renderer.
            Built by StepsListPresenter using step_label_formatters — the View
            reads it directly without any conditional logic.
    """

    step_id: str
    step_type: StepTypeEnum
    is_active: bool
    modified_date: datetime
    params_dict: dict[str, Any]
    label: str


# EOF
