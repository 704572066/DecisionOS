from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.reasoning.context import EvaluationConstraint


@dataclass
class ConstraintValidationResult:
    valid: bool
    constraint: EvaluationConstraint | None = None
    errors: list[str] = field(default_factory=list)


class ConstraintValidator:
    """
    Validation boundary between Constraint Compiler and Generic Evaluator.

    Responsibilities:
    - reject structurally invalid constraints
    - reject incomplete relational constraints
    - enforce generic consistency rules

    Non-responsibilities:
    - understand enterprise/business semantics
    - interpret natural-language policies
    - contain domain-specific thresholds
    """

    RELATIONAL_OPERATORS = {
        "requires",
        "depends_on",
        "conflicts_with",
    }

    VALUE_OPERATORS = {
        "=",
        "!=",
        ">",
        ">=",
        "<",
        "<=",
        "in",
        "not_in",
    }

    EXISTENCE_OPERATORS = {
        "exists",
        "missing",
    }

    def validate(
        self,
        constraint: EvaluationConstraint,
    ) -> ConstraintValidationResult:
        errors: list[str] = []

        self._validate_identity(constraint, errors)
        self._validate_subject(constraint, errors)
        self._validate_operator(constraint, errors)
        self._validate_operand(constraint, errors)

        return ConstraintValidationResult(
            valid=not errors,
            constraint=constraint if not errors else None,
            errors=errors,
        )

    def validate_many(
        self,
        constraints: list[EvaluationConstraint],
    ) -> tuple[list[EvaluationConstraint], list[dict[str, Any]]]:
        valid_constraints: list[EvaluationConstraint] = []
        rejected: list[dict[str, Any]] = []

        seen_ids: set[str] = set()

        for constraint in constraints:
            result = self.validate(constraint)

            if constraint.id in seen_ids:
                result.valid = False
                result.constraint = None
                result.errors.append(
                    f"duplicate constraint id: {constraint.id}"
                )

            seen_ids.add(constraint.id)

            if result.valid and result.constraint is not None:
                valid_constraints.append(result.constraint)
            else:
                rejected.append(
                    {
                        "id": constraint.id,
                        "errors": result.errors,
                    }
                )

        return valid_constraints, rejected

    def _validate_identity(
        self,
        constraint: EvaluationConstraint,
        errors: list[str],
    ) -> None:
        if not constraint.id.strip():
            errors.append("constraint id must not be empty")

    def _validate_subject(
        self,
        constraint: EvaluationConstraint,
        errors: list[str],
    ) -> None:
        if not constraint.subject.strip():
            errors.append("constraint subject must not be empty")

    def _validate_operator(
        self,
        constraint: EvaluationConstraint,
        errors: list[str],
    ) -> None:
        operator = constraint.operator

        if (
            operator in self.VALUE_OPERATORS
            and constraint.expectedValue is None
        ):
            errors.append(
                f"operator '{operator}' requires expectedValue"
            )

        if (
            operator in self.EXISTENCE_OPERATORS
            and constraint.expectedValue is not None
        ):
            errors.append(
                f"operator '{operator}' must not define expectedValue"
            )

    def _validate_operand(
        self,
        constraint: EvaluationConstraint,
        errors: list[str],
    ) -> None:
        operator = constraint.operator

        if operator in self.RELATIONAL_OPERATORS:
            if constraint.operand is None:
                errors.append(
                    f"operator '{operator}' requires operand"
                )
                return

        operand = constraint.operand

        if operand is None:
            return

        if not operand.subject.strip():
            errors.append("operand subject must not be empty")

        if (
            operand.operator in self.VALUE_OPERATORS
            and operand.expectedValue is None
        ):
            errors.append(
                f"operand operator '{operand.operator}' "
                "requires expectedValue"
            )

        if (
            operand.operator in self.EXISTENCE_OPERATORS
            and operand.expectedValue is not None
        ):
            errors.append(
                f"operand operator '{operand.operator}' "
                "must not define expectedValue"
            )


constraint_validator = ConstraintValidator()