from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime
from queue import Queue
from typing import Any
from uuid import uuid4

from crewai.events import crewai_event_bus
from crewai.events.types.agent_events import (
    AgentExecutionCompletedEvent,
    AgentExecutionErrorEvent,
    AgentExecutionStartedEvent,
)
from crewai.events.types.task_events import (
    TaskCompletedEvent,
    TaskFailedEvent,
    TaskStartedEvent,
)


ROLE_TO_STAGE = {
    "Symptom Analyst": "symptom_analysis",
    "Test Result Interpreter": "test_interpretation",
    "Possible Conditions Reviewer": "possible_conditions_review",
    "Care Guidance Assistant": "care_guidance",
}

EVENT_DETAILS = {
    TaskStartedEvent: ("task", "started"),
    TaskCompletedEvent: ("task", "completed"),
    TaskFailedEvent: ("task", "failed"),
    AgentExecutionStartedEvent: ("agent", "started"),
    AgentExecutionCompletedEvent: ("agent", "completed"),
    AgentExecutionErrorEvent: ("agent", "failed"),
}


class ProgressMessage:
    def __init__(
        self,
        event: str,
        data: dict[str, Any],
        terminal: bool = False,
    ) -> None:
        self.event = event
        self.data = data
        self.terminal = terminal


class ProgressSession:
    def __init__(self) -> None:
        self.request_id = uuid4().hex
        self.messages: Queue[ProgressMessage] = Queue()

    def publish_progress(self, event_data: dict[str, Any]) -> None:
        self.messages.put(
            ProgressMessage(
                event="progress",
                data={"request_id": self.request_id, **event_data},
            )
        )

    def publish_result(self, result: str) -> None:
        self.messages.put(
            ProgressMessage(
                event="result",
                data={"request_id": self.request_id, "result": result},
                terminal=True,
            )
        )

    def publish_failure(self) -> None:
        self.messages.put(
            ProgressMessage(
                event="failed",
                data={
                    "request_id": self.request_id,
                    "message": "The analysis could not be completed. Please try again later.",
                },
                terminal=True,
            )
        )


active_progress_session: ContextVar[ProgressSession | None] = ContextVar(
    "active_progress_session",
    default=None,
)


def map_crewai_event(event: Any) -> dict[str, str] | None:
    event_details = EVENT_DETAILS.get(type(event))
    if event_details is None:
        return None

    component, status = event_details
    if component == "agent":
        role = getattr(getattr(event, "agent", None), "role", None)
    else:
        role = getattr(
            getattr(getattr(event, "task", None), "agent", None),
            "role",
            None,
        )

    stage_id = ROLE_TO_STAGE.get(role)
    timestamp = getattr(event, "timestamp", None)
    if stage_id is None or not isinstance(timestamp, datetime):
        return None

    return {
        "component": component,
        "stage_id": stage_id,
        "role": role,
        "status": status,
        "timestamp": timestamp.isoformat(),
    }


def capture_crewai_event(event: Any) -> None:
    session = active_progress_session.get()
    if session is None:
        return

    event_data = map_crewai_event(event)
    if event_data is not None:
        session.publish_progress(event_data)


def _register_handler(event_type: type[Any]) -> None:
    def handler(_source: Any, event: Any) -> None:
        capture_crewai_event(event)

    handler.__name__ = f"capture_{event_type.__name__}"
    crewai_event_bus.on(event_type)(handler)


for _event_type in EVENT_DETAILS:
    _register_handler(_event_type)
