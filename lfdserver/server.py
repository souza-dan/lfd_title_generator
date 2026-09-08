import os

import ollama
from flask import Flask, render_template, request, jsonify, send_from_directory

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
    evaluate_scenario_prompt, create_gemini_model, configure_gemini, generate_content, \
    title_responsibilities_prompt

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, template_folder="./")

main_titles = []
main_nouns = []

# Initialize the queue with a maximum size
scenario_queue = queue.Queue(maxsize=10)

gemini_model = None

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
    title = '{} of {}'.format(random.choice(titles).capitalize(), random.choice(nouns).capitalize())
    if gemini_model:
        responsibilities = generate_content(gemini_model, title_responsibilities_prompt(title))
        # Sometimes, gemini will wrap the response in "```html"
        if "```html" in responsibilities:
            responsibilities = responsibilities.replace("```html", "")
            responsibilities = responsibilities.replace("```", "")
        # The responsibilities usually includes the title
        return (f'<h1 class="card-title pricing-card-title">{title}</h1>'
                f'<div class="card-title pricing-card-body text-left">{responsibilities}</div>')
    else:
        return title

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


@app.route('/storybook')
def storybook():
    return send_from_directory(os.path.dirname(__file__), 'storybook.html')


@app.route('/assets/<path:filename>')
def serve_assets(filename):
    assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
    return send_from_directory(assets_dir, filename)


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
    parser.add_argument('-s', '--scenarios', action='store_true',
                        help='generate scenarios with ollama. Set model with '
                             'environment variable OLLAMA_MODEL')


    args = parser.parse_args()

    main_nouns = load_args(args.nouns)
    main_titles = load_args(args.titles)

    if args.scenarios:
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

    if os.environ.get("GEMINI_API_KEY"):
        log.info(f"GEMINI_API_KEY=: {os.environ.get('GEMINI_API_KEY')[:4]}")
        client = configure_gemini()
        if os.environ.get("GEMINI_MODEL"):
            gemini_model = create_gemini_model(model=os.environ["GEMINI_MODEL"], client=client)
        else:
            gemini_model = create_gemini_model(client=client)


    app.run(host='0.0.0.0')
