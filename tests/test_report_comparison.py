import json
import shutil
import subprocess
import unittest
from pathlib import Path


NODE_EXECUTABLE = shutil.which("node")
TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "index.html"


@unittest.skipUnless(NODE_EXECUTABLE, "Node.js is required to test browser comparison logic")
class ReportComparisonLogicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
        function_start = template.index("        function compareMedicalReports(")
        function_end = template.index(
            "\n\n        function appendComparisonCell",
            function_start,
        )
        cls.comparison_function = template[function_start:function_end]

    def run_comparisons(self, cases):
        serialized_cases = json.dumps(cases)
        script = (
            f"{self.comparison_function}\n"
            f"const cases = {serialized_cases};\n"
            "console.log(JSON.stringify(cases.map(({ previous, latest }) => "
            "compareMedicalReports(previous, latest))));"
        )
        completed = subprocess.run(
            [NODE_EXECUTABLE, "-e", script],
            capture_output=True,
            check=True,
            text=True,
        )
        return json.loads(completed.stdout)

    @staticmethod
    def report(**overrides):
        report = {
            "date": "2025-01-01",
            "testName": "Glucose",
            "value": 10,
            "unit": "mmol/L",
            "referenceRange": "",
        }
        report.update(overrides)
        return report

    def test_matching_reports_calculate_absolute_and_percentage_change(self):
        previous = self.report(testName="  GLUCOSE  ", value=10)
        latest = self.report(date="2025-02-01", testName="glucose", value=12)

        result = self.run_comparisons([{"previous": previous, "latest": latest}])[0]

        self.assertTrue(result["valid"])
        self.assertTrue(result["comparable"])
        self.assertEqual(result["absoluteChange"], 2)
        self.assertEqual(result["percentageChange"], 20)

    def test_different_tests_are_not_comparable(self):
        previous = self.report()
        latest = self.report(date="2025-02-01", testName="Hemoglobin")

        result = self.run_comparisons([{"previous": previous, "latest": latest}])[0]

        self.assertTrue(result["valid"])
        self.assertFalse(result["comparable"])
        self.assertIn("Different tests cannot be directly compared", result["message"])

    def test_different_units_are_not_calculated(self):
        previous = self.report()
        latest = self.report(date="2025-02-01", unit="mg/dL")
        case_mismatched_unit = self.report(date="2025-02-01", unit="MMOL/L")

        results = self.run_comparisons(
            [
                {"previous": previous, "latest": latest},
                {"previous": previous, "latest": case_mismatched_unit},
            ]
        )

        for result in results:
            self.assertTrue(result["valid"])
            self.assertFalse(result["comparable"])
            self.assertIn("Compatible units are required", result["message"])

    def test_zero_previous_value_has_no_percentage_change(self):
        previous = self.report(value=0)
        latest = self.report(date="2025-02-01", value=3)

        result = self.run_comparisons([{"previous": previous, "latest": latest}])[0]

        self.assertTrue(result["comparable"])
        self.assertEqual(result["absoluteChange"], 3)
        self.assertIsNone(result["percentageChange"])

    def test_invalid_values_and_date_order_are_rejected(self):
        invalid_value = self.report(value=float("nan"))
        latest = self.report(date="2025-02-01")
        invalid_dates = self.report(date="2025-03-01")

        results = self.run_comparisons(
            [
                {"previous": invalid_value, "latest": latest},
                {"previous": invalid_dates, "latest": latest},
            ]
        )

        self.assertTrue(all(not result["valid"] for result in results))
        self.assertTrue(all(not result["comparable"] for result in results))


if __name__ == "__main__":
    unittest.main()
