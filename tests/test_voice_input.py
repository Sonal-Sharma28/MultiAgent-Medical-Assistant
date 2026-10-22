import json
import shutil
import subprocess
import unittest
from pathlib import Path


NODE_EXECUTABLE = shutil.which("node")
TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "index.html"


@unittest.skipUnless(NODE_EXECUTABLE, "Node.js is required to test voice input helpers")
class VoiceInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
        cls.template = template
        language_start = template.index("        function getSpeechRecognitionLanguage(")
        language_end = template.index(
            "\n\n        function appendVoiceTranscript",
            language_start,
        )
        cls.language_function = template[language_start:language_end]
        function_start = template.index("        function appendVoiceTranscript(")
        function_end = template.index("\n\n        function setSpeechStatus", function_start)
        cls.append_function = template[function_start:function_end]

    def get_recognition_language(self, preferred_languages):
        script = (
            f"{self.language_function}\n"
            "console.log(JSON.stringify(getSpeechRecognitionLanguage("
            f"{json.dumps(preferred_languages)})));"
        )
        completed = subprocess.run(
            [NODE_EXECUTABLE, "-e", script],
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        return json.loads(completed.stdout)

    def append_transcript(self, existing, transcript, max_length):
        script = (
            f"{self.append_function}\n"
            "console.log(JSON.stringify(appendVoiceTranscript("
            f"{json.dumps(existing)}, {json.dumps(transcript)}, {max_length})));"
        )
        completed = subprocess.run(
            [NODE_EXECUTABLE, "-e", script],
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        return json.loads(completed.stdout)

    def test_appends_speech_with_spacing(self):
        result = self.append_transcript("Existing symptoms", "new spoken words", 100)

        self.assertEqual(result["value"], "Existing symptoms new spoken words")
        self.assertFalse(result["truncated"])

    def test_voice_input_is_truncated_at_character_limit(self):
        result = self.append_transcript("12345", "67890", 8)

        self.assertEqual(result["value"], "12345 67")
        self.assertEqual(len(result["value"]), 8)
        self.assertTrue(result["truncated"])

    def test_appended_speech_preserves_unicode_character_count(self):
        result = self.append_transcript("नमस्ते", "दुनिया", 13)

        self.assertEqual(result["value"], "नमस्ते दुनिया")
        self.assertFalse(result["truncated"])

    def test_recognition_language_uses_first_supported_browser_locale(self):
        cases = [
            (["hi-IN", "en-US"], "hi-IN"),
            (["mr-IN", "en-US"], "mr-IN"),
            (["en-GB", "mr-IN"], "en-IN"),
            (["fr-FR"], "en-IN"),
            ([], "en-IN"),
        ]
        for preferred_languages, expected in cases:
            with self.subTest(preferred_languages=preferred_languages):
                self.assertEqual(
                    self.get_recognition_language(preferred_languages),
                    expected,
                )

    def test_ui_has_no_language_selector_and_discloses_no_auto_detection(self):
        self.assertNotIn('id="speechLanguage"', self.template)
        self.assertNotIn("speechLanguage.disabled", self.template)
        self.assertIn("does not automatically detect", self.template)


if __name__ == "__main__":
    unittest.main()
