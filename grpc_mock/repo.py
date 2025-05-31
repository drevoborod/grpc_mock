from datetime import datetime
from typing import Protocol

from grpc_mock.models import LogFromStorage, MockFromStorage


class DatabaseError(Exception):
    pass


class MockRepo(Protocol):
    async def get_mocks_from_storage(
        self, package: str, service: str, method: str
    ) -> list[MockFromStorage]:
        ...

    async def update_mock(
        self, mock_ids: list[int], updated_at: datetime, is_deleted: bool = True
    ) -> None:
        ...

    async def add_mock_to_db(
        self,
        config_uuid: str,
        package_name: str,
        service_name: str,
        method_name: str,
        mock_filter: str,
        request_schema: str,
        response_schema: str,
        response_mock: str,
        response_status: int,
    ) -> None:
        ...


class LogRepo(Protocol):
    async def get_route_log(
        self,
        package: str | None,
        service: str | None,
        method: str | None,
        config_uuid: str | None,
    ) -> list[LogFromStorage]:
        ...

    async def store_log(
        self,
        mock_id: int,
        request_data: dict,
        response_data: dict,
        response_status: int,
    ) -> None:
        ...
