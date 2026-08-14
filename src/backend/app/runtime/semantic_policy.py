from __future__ import annotations

from enum import Enum
from typing import Any


class SemanticRole(str, Enum):
    ACCEPTANCE = "acceptance"
    COMMITMENT = "commitment"
    PROPOSAL = "proposal"
    DEPENDENCY = "dependency"
    REQUIREMENT = "requirement"
    ASSESSMENT = "assessment"
    LIABILITY = "liability"
    UNKNOWN = "unknown"


class SemanticActor(str, Enum):
    CUSTOMER = "customer"
    US = "us"
    THIRD_PARTY = "third_party"
    UNKNOWN = "unknown"


class SemanticPolicy:
    """
    Central semantic governance policy.

    Responsible for:
    - role normalization
    - actor normalization
    - semantic priority
    - decision effectiveness
    """

    ROLE_PRIORITY = {
        SemanticRole.ACCEPTANCE.value: 60,
        SemanticRole.COMMITMENT.value: 55,
        SemanticRole.PROPOSAL.value: 40,
        SemanticRole.DEPENDENCY.value: 35,
        SemanticRole.REQUIREMENT.value: 20,
        SemanticRole.ASSESSMENT.value: 10,
        SemanticRole.LIABILITY.value: 10,
        SemanticRole.UNKNOWN.value: 0,
    }


    STATUS_PRIORITY = {
        "confirmed": 100,
        "accepted": 90,
        "active": 80,
        "pending": 40,
        "proposed": 20,
        "withdrawn": -100,
        "rejected": -100,
    }


    DECISION_ROLES = {
        SemanticRole.ACCEPTANCE.value,
        SemanticRole.COMMITMENT.value,
        SemanticRole.PROPOSAL.value,
    }


    RUNTIME_CONSTRAINT_ROLES = {
        SemanticRole.ACCEPTANCE.value,
        SemanticRole.COMMITMENT.value,
        SemanticRole.PROPOSAL.value,
        SemanticRole.DEPENDENCY.value,
        SemanticRole.LIABILITY.value,
    }


    @classmethod
    def normalize_role(
        cls,
        event: Any,
    ) -> str:

        role = (
            getattr(event, "role", None)
            or ""
        ).lower().strip()


        if role in {
            item.value
            for item in SemanticRole
        }:
            return role


        kind = (
            getattr(event, "kind", "")
            or ""
        )


        status = (
            getattr(event, "status", "")
            or ""
        )


        if kind == "dependency":
            return SemanticRole.DEPENDENCY.value


        if kind == "commitment":
            return SemanticRole.COMMITMENT.value


        if status == "accepted":
            return SemanticRole.ACCEPTANCE.value


        if status == "proposed":
            return SemanticRole.PROPOSAL.value


        return SemanticRole.UNKNOWN.value



    @classmethod
    def normalize_actor(
        cls,
        actor: str | None,
    ) -> str:

        value = (
            actor or ""
        ).strip().lower()


        mapping = {

            "customer":
            SemanticActor.CUSTOMER.value,

            "客户":
            SemanticActor.CUSTOMER.value,

            "客户方":
            SemanticActor.CUSTOMER.value,


            "we":
            SemanticActor.US.value,

            "us":
            SemanticActor.US.value,

            "我方":
            SemanticActor.US.value,

            "我们":
            SemanticActor.US.value,


            "third_party":
            SemanticActor.THIRD_PARTY.value,


            "第三方":
            SemanticActor.THIRD_PARTY.value,

        }


        return mapping.get(
            value,
            SemanticActor.UNKNOWN.value,
        )



    @classmethod
    def is_decision_effective(
        cls,
        item: dict,
    ) -> bool:

        if item.get("status") in {
            "withdrawn",
            "rejected",
        }:
            return False


        return (
            item.get("role")
            in cls.DECISION_ROLES
        )



    @classmethod
    def is_runtime_constraint_effective(
        cls,
        item: dict,
    ) -> bool:

        if item.get("status") in {
            "withdrawn",
            "rejected",
        }:
            return False


        return (
            item.get("role")
            in cls.RUNTIME_CONSTRAINT_ROLES
        )



    @classmethod
    def semantic_score(
        cls,
        item:dict,
    ) -> int:

        return (
            cls.ROLE_PRIORITY.get(
                item.get("role"),
                0
            )
            +
            cls.STATUS_PRIORITY.get(
                item.get("status"),
                0
            )
        )


semantic_policy = SemanticPolicy()