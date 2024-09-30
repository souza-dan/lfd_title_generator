import sys
import os
import unittest
import ollama

from llm import generate_scenario, extract_json_from_response, pull_model, start_ollama
from server import scenario

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from llama3.model import Llama3Model

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
        response = ollama.generate(model='gemma', prompt=generate_scenario())
        print("Prompt Response:", response)
        self.assertIn("choices", response['response'].lower())
        self.assertIn("text", response['response'].lower())


class TestExtractJsonFromResponse(unittest.TestCase):

    def test_valid_json(self):
        response = """
        Here is your scenario:

        {
            "text": "You find a mysterious book in an old library. What do you do?",
            "choices": ["Read it", "Ignore it", "Take it home"]
        }.
        """
        expected_output = {
            "text": "You find a mysterious book in an old library. What do you do?",
            "choices": ["Read it", "Ignore it", "Take it home"]
        }
        self.assertEqual(extract_json_from_response(response), expected_output)

    def test_no_json(self):
        response = "Here is your scenario: No JSON here."
        self.assertIsNone(extract_json_from_response(response))

    def test_invalid_json(self):
        response = """
        Here is your scenario:

        {
            "text": "You find a mysterious book in an old library. What do you do?",
            "choices": ["Read it", "Ignore it", "Take it home"
        }
        """
        self.assertIsNone(extract_json_from_response(response))

    def test_multiple_json_objects(self):
        response = """
        Here is your scenario:

        {
            "text": "You find a mysterious book in an old library. What do you do?",
            "choices": ["Read it", "Ignore it", "Take it home"]
        }

        Another scenario:

        {
            "text": "You encounter a dragon. What do you do?",
            "choices": ["Fight it", "Run away", "Befriend it"]
        }
        """
        expected_output = {
            "text": "You find a mysterious book in an old library. What do you do?",
            "choices": ["Read it", "Ignore it", "Take it home"]
        }
        self.assertEqual(extract_json_from_response(response), expected_output)

if __name__ == '__main__':
    unittest.main()
