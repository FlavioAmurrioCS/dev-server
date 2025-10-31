from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING
from typing import NamedTuple
from urllib.parse import parse_qs

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping
    from collections.abc import MutableMapping
    from typing import Callable
    from typing import Literal
    from typing import TypedDict
    from wsgiref.simple_server import WSGIServer

    from _typeshed.wsgi import ErrorStream
    from _typeshed.wsgi import InputStream
    from _typeshed.wsgi import StartResponse

    Environ = TypedDict(
        "Environ",
        {
            "REQUEST_METHOD": str,
            "SCRIPT_NAME": str,
            "PATH_INFO": str,
            "QUERY_STRING": str,
            "SERVER_PROTOCOL": str,
            "wsig.version": tuple[int, int],
            "wsgi.url_scheme": str,
            "wsgi.input": InputStream,
            "wsgi.errors": ErrorStream,
            "wsgi.multithread": bool,
            "wsgi.multiprocess": bool,
            "wsgi.run_once": bool,
            "SERVER_NAME": str,
            "SERVER_PORT": int,
            "REMOTE_ADDR": str,
        },
    )

    HTTP_METHOD = Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"]

    class SimpleRequestEvent(TypedDict):
        url: str
        method: HTTP_METHOD
        headers: MutableMapping[str, str]
        params: dict[str, list[str]]
        content: bytes

    class SimpleResponseEvent(TypedDict):
        status_code: int
        headers: MutableMapping[str, str]
        body: Iterable[bytes]


logger = logging.getLogger(__name__)


def clean_headers(headers: Mapping[str, str]) -> dict[str, str]:
    # Need to remove hop-by-hop headers
    # https://github.com/python/cpython/blob/24b147a19b360c49cb1740aa46211d342aaa071f/Lib/wsgiref/util.py#L151
    hop_by_hop_headers = {
        "CONNECTION",
        "KEEP-ALIVE",
        "PROXY-AUTHENTICATE",
        "PROXY-AUTHORIZATION",
        "TE",
        "TRAILERS",
        "TRANSFER-ENCODING",
        "UPGRADE",
        "CONTENT-ENCODING",
    }

    return {k: v for k, v in headers.items() if k.upper() not in hop_by_hop_headers}


class SimpleServer(NamedTuple):
    request_handler: Callable[[SimpleRequestEvent], SimpleResponseEvent]

    def _extract_headers(self, environ: Environ | dict[str, str]) -> dict[str, str]:
        headers = {}
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                headers[key[5:].replace("_", "-")] = value  # pyrefly: ignore[unsupported-operation]
            elif key in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                headers[key.replace("_", "-")] = value  # pyrefly: ignore[unsupported-operation]
        headers.pop("HOST", None)
        return headers  # type: ignore[return-value]

    def get_request_event(self, environ: Environ) -> SimpleRequestEvent:
        headers = self._extract_headers(environ)
        content_length = int(headers.pop("CONTENT-LENGTH", "") or "0")
        body = environ["wsgi.input"].read(content_length)

        return {
            "method": environ["REQUEST_METHOD"],  # type: ignore[typeddict-item]
            "url": environ["PATH_INFO"],
            "headers": headers,
            "params": parse_qs(environ["QUERY_STRING"]),
            "content": body,
        }

    def __call__(self, environ: Environ, start_response: StartResponse) -> Iterable[bytes]:
        request_event = self.get_request_event(environ)
        response_event = self.request_handler(request_event)
        status_code = response_event["status_code"]
        phrase = HTTPStatus(status_code).phrase
        headers = response_event["headers"]
        headers = clean_headers(headers)
        start_response(f"{status_code} {phrase}", list(headers.items()))
        return response_event["body"]

    def make_server(self, host: str = "127.0.0.1", port: int = 3000) -> WSGIServer:
        from wsgiref.simple_server import make_server

        return make_server(host, port, self)  # type: ignore[arg-type]

    def serve_forever(
        self, host: str = "127.0.0.1", port: int = 3000, timeout: float | None = None
    ) -> None:
        with self.make_server(host, port) as httpd:
            httpd.timeout = timeout
            sa = httpd.socket.getsockname()
            server_host, server_port = sa[0], sa[1]
            logger.info("Running on http://%s:%d", server_host, server_port)
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                logger.info("Shutting down server")
