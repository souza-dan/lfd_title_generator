# LFD Server

LFD Server is a simple Flask-based web server that generates random titles and shuffles lists. It provides several API endpoints for generating titles and shuffling lists.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Docker](#docker)
- [API Endpoints](#api-endpoints)
- [Configuration](#configuration)
- [License](#license)

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/souza-dan/lfd_title_generator.git
    cd lfd_title_generator
    ```

2. Create a virtual environment and activate it:
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the required dependencies:
    ```sh
    cd lfdserver
    pip install -r requirements.txt
    ```

## Usage

1. Run the server:
    ```sh
    python server.py
    ```

2. The server will start on `http://0.0.0.0:5000`.


## Docker

### Build the Docker image
```sh
cd lfdserver
docker build -t lfd_server .
```

### Run the Docker container
```sh
docker run -p 5000:5000 lfd_server
```

## API Endpoints

### `GET /api/v1/hello`

Returns a simple "hello world" message.

### `GET /api/v1/title`

Generates a random title in the format "Title of Noun".

### `GET /api/v1/title2`

Generates a random title in the format "Title of Noun and Noun".

### `POST /api/v1/shuffle`

Shuffles a list of items provided in the request.

- **Request Parameters:**
  - `list` (string): A comma-separated list of items to shuffle.
  - `separator` (string, optional): The separator to use in the response. Defaults to a comma.

- **Example Request:**
    ```sh
    curl -X POST -F "list=item1,item2,item3" -F "separator=," http://0.0.0.0:5000/api/v1/shuffle
    ```

- **Example Response:**
    ```json
    ["item3,item1,item2"]
    ```

## Configuration

The server uses two JSON files for generating titles and nouns:

- `titles.json`: Contains a list of titles.
- `nouns.json`: Contains a list of nouns.

You can specify different files using the `-t` and `-n` command-line arguments when starting the server.

To enable scenario generation, use the -s flag when starting the server. Ensure the OLLAMA_MODEL environment variable is set to the desired model.

To enable gemini role descriptions, set `GEMINI_API_KEY`. The model is configurable with `GEMINI_MODEL` (e.g. `gemini-2.0-flash-lite`).

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
