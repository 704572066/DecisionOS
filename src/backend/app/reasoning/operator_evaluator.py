from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.reasoning.context import (
    ConstraintOperator,
    EvaluationSubject,
)


@dataclass
class OperatorEvaluationResult:
    """
    Result of evaluating one operator against one or more subjects.

    matched:
        Whether the operator condition matched.

    comparable:
        Whether the supplied values could be meaningfully evaluated.

        Example:
            actual="abc"
            operator=">"
            expected=10

        comparable=False

    matchedSubjects:
        Subjects that individually matched the condition.

    unmatchedSubjects:
        Subjects that were comparable but did not match.

    ignoredSubjects:
        Subjects excluded because they were not comparable.
    """

    operator: ConstraintOperator

    expectedValue: Any = None

    matched: bool = False

    comparable: bool = True

    matchedSubjects: list[EvaluationSubject] = field(
        default_factory=list
    )

    unmatchedSubjects: list[EvaluationSubject] = field(
        default_factory=list
    )

    ignoredSubjects: list[EvaluationSubject] = field(
        default_factory=list
    )

    diagnostics: dict[str, Any] = field(
        default_factory=dict
    )


class OperatorEvaluator:
    """
    Generic DSL operator evaluator.

    It knows NOTHING about business fields.

    It only understands:

        =
        !=
        >
        >=
        <
        <=
        in
        not_in
        exists
        missing

    Relational operators such as:

        requires
        depends_on
        conflicts_with

    are intentionally NOT evaluated here.

    They are orchestration semantics handled later by
    ConstraintEvaluator.
    """

    SIMPLE_OPERATORS = {
        "=",
        "!=",
        ">",
        ">=",
        "<",
        "<=",
        "in",
        "not_in",
        "exists",
        "missing",
    }

    def evaluate(
        self,
        subjects: list[EvaluationSubject],
        *,
        operator: ConstraintOperator,
        expected_value: Any = None,
    ) -> OperatorEvaluationResult:
        if operator not in self.SIMPLE_OPERATORS:
            return OperatorEvaluationResult(
                operator=operator,
                expectedValue=expected_value,
                matched=False,
                comparable=False,
                diagnostics={
                    "reason": (
                        "operator_not_supported_by_simple_evaluator"
                    )
                },
            )

        if operator == "exists":
            return self._evaluate_exists(
                subjects,
            )

        if operator == "missing":
            return self._evaluate_missing(
                subjects,
            )

        result = OperatorEvaluationResult(
            operator=operator,
            expectedValue=expected_value,
        )

        for subject in subjects:
            comparable, matched = (
                self._evaluate_value(
                    actual=subject.value,
                    operator=operator,
                    expected=expected_value,
                )
            )

            if not comparable:
                result.ignoredSubjects.append(
                    subject
                )
                continue

            if matched:
                result.matchedSubjects.append(
                    subject
                )
            else:
                result.unmatchedSubjects.append(
                    subject
                )

        #
        # Multi-subject semantics:
        #
        # A condition is considered matched when ANY comparable
        # subject satisfies it.
        #
        # Example:
        #
        # semanticSubjects:
        #   customer discount=10
        #   us discount=15 rejected
        #
        # operator >
        # expected 10
        #
        # matched=True because one subject has value=15.
        #
        # Whether rejected/withdrawn subjects should participate is
        # NOT decided here. That belongs to the ConstraintEvaluator
        # / subject-selection layer.
        #
        result.matched = bool(
            result.matchedSubjects
        )

        comparable_count = (
            len(result.matchedSubjects)
            + len(result.unmatchedSubjects)
        )

        result.comparable = (
            comparable_count > 0
        )

        result.diagnostics = {
            "subjectCount": len(subjects),
            "matchedCount": len(
                result.matchedSubjects
            ),
            "unmatchedCount": len(
                result.unmatchedSubjects
            ),
            "ignoredCount": len(
                result.ignoredSubjects
            ),
        }

        return result

    @staticmethod
    def _evaluate_exists(
        subjects: list[EvaluationSubject],
    ) -> OperatorEvaluationResult:
        #
        # Existence means that at least one subject exists.
        #
        return OperatorEvaluationResult(
            operator="exists",
            expectedValue=None,
            matched=bool(subjects),
            comparable=True,
            matchedSubjects=list(subjects),
            diagnostics={
                "subjectCount": len(subjects),
            },
        )

    @staticmethod
    def _evaluate_missing(
        subjects: list[EvaluationSubject],
    ) -> OperatorEvaluationResult:
        #
        # Missing means no matching subject exists.
        #
        return OperatorEvaluationResult(
            operator="missing",
            expectedValue=None,
            matched=not bool(subjects),
            comparable=True,
            unmatchedSubjects=list(subjects),
            diagnostics={
                "subjectCount": len(subjects),
            },
        )

    def _evaluate_value(
        self,
        *,
        actual: Any,
        operator: ConstraintOperator,
        expected: Any,
    ) -> tuple[bool, bool]:
        """
        Returns:

            comparable, matched
        """

        if operator == "=":
            return (
                True,
                self._equal(
                    actual,
                    expected,
                ),
            )

        if operator == "!=":
            return (
                True,
                not self._equal(
                    actual,
                    expected,
                ),
            )

        if operator in {
            ">",
            ">=",
            "<",
            "<=",
        }:
            return self._compare_ordered(
                actual=actual,
                expected=expected,
                operator=operator,
            )

        if operator == "in":
            return self._evaluate_in(
                actual,
                expected,
            )

        if operator == "not_in":
            comparable, matched = (
                self._evaluate_in(
                    actual,
                    expected,
                )
            )

            if not comparable:
                return False, False

            return True, not matched

        return False, False

    @staticmethod
    def _equal(
        actual: Any,
        expected: Any,
    ) -> bool:
        #
        # Preserve native equality first.
        #
        if actual == expected:
            return True

        #
        # Numeric normalization:
        #
        # 10 == 10.0
        # "10" == 10
        #
        actual_number = (
            OperatorEvaluator._number(
                actual
            )
        )

        expected_number = (
            OperatorEvaluator._number(
                expected
            )
        )

        if (
            actual_number is not None
            and expected_number is not None
        ):
            return (
                actual_number
                == expected_number
            )

        return False

    @staticmethod
    def _compare_ordered(
        *,
        actual: Any,
        expected: Any,
        operator: str,
    ) -> tuple[bool, bool]:
        actual_number = (
            OperatorEvaluator._number(
                actual
            )
        )

        expected_number = (
            OperatorEvaluator._number(
                expected
            )
        )

        #
        # First support generic numeric comparison.
        #
        if (
            actual_number is not None
            and expected_number is not None
        ):
            if operator == ">":
                return (
                    True,
                    actual_number
                    > expected_number,
                )

            if operator == ">=":
                return (
                    True,
                    actual_number
                    >= expected_number,
                )

            if operator == "<":
                return (
                    True,
                    actual_number
                    < expected_number,
                )

            if operator == "<=":
                return (
                    True,
                    actual_number
                    <= expected_number,
                )

        #
        # Do NOT perform arbitrary lexical ordering for strings.
        #
        # Example:
        #
        # "high" > "medium"
        #
        # would technically work in Python but has no generic
        # semantic meaning.
        #
        return False, False

    @staticmethod
    def _evaluate_in(
        actual: Any,
        expected: Any,
    ) -> tuple[bool, bool]:
        #
        # "in" expects the RHS to be an explicit collection.
        #
        if not isinstance(
            expected,
            (
                list,
                tuple,
                set,
                frozenset,
            ),
        ):
            return False, False

        for item in expected:
            if OperatorEvaluator._equal(
                actual,
                item,
            ):
                return True, True

        return True, False

    @staticmethod
    def _number(
        value: Any,
    ) -> float | None:
        #
        # bool is technically int in Python.
        # Do not silently treat True as 1.
        #
        if isinstance(
            value,
            bool,
        ):
            return None

        if isinstance(
            value,
            (int, float),
        ):
            return float(value)

        if isinstance(
            value,
            str,
        ):
            text = value.strip()

            if not text:
                return None

            try:
                return float(text)
            except ValueError:
                return None

        return None


operator_evaluator = OperatorEvaluator()