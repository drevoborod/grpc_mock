import json
from datetime import datetime, UTC
import re

import blackboxprotobuf
from jsonpath import jsonpath

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
        Before new mocks are saved, old ones are disabled.
        Old mocks are being located by package_name+service_name+method_name+filter.
        """
        root_structure = parse_proto_file(protos)
        for mock in mocks:
            await self._disable_old_mocks(
                package_name=mock.package,
                service_name=mock.service,
                method_name=mock.method,
                mock_filter=mock.filter,
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
                mock_filter=json.dumps(mock.filter),
                request_schema=json.dumps(method.request),
                response_schema=json.dumps(method.response),
                response_mock=json.dumps(mock.response, ensure_ascii=False),
                response_status=mock.response_status,
            )

    async def _disable_old_mocks(
        self,
        package_name: str,
        service_name: str,
        method_name: str,
        mock_filter: dict[str, str] | None,
    ):
        mocks = await self.get_mocks(
            package=package_name,
            service=service_name,
            method=method_name,
        )

        if mock_filter:
            mock_ids = [mock.id for mock in mocks if mock.filter == mock_filter]
        else:
            mock_ids = [mock.id for mock in mocks]

        await self.repo.update_mock(
            mock_ids,
            updated_at=datetime.now(UTC),
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
        ids = [x.id for x in await self.get_mocks(package=package, service=service, method=method)]
        await self.repo.update_mock(mock_ids=ids, updated_at=datetime.now(UTC), is_deleted=True)


class GRPCService:
    def __init__(self, mock_repo: MockRepo, log_repo: LogRepo):
        self.mock_repo = mock_repo
        self.log_repo = log_repo

    async def process_grpc(
        self, package: str, service: str, method: str, payload: bytes
    ) -> tuple[bytes, int]:
        storage_mocks = (
            await self.mock_repo.get_mocks_from_storage(
                package=package,
                service=service,
                method=method,
            )
        )

        # Let's assume that any corresponding DB record does contain suitable schema:
        request_data, _ = blackboxprotobuf.decode_message(
            payload[5:], storage_mocks[0].request_schema
        )
        for mock in storage_mocks:
            if mock.filter:
                if self._compare_request_to_filter(request_data, mock.filter):
                    break
        else:
            mock = storage_mocks[0]

        await self.log_repo.store_log(
            mock_id=mock.id,
            request_data=request_data,
            response_data=mock.response_mock,
            response_status=mock.response_status,
        )
        response_data = blackboxprotobuf.encode_message(
            mock.response_mock, mock.response_schema
        )
        return (
            (
                (0).to_bytes()
                + len(response_data).to_bytes(4, "big", signed=False)
                + response_data
            ),
            mock.response_status,
        )

    def _compare_request_to_filter(self, request: dict, mock_filter: dict) -> bool:
        """
        Verifies request against all values in the filter.

        :param request: gRPC request data as dictionary.
        :param mock_filter: dictionary which keys are json path strings and values are regular expressions.
        """

        for json_path, regexp in mock_filter.items():
            data = jsonpath(request, json_path)
            if not data:
                return False
            # jsonpath returns a list, so we need to check its first item:
            if not re.match(regexp, str(data[0])):
                return False
        return True
