import ollama
from flask import Flask, render_template, request, jsonify

import argparse
import json
import logging
import random
import atexit
import socket
import time
import threading
import queue

from llm import generate_scenario, extract_json_from_response, pull_model, get_model, start_ollama, \
    evaluate_scenario_prompt

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, template_folder="./")

main_titles = []
main_nouns = []

# Initialize the queue with a maximum size
scenario_queue = queue.Queue(maxsize=10)

def fill_scenario_queue():
    while True:
        if not scenario_queue.full():
            response = ollama.generate(model=get_model(), prompt=generate_scenario())
            log.info(f"Generated response: {response}")
            scenario_json = extract_json_from_response(response['response'])
            if scenario_json:
                scenario_queue.put(scenario_json)
        log.info(f"Scenario queue: {scenario_queue.qsize()}")
        time.sleep(1)  # Sleep for a while before checking the queue again


# apis
@app.route('/api/v1/hello')
def api_modules():
    return ('hello world')


@app.route('/api/v1/title')
def api_generate_title():
    titles = check_loaded(main_titles, 'titles.json')
    nouns = check_loaded(main_nouns, 'nouns.json')
    return '{} of {}'.format(random.choice(titles).capitalize(), random.choice(nouns).capitalize())

@app.route('/api/v1/title2')
def api_generate_title_2():
    titles = check_loaded(main_titles, 'titles.json')
    nouns = check_loaded(main_nouns, 'nouns.json')
    return '{} of {} and {}'.format(
        random.choice(titles).capitalize(),
        random.choice(nouns).capitalize(),
        random.choice(nouns).capitalize()
    )


@app.route('/api/v1/shuffle', methods=['POST'])
def shuffle_list():
    csv = request.form.get('list')
    separator = request.form.get('separator')
    if not separator:
        separator = ","
    if csv:
        csv_list = ([x for x in request.form.get('list').split(",")])
        random.shuffle(csv_list)
        return jsonify(separator.join(csv_list))
    return jsonify(["no values"])


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_scenarios', methods=['POST'])
def submit_scenarios():
    responses = {}
    for key, value in request.form.items():
        if key.startswith('response_'):
            scenario_index = key.split('_')[1]
            scenario_text = request.form.get(f'scenario_{scenario_index}')
            responses[scenario_text] = value

    # Process the responses as needed
    # For example, generate a title based on the responses
    title = model.generate_title(responses)
    return jsonify({'title': title})

@app.route('/scenario', methods=['GET'])
def scenario():
    if not scenario_queue.empty():
        scenario_json = scenario_queue.queue[0]  # Peek at the first item
        if scenario_queue.qsize() > 1:
            scenario_queue.get()  # Remove the item if it's not the last one
        return render_template('scenario.html', scenarios=scenario_json)
    else:
        log.error("Scenario queue is empty.")
        return "Error: No scenarios available. Try again later.", 500

@app.route('/submit_response', methods=['POST'])
def submit_response():
    log.info(f"Submitted form: {request.form}")
    user_response = {}
    for key, value in request.form.items():
        if key.startswith('response_'):
            scenario_index = key.split('_')[1]
            scenario_text = request.form.get(f'scenario_{scenario_index}')
            user_response[scenario_text] = value

    log.info(f"Submitted response: {user_response}")

    # Generate a title based on the user's response
    response = ollama.generate(model=get_model(), prompt=evaluate_scenario_prompt(user_response))

    log.info(f"Evaluated Response: {response}")

    return jsonify({'title': response['response']})


def load_args(json_file):
    with open(json_file) as f:
        return list(set([item.lower() for item in json.load(f)]))


def check_loaded(loaded_content, json_file):
    # In case main is not used
    if not loaded_content:
        return load_args(json_file)
    return loaded_content


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run a simple web server that generates titles")
    parser.add_argument('-n', '--nouns', default="nouns.json",
                        help='a file with a json list of nouns')
    parser.add_argument('-t', '--titles', default="titles.json",
                        help='a file with a json list of titles')

    args = parser.parse_args()

    main_nouns = load_args(args.nouns)
    main_titles = load_args(args.titles)

    service_manager = start_ollama()
    atexit.register(service_manager.stop_service)

    pull_model()

    # Set the socket timeout
    socket.setdefaulttimeout(600)
    # Start the background thread to fill the scenario queue
    threading.Thread(target=fill_scenario_queue, daemon=True).start()

    scenario_queue.put([
        {
            "text": "You find a mysterious book in an old library. What do you do?",
            "choices": ["Read it", "Ignore it", "Take it home"]
        },
        {
            "text": "You encounter a dragon. What do you do?",
            "choices": ["Fight it", "Run away", "Befriend it"]
        }
    ])

    app.run(host='0.0.0.0')
