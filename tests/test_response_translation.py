import json
import shutil
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

import main


NODE_EXECUTABLE = shutil.which("node")
TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "index.html"


class ResponseTranslationApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_translation_uses_configured_llm_without_running_analysis(self):
        original_response = (
            "## Summary\n\nValue: 120 mg/dL (reference range: 70-100).\n"
            "Seek urgent care for severe symptoms.\n\nMedical disclaimer."
        )
        llm_call = Mock(return_value="## सारांश\n\nमूल्य: 120 mg/dL (संदर्भ सीमा: 70-100)।")
        kickoff = Mock()

        with patch.object(main, "my_llm", SimpleNamespace(call=llm_call)), patch.object(
            main,
            "medical_crew",
            SimpleNamespace(kickoff_async=kickoff),
        ):
            response = self.client.post(
                "/api/translate",
                json={"response": original_response, "language": "hi"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["translation"], llm_call.return_value)
        self.assertEqual(response.json()["language"], "hi")
        prompt = llm_call.call_args.args[0]
        self.assertIn(original_response, prompt)
        self.assertIn("urgent-care warnings", prompt)
        kickoff.assert_not_called()

    def test_translation_failure_returns_clear_generic_error(self):
        llm_call = Mock(side_effect=RuntimeError("private provider details"))

        with patch.object(
            main,
            "my_llm",
            SimpleNamespace(call=llm_call),
        ):
            response = self.client.post(
                "/api/translate",
                json={"response": "Original response", "language": "mr"},
            )

        self.assertEqual(response.status_code, 502)
        self.assertIn("original English response is unchanged", response.json()["detail"])
        self.assertNotIn("private provider details", response.text)

    def test_unsupported_language_is_rejected_without_calling_provider(self):
        llm_call = Mock()

        with patch.object(
            main,
            "my_llm",
            SimpleNamespace(call=llm_call),
        ):
            response = self.client.post(
                "/api/translate",
                json={"response": "Original response", "language": "en"},
            )

        self.assertEqual(response.status_code, 422)
        llm_call.assert_not_called()


@unittest.skipUnless(NODE_EXECUTABLE, "Node.js is required to test response translation")
class ResponseTranslationFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = TEMPLATE_PATH.read_text(encoding="utf-8")
        function_start = cls.template.index(
            "        async function requestResponseTranslation("
        )
        function_end = cls.template.index(
            "\n\n        async function showSelectedResponseLanguage",
            function_start,
        )
        cls.translation_function = cls.template[function_start:function_end]
        handler_start = function_end + 2
        handler_end = cls.template.index(
            "\n\n        responseLanguageSelect.addEventListener",
            handler_start,
        )
        cls.display_function = cls.template[handler_start:handler_end]

    def run_display_flow(self, fetch_response):
        original_response = (
            "Summary: 100 mg/dL. Seek urgent care if symptoms worsen. Disclaimer."
        )
        script = (
            "const original = "
            f"{json.dumps(original_response, ensure_ascii=False)};\n"
            "let currentAnalysis = {id: 'analysis-1', response: original};\n"
            "let translationRequestId = 0;\n"
            "const translatedResponses = new Map();\n"
            "const responseLanguageSelect = {value: 'en', removeAttribute() {}, setAttribute() {}};\n"
            "const translationMessage = {textContent: '', dataset: {}};\n"
            "const copyMessage = {textContent: '', dataset: {}};\n"
            "const downloadMessage = {textContent: ''};\n"
            "const resultContent = {hidden: false, textContent: ''};\n"
            "const copyResponseButton = {disabled: false};\n"
            "const downloadReportButton = {disabled: false};\n"
            "const requests = [];\n"
            "function renderMarkdownResult(text, container) { container.textContent = text; }\n"
            f"global.fetch = async (url, options) => {{ requests.push({{url, body: JSON.parse(options.body)}}); return {fetch_response}; }};\n"
            f"{self.translation_function}\n"
            f"{self.display_function}\n"
            "(async () => {\n"
            "  await showSelectedResponseLanguage();\n"
            "  const english = resultContent.textContent;\n"
            "  responseLanguageSelect.value = 'hi';\n"
            "  await showSelectedResponseLanguage();\n"
            "  const hindi = resultContent.textContent;\n"
            "  responseLanguageSelect.value = 'en';\n"
            "  await showSelectedResponseLanguage();\n"
            "  const restoredEnglish = resultContent.textContent;\n"
            "  responseLanguageSelect.value = 'mr';\n"
            "  await showSelectedResponseLanguage();\n"
            "  console.log(JSON.stringify({english, hindi, restoredEnglish, finalText: resultContent.textContent, selected: responseLanguageSelect.value, message: translationMessage.textContent, requests}));\n"
            "})();"
        )
        completed = subprocess.run(
            [NODE_EXECUTABLE, "-e", script],
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        return original_response, json.loads(completed.stdout)

    def test_response_language_options_default_to_english_without_voice_dropdown(self):
        self.assertIn(
            '<select id="responseLanguage" name="response_language"',
            self.template,
        )
        self.assertIn('<option value="en" selected>English</option>', self.template)
        self.assertIn('<option value="hi">Hindi (हिन्दी)</option>', self.template)
        self.assertIn('<option value="mr">Marathi (मराठी)</option>', self.template)
        self.assertNotIn('id="speechLanguage"', self.template)

    def test_switching_languages_always_sends_the_original_response(self):
        original_response, result = self.run_display_flow(
            "{ok: true, json: async () => ({translation: `translated-${requests.length}`})}"
        )

        self.assertEqual(result["english"], original_response)
        self.assertEqual(result["hindi"], "translated-1")
        self.assertEqual(result["restoredEnglish"], original_response)
        self.assertEqual(result["finalText"], "translated-2")
        self.assertEqual(result["selected"], "mr")
        self.assertEqual([request["url"] for request in result["requests"]], [
            "/api/translate",
            "/api/translate",
        ])
        self.assertEqual(
            [request["body"]["response"] for request in result["requests"]],
            [original_response, original_response],
        )
        self.assertEqual(
            [request["body"]["language"] for request in result["requests"]],
            ["hi", "mr"],
        )
        self.assertNotIn("/api/analyze", json.dumps(result["requests"]))

    def test_translation_failure_is_not_treated_as_a_success(self):
        original_response, result = self.run_display_flow(
            "{ok: false, json: async () => ({})}"
        )

        self.assertEqual(result["english"], original_response)
        self.assertEqual(result["hindi"], original_response)
        self.assertEqual(result["restoredEnglish"], original_response)
        self.assertEqual(result["selected"], "en")
        self.assertIn("Translation is unavailable", result["message"])
        self.assertEqual(len(result["requests"]), 2)


if __name__ == "__main__":
    unittest.main()
