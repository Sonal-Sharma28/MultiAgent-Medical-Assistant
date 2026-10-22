import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

import main


class AnalysisValidationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_oversized_symptoms_are_rejected_before_ai_workflow(self):
        kickoff = AsyncMock()
        workflow = SimpleNamespace(kickoff_async=kickoff)

        with patch.object(main, "medical_crew", workflow):
            response = self.client.post(
                "/api/analyze",
                json={
                    "symptoms": "x" * (main.MAX_SYMPTOMS_LENGTH + 1),
                    "test_results": "",
                },
            )

        self.assertEqual(response.status_code, 422)
        self.assertIn(
            f"at most {main.MAX_SYMPTOMS_LENGTH} characters",
            response.text,
        )
        kickoff.assert_not_awaited()

    def test_oversized_test_results_are_rejected_before_ai_workflow(self):
        kickoff = AsyncMock()
        workflow = SimpleNamespace(kickoff_async=kickoff)

        with patch.object(main, "medical_crew", workflow):
            response = self.client.post(
                "/api/analyze",
                json={
                    "symptoms": "A symptom",
                    "test_results": "x" * (main.MAX_TEST_RESULTS_LENGTH + 1),
                },
            )

        self.assertEqual(response.status_code, 422)
        self.assertIn(
            f"at most {main.MAX_TEST_RESULTS_LENGTH} characters",
            response.text,
        )
        kickoff.assert_not_awaited()

    def test_symptoms_at_maximum_length_are_accepted(self):
        kickoff = AsyncMock(return_value="Example response")
        workflow = SimpleNamespace(kickoff_async=kickoff)
        symptoms = "x" * main.MAX_SYMPTOMS_LENGTH

        with patch.object(main, "medical_crew", workflow):
            response = self.client.post(
                "/api/analyze",
                json={"symptoms": symptoms, "test_results": ""},
            )

        self.assertEqual(response.status_code, 200)
        kickoff.assert_awaited_once_with(
            inputs={"symptoms": symptoms, "test_results": ""}
        )

    def test_form_uses_backend_length_limits(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            f'data-max-length="{main.MAX_SYMPTOMS_LENGTH}"',
            response.text,
        )
        self.assertIn(
            f'data-max-length="{main.MAX_TEST_RESULTS_LENGTH}"',
            response.text,
        )


if __name__ == "__main__":
    unittest.main()
