from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable
    from typing import TypeVar

    from dev_server.simple_server import SimpleRequestEvent
    from dev_server.simple_server import SimpleResponseEvent

    R = TypeVar("R")


logger = logging.getLogger(__name__)


def serve_single_request(
    *,
    handler: Callable[[SimpleRequestEvent], R],
    port: int = 3000,
    host: str = "127.0.0.1",
    timeout: float | None = None,
    success_message: str = "Go back to terminal.",
) -> R:
    storage: list[R] = []

    def request_handler(request: SimpleRequestEvent) -> SimpleResponseEvent:
        response_event = handler(request)
        storage.append(response_event)
        return {
            "status_code": 200,
            "headers": {},
            "body": (
                f"<html><body><h1>Success</h1><p>{success_message}</p></body></html>".encode(),
            ),
        }

    from dev_server.simple_server import SimpleServer

    server = SimpleServer(request_handler=request_handler).make_server(host, port)

    server.timeout = timeout
    with server as httpd:
        sa = httpd.socket.getsockname()
        server_host, server_port = sa[0], sa[1]
        logger.info("Waiting for callback on http://%s:%d", server_host, server_port)
        try:
            server.handle_request()
        except KeyboardInterrupt:
            msg = "Server stopped by user"
            raise SystemExit(msg) from None

    return storage[0]


if __name__ == "__main__":
    import argparse
    import json

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(description="Serve a single request and print the request.")
    parser.add_argument(
        "--url-open",
        default=None,
        help="URL to open in the browser (default: %(default)s)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to listen on for the callback (default: %(default)s)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port to listen on for the callback (default: %(default)s)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Timeout for the server (default: %(default)s)",
    )
    args = parser.parse_args()
    url: str = args.url_open
    port: int = args.port
    host: str = args.host
    timeout: float | None = args.timeout
    if url is not None:
        import sys
        import webbrowser

        logger.info("Opening browser for authentication: %s", url)
        if not webbrowser.open_new_tab(url):
            print(f"Please open {url} in your browser", file=sys.stderr)
    result = serve_single_request(handler=lambda x: x, port=port, host=host, timeout=timeout)
    print(json.dumps({**result, "content": result["content"].decode("utf-8")}, indent=2))
