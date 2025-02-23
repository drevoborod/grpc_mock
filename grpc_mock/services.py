import json
from datetime import datetime, UTC

import blackboxprotobuf

from grpc_mock.models import MockFromStorage
from grpc_mock.proto_parser import parse_proto_file, ProtoMethod
from grpc_mock.repo import MockRepo, LogRepo, DatabaseError
from grpc_mock.schemas import (
    MockFromSetRequest,
    DefaultResponse,
    MockFromGetRequest,
)


class MockService:
    def __init__(self, repo: MockRepo):
        self.repo = repo

    async def store_mocks(
        self,
        protos: list[str],
        config_uuid: str,
        mocks: list[MockFromSetRequest],
    ) -> None:
        """
        Parse mocks from a configuration request and save them to the storage.
        """
        root_structure = parse_proto_file(protos)
        for mock in mocks:
            await self._disable_old_mocks(
                package_name=mock.package,
                service_name=mock.service,
                method_name=mock.method,
            )

            method: ProtoMethod = (
                root_structure.packages[mock.package]
                .services[mock.service]
                .methods[mock.method]
            )

            await self.repo.add_mock_to_db(
                config_uuid=config_uuid,
                package_name=mock.package,
                service_name=mock.service,
                method_name=mock.method,
                request_schema=json.dumps(method.request),
                response_schema=json.dumps(method.response),
                response_mock=json.dumps(mock.response, ensure_ascii=False),
            )

    async def _disable_old_mocks(
        self,
        package_name: str,
        service_name: str,
        method_name: str,
    ):
        mock_ids = await self.repo.get_enabled_mock_ids(
            package_name=package_name,
            service_name=service_name,
            method_name=method_name,
        )
        now = datetime.now(UTC)
        await self.repo.update_mock(
            mock_ids,
            updated_at=now,
            is_deleted=True,
        )

    async def get_mocks(
        self, package, service, method
    ) -> list[MockFromStorage]:
        try:
            res = await self.repo.get_mocks_from_storage(
                package=package, service=service, method=method
            )
        except DatabaseError:
            return []
        return res

    async def delete_mocks(self, package, service, method) -> None:
        ids = await self.repo.get_enabled_mock_ids(
            package_name=package, service_name=service, method_name=method
        )
        now = datetime.now(UTC)
        await self.repo.update_mock(mock_ids=ids, updated_at=now)


class GRPCService:
    def __init__(self, mock_repo: MockRepo, log_repo: LogRepo):
        self.mock_repo = mock_repo
        self.log_repo = log_repo

    async def process_grpc(
        self, package: str, service: str, method: str, payload: bytes
    ) -> bytes:
        storage_mock = (
            await self.mock_repo.get_mocks_from_storage(
                package=package,
                service=service,
                method=method,
            )
        )[0]
        request_data, _ = blackboxprotobuf.decode_message(
            payload[5:], storage_mock.request_schema
        )
        await self.log_repo.store_log(
            storage_mock.id, request_data, storage_mock.response_mock
        )
        response_data = blackboxprotobuf.encode_message(
            storage_mock.response_mock, storage_mock.response_schema
        )
        return (
            (0).to_bytes()
            + len(response_data).to_bytes(4, "big", signed=False)
            + response_data
        )
