from __future__ import annotations

import json
from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from typing_extensions import NotRequired
    from typing_extensions import TypedDict

    from dev_server._types import RequestRecord
    from dev_server.simple_server import SimpleRequestEvent
    from dev_server.simple_server import SimpleResponseEvent

    class PreDeterminedResponses(TypedDict):
        status_code: int
        headers: NotRequired[MutableMapping[str, str]]
        body: NotRequired[str]

    PreDeterminedResponsesMapping = MutableMapping[str, PreDeterminedResponses]

pre_determined_responses_map: PreDeterminedResponsesMapping = {
    "GET:/_ping": {
        "status_code": 200,
        "body": "pong",
    },
}


@dataclass
class MockRequestHandler:
    default_response_mapping: PreDeterminedResponsesMapping = field(default_factory=dict)
    requests: list[RequestRecord] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.default_response_mapping.update(pre_determined_responses_map)

    def __call__(self, request: SimpleRequestEvent) -> SimpleResponseEvent:
        key = f"{request['method']}:{request['url']}"
        if key == "GET:/_requests":
            ret = self.requests
            if request.get("params", {}).get("clear"):
                ret = [*self.requests]
                self.requests.clear()
            if request.get("params", {}).get("last"):
                ret = ret[-1:]
            return {
                "status_code": 200,
                "headers": {"Content-Type": "application/json"},
                "body": [json.dumps(ret).encode("utf-8")],
            }
        if key in self.default_response_mapping:
            resp = self.default_response_mapping[key]
            return {
                "status_code": resp["status_code"],
                "headers": resp.get("headers", {}),
                "body": [resp.get("body", "").encode("utf-8")],
            }
        record: RequestRecord = {
            "url": request["url"],
            "method": request["method"],
            "headers": request["headers"],
            "params": request["params"],
            "content": request["content"].decode("utf-8", errors="replace"),
        }
        self.requests.append(record)
        return {
            "status_code": 200,
            "headers": {"Content-Type": "application/json"},
            "body": [json.dumps(record).encode("utf-8")],
        }


if __name__ == "__main__":
    from dev_server.simple_server import SimpleServer

    server = SimpleServer(request_handler=MockRequestHandler())

    server.serve_forever()
