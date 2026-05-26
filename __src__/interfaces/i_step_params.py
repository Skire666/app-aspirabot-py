"""Contract for typed step parameter models.

Every concrete step exposes a frozen dataclass that implements this interface.
The dataclass documents all parameters explicitly and provides safe
serialisation to and from the raw ``dict[str, Any]`` used in JSON storage.

Example:
    >>> params = WaitElementParams.default()
    >>> params.to_dict()["selector"]
    ''
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from typing import Any, Protocol, Self

from shared.enums import StepTypeEnum

# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------


class IStepParams(Protocol):
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
    def default(cls) -> Self:
        """Return a new instance populated with default parameter values.

        Returns:
            A default-initialised params instance.
        """
        ...

    def to_dict(self) -> dict[str, Any]:
        """Serialise the params to a JSON-compatible dictionary.

        Returns:
            A plain dict mirroring the JSON storage format.
        """
        ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialise params from a raw dictionary.

        Args:
            data: Raw parameter dict as stored in JSON.

        Returns:
            A fully populated params instance; missing keys fall back to defaults.
        """
        ...

    @classmethod
    def get_step_type(cls) -> StepTypeEnum:
        """Return the step type string associated with these parameters.

        Returns:
            The StepType value corresponding to these params.
        """
        ...
