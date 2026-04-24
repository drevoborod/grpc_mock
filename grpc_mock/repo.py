from datetime import datetime
from enum import Enum
from typing import Protocol

from grpc_mock.models import LogFromStorage, GrpcMockFromStorage, RestMockFromStorage


class MockType(Enum):
    rest = 1
    grpc = 2


class DatabaseError(Exception):
    pass


class MockRepo(Protocol):
    async def get_grpc_mocks_from_storage(
        self, package: str, service: str, method: str
    ) -> list[GrpcMockFromStorage]:
        ...

    async def update_mock(
        self, mock_type: MockType, mock_ids: list[int], updated_at: datetime, is_deleted: bool = True
    ) -> None:
        ...

    async def add_grpc_mock_to_storage(
        self,
        config_uuid: str,
        package_name: str,
        service_name: str,
        method_name: str,
        mock_filter: str,
        request_schema: str,
        response_schema: str,
        response_mock: str,
        response_status: int | None,
    ) -> None:
        ...

    async def add_rest_mock_to_storage(
        self,
        config_uuid: str,
        endpoint: str,
        method: str,
        query_params_filter: str | None,
        body_filter: str | None,
        headers_filter: str | None,
        response_body: str | None,
        response_headers: str | None,
        response_status: int,
    ) -> None:
        ...

    async def get_rest_mocks_from_storage(
        self, endpoint: str, method: str
    ) -> list[RestMockFromStorage]:
        ...


class LogRepo(Protocol):
    async def get_grpc_log(
        self,
        package: str | None,
        service: str | None,
        method: str | None,
        config_uuid: str | None,
    ) -> list[LogFromStorage]:
        ...

    async def get_rest_log(
        self,
        endpoint: str | None,
        method: str | None,
        config_uuid: str | None,
    ) -> list[LogFromStorage]:
        ...

    async def store_log(
        self,
        mock_type: MockType,
        mock_id: int,
        request_data: dict,
        response_data: dict,
        response_status: int,
    ) -> None:
        ...
