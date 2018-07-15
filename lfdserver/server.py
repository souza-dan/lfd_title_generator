from flask import Flask, render_template

import argparse
import json
import logging
import random

log = logging.getLogger(__name__)
app = Flask(__name__, template_folder="./")

main_titles = []
main_nouns = []

# apis
@app.route('/api/v1/hello')
def api_modules():
    return ('hello world')


@app.route('/api/v1/title')
def api_generate_title():
    titles = check_loaded(main_titles, 'titles.json')
    nouns = check_loaded(main_nouns, 'nouns.json')
    return '{} of {}'.format(random.choice(titles).capitalize(), random.choice(nouns).capitalize())


@app.route('/')
def index():
    return render_template('index.html')


def load_args(json_file):
    with open(json_file) as f:
        return json.load(f)


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
    app.run(host='0.0.0.0')
