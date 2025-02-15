import json
from datetime import datetime, UTC

from databases import Database
from starlette import status
from starlette.responses import JSONResponse

from grpc_mock.proto_parser import parse_proto_file
from grpc_mock.repo import MockRepo
from grpc_mock.schemas import RequestMock, DefaultResponse


class MockService:
    def __init__(self, repo: MockRepo):
        self.repo = repo

    async def store_mock(self, proto: str, config_uuid: str, mocks: list[RequestMock]) -> None:
        """
        Parse mocks from a configuration request and save them to the storage.
        """
        package_structure = parse_proto_file(proto)
        mock_mapping = {}
        for mock in mocks:
            method_mock_mapping = mock_mapping.get(mock.service, {})
            method_mock_mapping.update({mock.method: mock.response})
            mock_mapping[mock.service] = method_mock_mapping

        for service_name, service in package_structure.services.items():
            for method_name, method in service.methods.items():
                await self._disable_old_mocks(
                    package_name=package_structure.name,
                    service_name=service_name,
                    method_name=method_name,
                )
                await self.repo.add_mock_to_db(
                    config_uuid=config_uuid,
                    package_name=package_structure.name,
                    service_name=service_name,
                    method_name=method_name,
                    request_schema=json.dumps(method.request),
                    response_schema=json.dumps(method.response),
                    response_mock=json.dumps(mock_mapping[service_name][method_name], ensure_ascii=False),
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
                mock_id, updated_at=now, is_deleted=True,
            )

    async def get_mock(self): pass


def prepare_default_response(
    message: str, status_code: status = status.HTTP_200_OK
) -> DefaultResponse:
    return DefaultResponse(
        status="ok",
        message=message,
        status_code=status_code,
    )


def prepare_error_response(
    message: str, status_code: status = status.HTTP_400_BAD_REQUEST
) -> DefaultResponse:
    return DefaultResponse(
        status="error",
        message=message,
        status_code=status_code,
    )
