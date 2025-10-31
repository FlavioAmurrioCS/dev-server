# dev-server

[![PyPI - Version](https://img.shields.io/pypi/v/dev-server.svg)](https://pypi.org/project/dev-server)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/dev-server.svg)](https://pypi.org/project/dev-server)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/FlavioAmurrioCS/dev-server/main.svg)](https://results.pre-commit.ci/latest/github/FlavioAmurrioCS/dev-server/main)

-----

## Table of Contents

- [dev-server](#dev-server)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Quick Start](#quick-start)
    - [Commands](#commands)
      - [1. Mock Server](#1-mock-server)
      - [2. Proxy Server](#2-proxy-server)
      - [3. Single Request Server](#3-single-request-server)
    - [Global Options](#global-options)
    - [Examples](#examples)
  - [Programmatic Usage](#programmatic-usage)
    - [SimpleServer](#simpleserver)
      - [Basic Example](#basic-example)
      - [Request Event Structure](#request-event-structure)
      - [Response Event Structure](#response-event-structure)
  - [License](#license)

## Installation

```console
pip install dev-server
```

## Usage

`dev-server` is a lightweight development HTTP server with three modes of operation:

### Quick Start

```bash
dev-server <command> [options]
```

### Commands

#### 1. Mock Server

Start a mock HTTP server that returns predefined responses and stores request history.

```bash
dev-server [-p PORT] [--host HOST] mock [--responses FILE]
```

**Features:**
- Return predefined responses based on HTTP method and path
- Store all requests in memory for later retrieval
- Built-in endpoints:
  - `GET /_ping` - Health check endpoint (returns "pong")
  - `GET /_requests` - Retrieve stored requests
    - `?last=true` - Get only the last request
    - `?clear=true` - Get all requests and clear the history

**Response Mapping Format:**

Create a JSON file with response mappings:

```json
{
  "GET:/api/users": {
    "status_code": 200,
    "headers": {
      "Content-Type": "application/json"
    },
    "body": "[{\"id\": 1, \"name\": \"李明\"}, {\"id\": 2, \"name\": \"García\"}]"
  },
  "POST:/api/users": {
    "status_code": 201,
    "body": "{\"id\": 3, \"created\": true}"
  }
}
```

#### 2. Proxy Server

Start a proxy server that forwards requests to a target URL and records all traffic.

```bash
dev-server proxy <TARGET_URL> [-o OUTPUT] [--indent INDENT]
```

**Features:**
- Forward all requests to a target server
- Record requests and responses to a file (JSONL format)
- Useful for debugging, testing, and traffic analysis

**Example:**

```bash
# Proxy to example.com and save to file
dev-server proxy https://api.example.com -o requests.jsonl

# Proxy with formatted JSON output
dev-server proxy https://api.example.com -o requests.jsonl --indent 2

# Proxy to stdout (default)
dev-server proxy https://api.example.com
```

#### 3. Single Request Server

Serve a single HTTP request, print the request details, and optionally open a URL in the browser.

```bash
dev-server [-p PORT] [--host HOST] single-request [URL]
```

**Features:**
- Ideal for OAuth callbacks and webhook testing
- Automatically opens URL in browser (if provided)
- Returns full request details as JSON
- Server terminates after handling one request

**Example:**

```bash
# Capture a single request
dev-server single-request

# Open OAuth URL and capture callback
dev-server single-request "https://oauth.example.com/authorize?client_id=xyz"
```

### Global Options

**Note:** Global options must be placed BEFORE the command name.

- `-p, --port PORT` - Port to run the server on (default: 3000)
- `--host HOST` - Host to bind the server to (default: 127.0.0.1)
- `-t, --timeout TIMEOUT` - Timeout for the server in seconds
- `-v, --verbose` - Increase verbosity level (can be used multiple times)

### Examples

```bash
# Mock server on custom port with verbose logging
dev-server -p 8080 -vvv mock --responses api-mocks.json

# Proxy server with request recording on custom port
dev-server -p 8000 proxy https://jsonplaceholder.typicode.com -o captured.jsonl

# Single request for OAuth callback on custom port
dev-server -p 3000 single-request "https://oauth.example.com/authorize?client_id=xyz"

# Mock server with custom host and timeout
dev-server --host 0.0.0.0 -t 60 -p 8080 mock --responses api-mocks.json

# Check stored requests in mock server
curl http://localhost:3000/_requests

# Get last request only
curl http://localhost:3000/_requests?last=true

# Get all requests and clear history
curl http://localhost:3000/_requests?clear=true
```

## Programmatic Usage

### SimpleServer

The `SimpleServer` class provides a simple WSGI server interface that can be used to build custom HTTP tooling. It abstracts away WSGI complexities and provides a clean request/response API.

#### Basic Example

```python
from dev_server.simple_server import SimpleServer, SimpleRequestEvent, SimpleResponseEvent

def my_handler(request: SimpleRequestEvent) -> SimpleResponseEvent:
    """Handle incoming HTTP requests."""
    return {
        "status_code": 200,
        "headers": {"Content-Type": "text/plain"},
        "body": [b"Hello, World!"],
    }

server = SimpleServer(request_handler=my_handler)
server.serve_forever(host="127.0.0.1", port=8080)
```

#### Request Event Structure

The `SimpleRequestEvent` provides parsed request data:

```python
{
    "method": "GET",           # HTTP method (GET, POST, PUT, DELETE, etc.)
    "url": "/api/users",       # Request path
    "headers": {               # Request headers (dict)
        "Content-Type": "application/json",
        "User-Agent": "..."
    },
    "params": {                # Query parameters (dict[str, list[str]])
        "page": ["1"],
        "limit": ["10"]
    },
    "content": b"..."          # Request body as bytes
}
```

#### Response Event Structure

Return a `SimpleResponseEvent` from your handler:

```python
{
    "status_code": 200,        # HTTP status code
    "headers": {               # Response headers (dict)
        "Content-Type": "application/json"
    },
    "body": [b"..."]          # Response body as iterable of bytes
}
```


## License

`dev-server` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
