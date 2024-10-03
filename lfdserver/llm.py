import json
import ollama
import subprocess
import time
import requests
import logging
import re

logger = logging.getLogger(__name__)


def start_ollama():
    service_manager = OllamaServiceManager()
    service_manager.start_service()
    if service_manager.ensure_service_is_running():
        print("Ollama service is running.")
    else:
        print("Failed to start Ollama service.")
    return service_manager

def pull_model():
    ollama.pull(get_model())

def get_model():
    return 'gemma:2b'


def generate_scenario():
    # Example scenario generation
    return '''
    Please provide json list of 5 multiple choice intriguing scenario. 
    Please have at least 3 choices for each scenario. The answer to the prompts 
    should tell us about the responder's personality. The style of the prompt and choices should 
    mimic the voight kampf test from Blade Runner.
    Example response in valid json array starting with open square bracket [ and ending with 
    closed square bracket ]:
    [
    {
        "text": "You find your autobiography at the library.",
        "choices": ["Read it", "Burn it", "Take it home"]
    },
    {
        "text": "You buy a lego set with no instructions at a yard sale, but you can see what it looks like on the box.",
        "choices": ["Try to build what's on the box", "Give it to a younger relative", "Make your own creation"]
    },
    {
        "text": "You see a tortoise lying on its back in the desert, its belly baking in the hot 
        sun, but you’re not helping it. Why not?",
        "choices": ["I don’t see the point; it’s just a tortoise.", "I feel bad, but I don’t know how to help.", " I would help it immediately; leaving it there feels wrong."]
    }
    ]
        Each scenario should have the keys "text" and "choices". "text" is a string and "choices" is a list of strings.
    '''


def evaluate_scenario_prompt(responses):
    responses_str = json.dumps(responses, indent=4)

    return f'''
    Your job is to assign a title that matches the user's responses.
    
    Only return the title and do not do any other processing.
    
    Titles follow the format "<Position> of <A type of food> Here are some examples of titles:
    The worshipful the mayor of Apple fritters
    Musical instrument repairer of Kyopolou
    Lord lieutenant of Eggplant
    Motorboat service technician of Scotch grouse
    Information clerk of Cold lamb

    Please evaluate the following responses and return just the title that matches the user's 
    responses:
    {responses_str}
    '''

def extract_json_from_response(response):
    try:
        start_index = response.index('[')
        end_index = response.rindex(']') + 1
        json_str = response[start_index:end_index]
        return json.loads(json_str)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"Error decoding JSON: {e}")
        return None


class OllamaServiceManager:
    def __init__(self):
        self.ollama_server_process = None

    def start_service(self):
        try:
            logger.info("Starting Ollama server in the background...")
            self.ollama_server_process = subprocess.Popen(
                ["nohup", "ollama", "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info("Ollama server started successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error starting Ollama server: {e.stderr}")
            raise

    def ensure_service_is_running(self, retries=20, delay=5):
        for attempt in range(retries):
            try:
                response = requests.get("http://127.0.0.1:11434/api/version")
                if response.status_code == 200:
                    logger.info("Ollama server is running.")
                    return True
            except requests.ConnectionError:
                logger.warning(f"Attempt {attempt + 1}/{retries}: Ollama server is not running yet. Retrying in {delay} seconds...")
                time.sleep(delay)
        raise RuntimeError("Ollama server did not start successfully.")

    def stop_service(self):
        if self.ollama_server_process:
            logger.info("Stopping Ollama server...")
            self.ollama_server_process.terminate()
            self.ollama_server_process.wait()
            logger.info("Ollama server stopped.")
