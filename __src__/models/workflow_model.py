"""Domain model for a provider's scraping workflow.

This module defines WorkflowModel, a pure data container that holds
an ordered list of scraping steps associated with a specific provider.

Example:
    >>> from models.step_scrapping_model import StepScrappingModel, StepType
    >>> step = StepScrappingModel.create_default(StepType.OPEN_URL)
    >>> workflow = WorkflowModel(provider_id_file="abc", steps=[step])
    >>> len(workflow.steps)
    1
"""

from dataclasses import dataclass, field

from models.step_scrapping_model import StepScrappingModel


@dataclass
class WorkflowModel:
    """Represents an ordered list of scraping steps attached to a provider.

    This is a pure data entity with no business logic or persistence concerns.

    Attributes:
        provider_id_file: The GUID of the provider this workflow belongs to.
        steps: Ordered list of scraping actions to execute.

    Example:
        >>> workflow = WorkflowModel(provider_id_file="some-guid")
        >>> workflow.steps
        []
    """

    provider_id_file: str
    steps: list[StepScrappingModel] = field(default_factory=list)
