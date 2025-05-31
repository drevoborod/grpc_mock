from dataclasses import dataclass


@dataclass
class MockFromStorage:
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
