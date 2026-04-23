from dataclasses import dataclass

import json


@dataclass
class GrpcMockFromStorage:
    id: int
    request_schema: dict
    response_schema: dict
    response_mock: dict
    response_status: int
    filter: dict[str, str] | None


@dataclass
class LogFromStorage:
    config_uuid: str
    request: dict
    response: dict
    response_status: int
    created_at: str

    def __post_init__(self):
        self.created_at = str(self.created_at)


@dataclass
class RestMockFromStorage:
    id: int
    query_params_filter: dict | None
    body_filter: dict | None
    headers_filter: dict | None
    response_body: str | dict | None
    response_headers: dict | None
    response_status: int

    def __post_init__(self):
        try:
            self.response_body = json.loads(self.response_body)
        except json.decoder.JSONDecodeError:
            pass
