"""FluentValidation-inspired base validator infrastructure.

Usage::

    class MyValidator(AbstractValidator[MyModel]):
        def __init__(self) -> None:
            super().__init__()
            self.rule_for(lambda m: m.name, "name").not_empty(MSG_NAME_REQUIRED)
            self.rule_for(lambda m: m.value, "value").must(
                lambda v: v > 0, MSG_VALUE_POSITIVE
            ).when(lambda m: m.has_value)

    result = MyValidator().validate(instance)
    if not result.is_valid:
        view.show_errors(list(result.errors))
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")
V = TypeVar("V")

# -----------------------------------------------------------------------------
# ValidationResult
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of a validate() call.

    Attributes:
        errors: Ordered tuple of French error messages, ready for display.
    """

    errors: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_valid(self) -> bool:
        """True when no errors were produced."""
        return not self.errors

    @property
    def first_error(self) -> str | None:
        """First error message, or None when valid."""
        return self.errors[0] if self.errors else None


# -----------------------------------------------------------------------------
# _Rule — internal
# -----------------------------------------------------------------------------


class _Rule(Generic[T, V]):
    """A single validation predicate with an optional guard condition."""

    def __init__(
        self, predicate: Callable[[V], bool], message: str, condition: Callable[[T], bool] | None = None
    ) -> None:
        self._predicate = predicate
        self._message = message
        self._condition = condition

    def with_condition(self, condition: Callable[[T], bool]) -> _Rule[T, V]:
        """Return a copy of this rule bound to *condition*.

        Args:
            condition: Guard predicate evaluated on the full instance.

        Returns:
            A new _Rule with the condition applied.
        """
        return _Rule(self._predicate, self._message, condition)

    def evaluate(self, instance: T, value: V) -> str | None:
        """Apply this rule; return the error message or None when passing.

        Args:
            instance: Full object being validated (used by the guard condition).
            value: Field value extracted by the accessor.

        Returns:
            Error message string, or None when the rule passes or is skipped.
        """
        if self._condition is not None and not self._condition(instance):
            return None
        return None if self._predicate(value) else self._message


# -----------------------------------------------------------------------------
# RuleBuilder
# -----------------------------------------------------------------------------


class RuleBuilder(Generic[T, V]):
    """Fluent builder that accumulates validation rules for a single field.

    Chain predicates via .not_empty(), .must(), etc., then optionally guard
    the last rule with .when() or override its message with .with_message().

    Example::

        self.rule_for(lambda m: m.name, "name")
            .not_empty(MSG_REQUIRED)
            .must(lambda v: len(v) <= 50, MSG_TOO_LONG)
            .when(lambda m: m.is_active)
    """

    def __init__(self, accessor: Callable[[T], V], field_name: str) -> None:
        """Initialize the builder for a single field.

        Args:
            accessor: Lambda extracting the field value from an instance.
            field_name: Descriptive name used for context (not in messages).
        """
        self._accessor = accessor
        self._field_name = field_name
        self._rules: list[_Rule] = []

    # ── Rule factories ────────────────────────────────────────────────

    def not_empty(self, message: str = "La valeur ne peut pas être vide.") -> RuleBuilder[T, V]:
        """Fail when the value is None, empty string, or whitespace only.

        Args:
            message: French error message displayed when the rule fails.

        Returns:
            This builder, for further chaining.
        """

        def _check(v: object) -> bool:
            if isinstance(v, str):
                return bool(v.strip())
            return v is not None and bool(v)

        return self._add(_check, message)

    def not_equal(self, other: V, message: str = "La valeur n'est pas autorisée.") -> RuleBuilder[T, V]:
        """Fail when the value equals *other*.

        Args:
            other: The forbidden value.
            message: French error message displayed when the rule fails.

        Returns:
            This builder, for further chaining.
        """
        return self._add(lambda v: v != other, message)

    def must(self, predicate: Callable[[V], bool], message: str = "La valeur est invalide.") -> RuleBuilder[T, V]:
        """Fail when *predicate(value)* returns False.

        Args:
            predicate: Custom validation function applied to the field value.
            message: French error message displayed when the rule fails.

        Returns:
            This builder, for further chaining.
        """
        return self._add(predicate, message)

    # ── Modifiers ─────────────────────────────────────────────────────

    def when(self, condition: Callable[[T], bool]) -> RuleBuilder[T, V]:
        """Guard the last registered rule with *condition*.

        When *condition(instance)* returns False the rule is skipped entirely
        — no error is produced even if the predicate would have failed.

        Args:
            condition: Predicate evaluated against the whole instance (not just
                the field value), allowing cross-field guards.

        Returns:
            This builder, for further chaining.
        """
        if self._rules:
            self._rules[-1] = self._rules[-1].with_condition(condition)
        return self

    def with_message(self, message: str) -> RuleBuilder[T, V]:
        """Override the message on the last registered rule.

        Args:
            message: Replacement French error message.

        Returns:
            This builder, for further chaining.
        """
        if self._rules:
            last = self._rules[-1]
            self._rules[-1] = _Rule(last._predicate, message, last._condition)
        return self

    # ── Internal ──────────────────────────────────────────────────────

    def _add(self, predicate: Callable[[V], bool], message: str) -> RuleBuilder[T, V]:
        self._rules.append(_Rule(predicate, message))
        return self

    def _evaluate_all(self, instance: T) -> list[str]:
        """Collect error messages for all failing rules on this field.

        Args:
            instance: The full object being validated.

        Returns:
            List of error message strings (may be empty).
        """
        value = self._accessor(instance)
        return [msg for rule in self._rules if (msg := rule.evaluate(instance, value)) is not None]


# -----------------------------------------------------------------------------
# AbstractValidator
# -----------------------------------------------------------------------------


class AbstractValidator(Generic[T]):
    """Base class for FluentValidation-style domain validators.

    Subclasses define rules in ``__init__`` using ``self.rule_for(...)``.
    ``validate()`` runs all rules and collects every error message into a
    ``ValidationResult``.

    Rules are evaluated in declaration order. All rules run regardless of
    earlier failures (full validation — not fail-fast). Use ``result.first_error``
    when only the first message is needed for display.
    """

    def __init__(self) -> None:
        """Initialize the validator with an empty rule set."""
        self._builders: list[RuleBuilder] = []

    def rule_for(self, accessor: Callable[[T], V], field_name: str = "") -> RuleBuilder[T, V]:
        """Register a rule chain for the field returned by *accessor*.

        Args:
            accessor: Lambda extracting the field value from an instance.
            field_name: Optional descriptive name for context.

        Returns:
            A ``RuleBuilder`` for chaining validation predicates on this field.
        """
        builder: RuleBuilder[T, V] = RuleBuilder(accessor, field_name)
        self._builders.append(builder)
        return builder

    def validate(self, instance: T) -> ValidationResult:
        """Run all registered rules against *instance*.

        All rules run even when earlier ones fail, so the result may contain
        multiple errors. Use ``result.first_error`` for single-message display.

        Args:
            instance: The object to validate.

        Returns:
            A ``ValidationResult`` collecting all error messages.
        """
        errors: list[str] = []
        for builder in self._builders:
            errors.extend(builder._evaluate_all(instance))
        return ValidationResult(errors=tuple(errors))


# EOF
