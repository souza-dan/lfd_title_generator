import sys
import os
import unittest
import ollama

from llm import generate_scenario, extract_json_from_response, pull_model, start_ollama, get_model, \
    evaluate_scenario_prompt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


class TestLlama3Model(unittest.TestCase):
    service_manager = None
    @classmethod
    def setUpClass(cls):
        cls.service_manager = start_ollama()
        pull_model()


    @classmethod
    def tearDownClass(cls):
        if (cls.service_manager):
            cls.service_manager.stop_service()

    def test_ollama(self):
        response = ollama.generate(model=get_model(), prompt=generate_scenario())
        print("Prompt Response:", response)
        self.assertIn("choices", response['response'].lower())
        self.assertIn("text", response['response'].lower())

        # ensure we can extract the json from the real response
        scenarios = extract_json_from_response(response['response'])
        self.assertIsNotNone(scenarios)
        self.assertEqual(len(scenarios), 5)

        title = ollama.generate(model=get_model(), prompt=evaluate_scenario_prompt(scenarios))
        print("Title Prompt Response:", title)
        self.assertIsNotNone(title.get('response'))







class TestExtractJsonFromResponse(unittest.TestCase):


    def test_valid_json(self):
        response = """
        Here are your scenarios:

        [
            {
                "text": "You find a mysterious book in an old library. What do you do?",
                "choices": ["Read it", "Ignore it", "Take it home"]
            },
            {
                "text": "You encounter a dragon. What do you do?",
                "choices": ["Fight it", "Run away", "Befriend it"]
            }
        ].
        """
        expected_output = [
            {
                "text": "You find a mysterious book in an old library. What do you do?",
                "choices": ["Read it", "Ignore it", "Take it home"]
            },
            {
                "text": "You encounter a dragon. What do you do?",
                "choices": ["Fight it", "Run away", "Befriend it"]
            }
        ]
        self.assertEqual(extract_json_from_response(response), expected_output)

    def test_no_json(self):
        response = "Here is your scenario: No JSON here."
        self.assertIsNone(extract_json_from_response(response))

    def test_invalid_json(self):
        response = """
        Here are your scenarios:

        [
            {
                "text": "You find a mysterious book in an old library. What do you do?",
                "choices": ["Read it", "Ignore it", "Take it home"
            },
            {
                "text": "You encounter a dragon. What do you do?",
                "choices": ["Fight it", "Run away", "Befriend it"]
            }
        ]
        """
        self.assertIsNone(extract_json_from_response(response))

    def test_multiple_json_objects(self):
        response = """
        Here are your scenarios:

        [
            {
                "text": "You find a mysterious book in an old library.",
                "choices": ["Read it", "Ignore it", "Take it home"]
            },
            {
                "text": "You encounter a dragon. It's scary.",
                "choices": ["Fight it", "Run away", "Befriend it"]
            }
        ].
        """
        expected_output = [
            {
                "text": "You find a mysterious book in an old library.",
                "choices": ["Read it", "Ignore it", "Take it home"]
            },
            {
                "text": "You encounter a dragon. It's scary.",
                "choices": ["Fight it", "Run away", "Befriend it"]
            }
        ]
        self.assertEqual(extract_json_from_response(response), expected_output)



if __name__ == '__main__':
    unittest.main()
