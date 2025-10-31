from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from typing_extensions import Protocol

    from dev_server.simple_server import SimpleRequestEvent
    from dev_server.simple_server import SimpleResponseEvent

    class Args(Protocol):
        command: str
        port: int
        host: str
        timeout: float | None
        verbose: int
        responses: str | None
        url: str
        output: str
        indent: int | None


logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="A simple development HTTP server with mock and proxy capabilities.",
        epilog=(
            "Example usages:\n"
            "  %(prog)s mock --responses responses.json\n"
            "  %(prog)s proxy https://example.com -o requests.jsonl\n"
            "  %(prog)s single-request\n"
        ),
    )
    parser.add_argument("-p", "--port", type=int, default=3000, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to run the server on")
    parser.add_argument("-t", "--timeout", type=float, default=None, help="Timeout for the server")
    parser.add_argument(
        "-v", "--verbose", action="count", default=2, help="Increase verbosity level"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ############################################################################
    # region: Mock server parser
    ############################################################################
    mock_parser = subparsers.add_parser(
        "mock",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help=(
            "Start a mock HTTP server that returns predefined responses "
            "and stores request history for later retrieval"
        ),
        epilog=(
            "Response mapping format:\n"
            '  {"METHOD:/path": {"status_code": 200, "headers": {...}, "body": "..."}}\n'
            "\n"
            "Example:\n"
            '  {"GET:/api/users": {"status_code": 200, "body": "[]"}}'
        ),
    )
    mock_parser.add_argument(
        "--responses",
        nargs="?",
        default=None,
        help="Path to JSON file with response mappings",
    )
    ############################################################################
    # endregion: Mock server parser
    ############################################################################

    ############################################################################
    # region: Proxy server parser
    ############################################################################
    proxy_parser = subparsers.add_parser("proxy", help="Run the proxy server")
    proxy_parser.add_argument("url", help="Target URL to proxy requests to")
    proxy_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="/dev/stdout",
        help="Output file to record requests and responses",
    )
    proxy_parser.add_argument(
        "indent", type=int, default=None, help="Indentation level for JSON output"
    )
    ############################################################################
    # endregion: Proxy server parser
    ############################################################################

    ############################################################################
    # region: Single request parser
    ############################################################################
    single_request_parser = subparsers.add_parser(
        "single-request", help="Serve a single request and print the request"
    )

    single_request_parser.add_argument(
        "url", nargs="?", default=None, help="URL to open in browser"
    )
    ############################################################################
    # endregion: Single request parser
    ############################################################################

    args: Args = parser.parse_args(argv)  # pyright: ignore[reportAssignmentType] # pyrefly: ignore[bad-assignment]
    level = max(logging.ERROR - (args.verbose * 10), logging.DEBUG)
    logging.basicConfig(
        level=level, format="[%(asctime)s] [%(levelname)-7s] [%(name)s] %(message)s"
    )
    logger.info(f"Arguments: {vars(args)=}")  # noqa: G004
    handler: Callable[[SimpleRequestEvent], SimpleResponseEvent]

    ############################################################################
    # region: Single request
    ############################################################################
    if args.command == "single-request":
        import json

        from dev_server.serve_single_request import serve_single_request

        url: str = args.url
        if url is not None:
            import sys
            import webbrowser

            logger.info("Opening browser for authentication: %s", url)
            if not webbrowser.open_new_tab(url):
                print(f"Please open {url} in your browser", file=sys.stderr)
        result = serve_single_request(
            handler=lambda x: x, port=args.port, host=args.host, timeout=args.timeout
        )
        print(json.dumps({**result, "content": result["content"].decode("utf-8")}, indent=2))
        return 0
    ############################################################################
    # endregion: Single request
    ############################################################################

    ############################################################################
    # region: Mock request
    ############################################################################
    if args.command == "mock":
        from dev_server.mock_handler import MockRequestHandler

        data = {}

        if args.responses:
            import json

            with open(args.responses) as f:
                data = json.load(f)

        handler = MockRequestHandler(default_response_mapping=data)
    ############################################################################
    # endregion: Mock request
    ############################################################################

    ############################################################################
    # region: Proxy request
    ############################################################################
    elif args.command == "proxy":
        from dev_server.proxy_recorder import ProxyRecorder

        handler = ProxyRecorder(base_url=args.url, output=args.output, json_indent=args.indent)
    ############################################################################
    # endregion: Proxy request
    ############################################################################
    else:
        msg = f"Unknown command: {args.command}"
        raise ValueError(msg)

    from dev_server.simple_server import SimpleServer

    server = SimpleServer(handler)
    server.serve_forever(host=args.host, port=args.port, timeout=args.timeout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
