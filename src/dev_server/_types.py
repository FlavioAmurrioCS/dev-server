from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import MutableMapping
    from typing import TypedDict

    from dev_server.simple_server import HTTP_METHOD

    class RequestRecord(TypedDict):
        url: str
        method: HTTP_METHOD
        headers: MutableMapping[str, str]
        params: dict[str, list[str]]
        content: str

    class ResponseRecord(TypedDict):
        status_code: int
        headers: MutableMapping[str, str]
        body: str
