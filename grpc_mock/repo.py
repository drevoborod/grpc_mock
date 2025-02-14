import json
from datetime import datetime, UTC

from databases import Database

from grpc_mock.proto_utils import parse_proto_file, ProtoMethod
from grpc_mock.schemas import Mock
from grpc_mock.models import LogFromStorage, MockFromStorage


class StorageError(Exception):
    pass


class _Repo:
    def __init__(self, db: Database) -> None:
        self.db = db


class MockRepo(_Repo):
    async def get_mock_from_storage(self, package: str, service: str, method: str) -> MockFromStorage:
        db_data = await self.db.fetch_one(
            "select id, request_schema, response_schema, response_mock "
            "from mocks where package_name=:package_name and service_name=:service_name "
            "and method_name=:method_name and is_deleted is false",
            values=dict(
                package_name=package,
                service_name=service,
                method_name=method,
            ),
        )
        return MockFromStorage(
            id=db_data.id,
            request_schema=json.loads(db_data.request_schema),
            response_schema=json.loads(db_data.response_schema),
            response_mock=json.loads(db_data.response_mock),
        )


    async def store_mock(self, proto: str, config_uuid: str, mocks: list[Mock]) -> None:
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
                await self._add_mock_to_db(
                    config_uuid=config_uuid,
                    package_name=package_structure.name,
                    service_name=service_name,
                    method_name=method_name,
                    method=method,
                    response_mock=mock_mapping[service_name][method_name],
                )

    async def _add_mock_to_db(
            self,
            config_uuid: str,
            package_name: str,
            service_name: str,
            method_name: str,
            method: ProtoMethod,
            response_mock: dict,
    ) -> None:
        previous = await self.db.fetch_all(
            "select id from mocks where package_name=:package_name "
            "and service_name=:service_name and method_name=:method_name and is_deleted is false",
            values={
                "package_name": package_name,
                "service_name": service_name,
                "method_name": method_name,
            },
        )
        for item in previous:
            await self.db.execute(
                "update mocks set is_deleted=true, updated_at=:updated_at where id=:id",
                values={"updated_at": datetime.now(UTC), "id": item.id},
            )

        await self.db.execute(
            "insert into mocks (config_uuid, package_name, service_name, method_name, request_schema, response_schema, response_mock, is_deleted) "
            "values (:config_uuid, :package_name, :service_name, :method_name, :request_schema, :response_schema, :response_mock, :is_deleted)",
            values=dict(
                config_uuid=config_uuid,
                package_name=package_name,
                service_name=service_name,
                method_name=method_name,
                request_schema=json.dumps(method.request),
                response_schema=json.dumps(method.response),
                response_mock=json.dumps(response_mock, ensure_ascii=False),
                is_deleted=False,
            ),
        )


class LogRepo(_Repo):
    async def get_route_log(
            self, package: str | None, service: str | None, method: str | None, config_uuid: str | None,
    ) -> list[LogFromStorage]:

        query_params = {}
        if package:
            query_params["package_name"] = package
        if service:
            query_params["service_name"] = service
        if method:
            query_params["method_name"] = method
        if config_uuid:
            query_params["config_uuid"] = config_uuid

        clause = " and ".join([f"mocks.{key}=:{key}" for key in query_params])
        if clause:
            clause = f" where {clause}"
        result = await self.db.fetch_all(
            f"select mocks.config_uuid, logs.request, logs.response, logs.created_at from mocks "
            f"join logs on mocks.id=logs.mock_id "
            f"{clause}",
            values=query_params,
        )
        return [
            LogFromStorage(
                config_uuid=item.config_uuid,
                request=json.loads(item.request),
                response=json.loads(item.response),
                created_at=item.created_at,
            )
            for item in result
        ]


    async def store_log(self, mock_id: int, request_data: dict, response_data: dict) -> None:
        await self.db.execute(
            "insert into logs (mock_id, request, response) values (:mock_id, :request, :response)",
            values={
                "mock_id": mock_id,
                "request": json.dumps(request_data, ensure_ascii=False),
                "response": json.dumps(response_data, ensure_ascii=False),
            },
        )
