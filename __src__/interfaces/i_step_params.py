"""Contract for typed step parameter models.

Every concrete step exposes a frozen dataclass that implements this interface.
The dataclass documents all parameters explicitly and provides safe
serialisation to and from the raw ``dict[str, Any]`` used in JSON storage.

Example:
    >>> params = WaitElementParams.default()
    >>> params.to_dict()["selector"]
    ''
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from abc import ABC, abstractmethod
from typing import Any, Self

from models.step_scraping_model import StepType

## ---------------------------------------------------------------------------
## Interface
## ---------------------------------------------------------------------------


class IStepParams(ABC):
    """Contract for typed, serialisable step parameter objects.

    Each concrete step type owns exactly one implementation of this class,
    named ``<StepName>Params``.  The instance is used internally within the
    executor and form-definition layers; the public API still exchanges plain
    ``dict[str, Any]`` for JSON compatibility.

    Example:
        >>> params = ConcreteParams.default()
        >>> roundtrip = ConcreteParams.from_dict(params.to_dict())
        >>> roundtrip == params
        True
    """

    @classmethod
    @abstractmethod
    def default(cls) -> Self:
        """Returns a new instance populated with default parameter values.

        Returns:
            A default-initialised params instance.

        Raises:
            None.
        """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialises the params to a JSON-compatible dictionary.

        Returns:
            A plain dict mirroring the JSON storage format.

        Raises:
            None.
        """

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialises params from a raw dictionary.

        Args:
            data: Raw parameter dict as stored in JSON.

        Returns:
            A fully populated params instance.

        Raises:
            None — missing keys fall back to defaults.
        """

    @classmethod
    @abstractmethod
    def get_step_type(cls) -> StepType:
        """Returns the step type string associated with these parameters.

        This is used to link the params instance to its step type and form
        definition.

        Returns:
            The StepType value string corresponding to these params.
        """
