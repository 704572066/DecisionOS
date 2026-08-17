"""Manual integration smoke test for Dialogue v1.2.

Run inside the backend container after replacing src files.
"""
import asyncio

from app.reasoning import reasoning_service
from app.runtime.models import RuntimeState


async def main():
    state = RuntimeState(
        meetingId="meeting-shared-test",
        projectId="project-test",
        contextId="context-shared-test",
        objective="test",
    )

    first = await reasoning_service.get_or_reason(state)
    second = await reasoning_service.get_or_reason(state)

    print("same object:", first is second)
    print("same result:", first.model_dump(mode="json") == second.model_dump(mode="json"))

    state.updatedAt = state.updatedAt.replace(microsecond=(state.updatedAt.microsecond + 1) % 1000000)
    third = await reasoning_service.get_or_reason(state)
    print("new runtime revision recomputed:", third is not second)


asyncio.run(main())
