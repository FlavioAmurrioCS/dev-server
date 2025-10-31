from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING

from dev_server.simple_server import clean_headers

if TYPE_CHECKING:
    import ssl
    from http.client import HTTPResponse

    from dev_server._types import RequestRecord
    from dev_server._types import ResponseRecord
    from dev_server.simple_server import SimpleRequestEvent
    from dev_server.simple_server import SimpleResponseEvent


@dataclass
class ProxyRecorder:
    base_url: str
    output: str = "/dev/stdout"
    timeout: float = 10.0
    json_indent: int | None = None

    def record(self, request: RequestRecord, response: ResponseRecord) -> None:
        with open(self.output, "a", encoding="utf-8") as f:
            json.dump(
                {
                    "base_url": self.base_url,
                    "request": request,
                    "response": response,
                },
                f,
                ensure_ascii=False,
                indent=self.json_indent,
            )
            f.write("\n")

    @cached_property
    def ssl_context(self) -> ssl.SSLContext:
        import ssl

        ret = ssl.create_default_context()
        ret.check_hostname = False
        ret.verify_mode = ssl.CERT_NONE
        return ret

    def __call__(self, request: SimpleRequestEvent) -> SimpleResponseEvent:
        request_record: RequestRecord = {
            "url": request["url"],
            "method": request["method"],
            "headers": request["headers"],
            "params": request["params"],
            "content": request["content"].decode("utf-8", errors="replace"),
        }
        query_string = urllib.parse.urlencode(
            request["params"], doseq=True, encoding="utf-8", errors="strict"
        )
        final_url = request["url"] if not query_string else f"{request['url']}?{query_string}"
        req = urllib.request.Request(  # noqa: S310
            url=self.base_url.rstrip("/") + final_url,
            method=request["method"],
            headers=request["headers"],
            data=request["content"],
        )
        response: HTTPResponse = urllib.request.urlopen(  # noqa: S310
            url=req,
            timeout=self.timeout,
            context=self.ssl_context,
        )
        response_record: ResponseRecord = {
            "status_code": response.getcode(),
            "headers": clean_headers(dict(response.getheaders())),
            "body": response.read().decode("utf-8", errors="replace"),
        }
        self.record(request_record, response_record)
        return {
            "status_code": response_record["status_code"],
            "headers": response_record["headers"],
            "body": [response_record["body"].encode("utf-8")],
        }


if __name__ == "__main__":
    from dev_server.simple_server import SimpleServer

    server = SimpleServer(
        request_handler=ProxyRecorder(
            base_url="https://raw.githubusercontent.com",
            json_indent=2,
            # output="records.jsonl"
        )
    )

    server.serve_forever()
    "http://127.0.0.1:3000/FlavioAmurrioCS/stream4py/refs/heads/main/src/stream4py/__init__.py?foo=bar"
