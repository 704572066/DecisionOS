from __future__ import annotations

import calendar
import re
from datetime import date, datetime

from app.core.config import settings
from app.runtime.semantic_models import SemanticEventCandidate
from app.runtime.semantic_policy import semantic_policy



class SemanticEventValidator:


    DEFAULT_CONFIDENCE = 0.72
    MAX_EVENTS = 8



    def validate(
        self,
        events:list[SemanticEventCandidate],
        *,
        source_text:str,
        meeting_date:datetime | date | None=None,
    ):

        source = " ".join(
            (source_text or "").split()
        )


        output=[]
        seen=set()


        min_confidence=float(
            getattr(
                settings,
                "semantic_event_min_confidence",
                self.DEFAULT_CONFIDENCE,
            )
        )


        for event in events or []:


            if len(output)>=self.MAX_EVENTS:
                break


            if event.confidence < min_confidence:
                continue



            candidate=event.model_copy(
                deep=True
            )


            candidate.sourceText = (
                " ".join(
                    (
                        candidate.sourceText
                        or source
                    ).split()
                )
            )


            candidate.role = (
                semantic_policy
                .normalize_role(candidate)
            )


            candidate.actor = (
                semantic_policy
                .normalize_actor(
                    candidate.actor
                )
            )


            if not self._valid(candidate):
                continue



            key=(
                candidate.domain,
                candidate.field,
                candidate.target,
                candidate.actor,
                candidate.role,
                candidate.normalizedValue,
            )


            if key in seen:
                continue


            seen.add(key)
            output.append(candidate)



        return output



    @staticmethod
    def _valid(event):


        if event.actor not in {
            "customer",
            "us",
            "third_party",
            "unknown",
        }:
            return False



        if event.domain=="commercial":


            if event.field in {
                "discountPercent",
                "priceReduction",
            }:

                value=event.normalizedValue

                if not isinstance(
                    value,
                    (int,float)
                ):
                    return False


        return True



semantic_event_validator = SemanticEventValidator()