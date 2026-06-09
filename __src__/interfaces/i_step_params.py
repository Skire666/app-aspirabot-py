"""Contract for typed step parameter models."""

from __future__ import annotations

from typing import Any, Protocol, Self

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

    def to_dict(self) -> dict[str, object]:
        """Serialise the params to a JSON-compatible dictionary."""
        ...

    @classmethod
    def model_validate(cls, obj: object, *, context: dict[str, object] | None = None) -> Self:
        """Validate and construct the params model from a dict."""
        ...

    def validate_with_context(self, step_index: int, steps_context: Any, step_id: str) -> list[str]:
        """Validate params in workflow context and return French error strings.

        Returns:
            Empty list when valid; list of error strings otherwise.
        """
        ...


# EOF
