import unittest

from crew import medical_crew
from tasks import (
    diagnosis_suggestion_task,
    symptom_analysis_task,
    test_interpretation_task,
    treatment_planning_task,
)


class ResponsePromptTests(unittest.TestCase):
    def test_existing_sequential_task_order_and_assignments_remain(self):
        self.assertEqual(
            medical_crew.tasks,
            [
                symptom_analysis_task,
                test_interpretation_task,
                diagnosis_suggestion_task,
                treatment_planning_task,
            ],
        )
        self.assertEqual(medical_crew.process.value, "sequential")

    def test_final_task_requests_clear_concise_sections_and_safety(self):
        prompt = treatment_planning_task.description.lower()

        for section in (
            "## summary",
            "## what the information may indicate",
            "## recommended next steps",
            "## when to seek urgent medical care",
            "## questions to ask your doctor",
            "## medical disclaimer",
        ):
            with self.subTest(section=section):
                self.assertIn(section, prompt)

        self.assertIn("150–250", prompt)
        self.assertIn("not a hard limit", prompt)
        self.assertIn("never omit", prompt)
        self.assertIn("do not repeat", prompt)
        self.assertIn("do not claim possible", prompt)

    def test_analysis_tasks_limit_repetition_and_unsupported_claims(self):
        symptom_prompt = symptom_analysis_task.description.lower()
        test_prompt = test_interpretation_task.description.lower()
        diagnosis_prompt = diagnosis_suggestion_task.description.lower()

        self.assertIn("do not diagnose", symptom_prompt)
        self.assertIn("do not infer a diagnosis", test_prompt)
        self.assertIn("if no test results", test_prompt)
        self.assertIn("supported by the information", diagnosis_prompt)
        self.assertIn("do not introduce unsupported findings", diagnosis_prompt)
        self.assertIn("repeat prior summaries", diagnosis_prompt)


if __name__ == "__main__":
    unittest.main()
