import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from datetime import datetime, timezone

from fastapi.testclient import TestClient

import main
from agents import symptom_analyst
from tasks import symptom_analysis_task
from workflow_progress import (
    ProgressSession,
    active_progress_session,
    capture_crewai_event,
    map_crewai_event,
)
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


def make_event(event_type, **fields):
    return event_type.model_construct(
        timestamp=datetime.now(timezone.utc),
        **fields,
    )


class WorkflowProgressTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_frontend_has_workflow_progress_area_and_uses_progress_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="workflowProgress"', response.text)
        self.assertIn('data-stage="symptom_analysis"', response.text)
        self.assertIn('data-stage="test_interpretation"', response.text)
        self.assertIn('data-stage="possible_conditions_review"', response.text)
        self.assertIn('data-stage="care_guidance"', response.text)
        self.assertIn("fetch('/api/analyze/progress'", response.text)
        self.assertIn("eventName === 'progress'", response.text)
        self.assertIn("eventName === 'result'", response.text)
        self.assertIn("eventName === 'failed'", response.text)

    def capture_for_session(self, session, event):
        token = active_progress_session.set(session)
        try:
            context = copy_context()
        finally:
            active_progress_session.reset(token)
        context.run(capture_crewai_event, event)

    def test_maps_task_and_agent_lifecycle_without_sensitive_fields(self):
        task_event = make_event(
            TaskStartedEvent,
            task=symptom_analysis_task,
            context="private symptom details",
        )
        task_completed_event = make_event(
            TaskCompletedEvent,
            task=symptom_analysis_task,
            output="private medical response",
        )
        agent_event = make_event(
            AgentExecutionStartedEvent,
            agent=symptom_analyst,
            task=symptom_analysis_task,
            task_prompt="private prompt",
        )
        completed_event = make_event(
            AgentExecutionCompletedEvent,
            agent=symptom_analyst,
            task=symptom_analysis_task,
            output="private medical response",
        )
        agent_error_event = make_event(
            AgentExecutionErrorEvent,
            agent=symptom_analyst,
            task=symptom_analysis_task,
            error="private prompt and provider details",
        )

        self.assertEqual(
            map_crewai_event(task_event),
            {
                "component": "task",
                "stage_id": "symptom_analysis",
                "role": "Symptom Analyst",
                "status": "started",
                "timestamp": task_event.timestamp.isoformat(),
            },
        )
        self.assertEqual(map_crewai_event(task_completed_event)["status"], "completed")
        self.assertEqual(map_crewai_event(agent_event)["status"], "started")
        completed = map_crewai_event(completed_event)
        self.assertEqual(completed["status"], "completed")
        self.assertNotIn("output", completed)
        self.assertNotIn("task_prompt", completed)
        self.assertEqual(map_crewai_event(agent_error_event)["status"], "failed")

    def test_request_context_associates_concurrent_events_with_their_request(self):
        sessions = [ProgressSession(), ProgressSession()]
        events = [
            make_event(TaskStartedEvent, task=symptom_analysis_task, context=None)
            for _ in sessions
        ]

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(self.capture_for_session, session, event)
                for session, event in zip(sessions, events)
            ]
            for future in futures:
                future.result(timeout=5)

        messages = [
            session.messages.get_nowait()
            for session in sessions
        ]
        self.assertNotEqual(sessions[0].request_id, sessions[1].request_id)
        self.assertEqual(
            [message.data["request_id"] for message in messages],
            [session.request_id for session in sessions],
        )
        self.assertTrue(
            all(message.data["stage_id"] == "symptom_analysis" for message in messages)
        )

    def test_task_failure_is_mapped_without_error_details(self):
        session = ProgressSession()
        event = make_event(
            TaskFailedEvent,
            task=symptom_analysis_task,
            error="private symptoms and provider details",
        )

        token = active_progress_session.set(session)
        try:
            capture_crewai_event(event)
        finally:
            active_progress_session.reset(token)
        message = session.messages.get_nowait()

        self.assertEqual(message.data["status"], "failed")
        self.assertNotIn("error", message.data)
        self.assertNotIn("private", json.dumps(message.data))

    def test_progress_endpoint_streams_result_separately_and_preserves_json_api(self):
        class Workflow:
            async def kickoff_async(self, inputs):
                capture_crewai_event(
                    make_event(
                        TaskStartedEvent,
                        task=symptom_analysis_task,
                        context=None,
                    )
                )
                return "Sample analysis"

        original_workflow = main.medical_crew
        main.medical_crew = Workflow()
        try:
            response = self.client.post(
                "/api/analyze",
                json={"symptoms": "A symptom", "test_results": ""},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"result": "Sample analysis"})

            with self.client.stream(
                "POST",
                "/api/analyze/progress",
                json={"symptoms": "A symptom", "test_results": ""},
            ) as stream_response:
                body = "".join(stream_response.iter_text())

            self.assertEqual(stream_response.status_code, 200)
            self.assertIn("event: started", body)
            self.assertIn("event: progress", body)
            self.assertIn('"stage_id": "symptom_analysis"', body)
            self.assertIn("event: result", body)
            self.assertIn('"result": "Sample analysis"', body)
        finally:
            main.medical_crew = original_workflow

    def test_progress_endpoint_reports_failures_without_exception_details(self):
        class Workflow:
            async def kickoff_async(self, inputs):
                raise RuntimeError("private symptoms and provider details")

        original_workflow = main.medical_crew
        main.medical_crew = Workflow()
        try:
            with self.client.stream(
                "POST",
                "/api/analyze/progress",
                json={"symptoms": "A symptom", "test_results": ""},
            ) as response:
                body = "".join(response.iter_text())

            self.assertEqual(response.status_code, 200)
            self.assertIn("event: failed", body)
            self.assertNotIn("private symptoms", body)
            self.assertNotIn("provider details", body)
        finally:
            main.medical_crew = original_workflow


if __name__ == "__main__":
    unittest.main()
