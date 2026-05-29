"""Contract for typed step parameter models.

Every concrete step exposes a frozen dataclass that implements this interface.
The dataclass documents all parameters explicitly via named typed fields and
provides safe serialisation to the raw ``dict[str, Any]`` used in JSON storage.
Deserialisation is handled by per-step builder functions registered in the step registry.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from typing import Any, Protocol

# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------


class IStepParams(Protocol):
    """Contract for typed, serialisable step parameter objects.

    Each concrete step type owns exactly one implementation of this class,
    named ``<StepName>Params``.  Instances expose all parameters as named
    typed properties and provide round-trip serialisation via ``to_dict()``.
    Deserialisation from raw dicts is handled by the per-step builder functions
    registered in the step registry via ``register_params_builder``.
    """

    def to_dict(self) -> dict[str, Any]:
        """Serialise the params to a JSON-compatible dictionary.

        Returns:
            A plain dict mirroring the JSON storage format.
        """
        ...
