import json
from datetime import datetime, UTC

import blackboxprotobuf

from grpc_mock.proto_parser import parse_proto_file
from grpc_mock.repo import MockRepo, LogRepo
from grpc_mock.schemas import RequestMock, DefaultResponse


class MockService:
    def __init__(self, repo: MockRepo):
        self.repo = repo

    async def store_mock(
        self, protos: list[str], config_uuid: str, mocks: list[RequestMock]
    ) -> DefaultResponse:
        """
        Parse mocks from a configuration request and save them to the storage.
        """
        root_structure = parse_proto_file(protos)
        mock_mapping = {}
        for mock in mocks:
            package_mapping = mock_mapping.get(mock.package, {})
            service_mapping = package_mapping.get(mock.service, {})
            service_mapping[mock.method] = mock.response
            package_mapping[mock.service] = service_mapping
            mock_mapping[mock.package] = package_mapping

        for package_name, package in root_structure.packages.items():
            for service_name, service in package.services.items():
                for method_name, method in service.methods.items():
                    await self._disable_old_mocks(
                        package_name=package_name,
                        service_name=service_name,
                        method_name=method_name,
                    )
                    await self.repo.add_mock_to_db(
                        config_uuid=config_uuid,
                        package_name=package_name,
                        service_name=service_name,
                        method_name=method_name,
                        request_schema=json.dumps(method.request),
                        response_schema=json.dumps(method.response),
                        response_mock=json.dumps(
                            mock_mapping[package_name][service_name][
                                method_name
                            ],
                            ensure_ascii=False,
                        ),
                    )
        return DefaultResponse(
            status="ok",
            message="Mock configuration added successfully",
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
        for mock_id in mock_ids:
            await self.repo.update_mock(
                mock_id,
                updated_at=now,
                is_deleted=True,
            )


class GRPCService:
    def __init__(self, mock_repo: MockRepo, log_repo: LogRepo):
        self.mock_repo = mock_repo
        self.log_repo = log_repo

    async def process_grpc(
        self, package: str, service: str, method: str, payload: bytes
    ) -> bytes:
        storage_mock = await self.mock_repo.get_mock_from_storage(
            package=package,
            service=service,
            method=method,
        )
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
