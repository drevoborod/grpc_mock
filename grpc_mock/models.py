from dataclasses import dataclass
from datetime import datetime


@dataclass
class MockFromStorage:
    id: int
    request_schema: dict
    response_schema: dict
    response_mock: dict


@dataclass
class LogFromStorage:
    config_uuid: str
    request: dict
    response: dict
    created_at: str

    def __post_init__(self):
        self.created_at = str(self.created_at)
