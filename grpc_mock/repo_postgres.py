import json
from datetime import datetime

from databases import Database

from grpc_mock.models import LogFromStorage, MockFromStorage
from grpc_mock.repo import MockRepo, LogRepo, DatabaseError


class _RepoPostgres:
    def __init__(self, db: Database) -> None:
        self.db = db


class MockRepoPostgres(_RepoPostgres, MockRepo):
    async def get_mocks_from_storage(
        self, package: str, service: str, method: str
    ) -> list[MockFromStorage]:
        db_data = await self.db.fetch_all(
            "select id, request_schema, response_schema, response_mock, response_status, filter "
            "from mocks where package_name=:package_name and service_name=:service_name "
            "and method_name=:method_name and is_deleted is false",
            values=dict(
                package_name=package,
                service_name=service,
                method_name=method,
            ),
        )
        if not db_data:
            raise DatabaseError(
                f"Mocks not found. Search fields: package_name={package}, service_name={service}, method_name={method}"
            )
        return [
            MockFromStorage(
                id=x.id,
                request_schema=json.loads(x.request_schema),
                response_schema=json.loads(x.response_schema),
                response_mock=json.loads(x.response_mock),
                filter=json.loads(x.filter),
                response_status=x.response_status,
            )
            for x in db_data
        ]

    async def update_mock(
        self, mock_ids: list[int], updated_at: datetime, is_deleted: bool = True
    ):
        await self.db.execute_many(
            "update mocks set is_deleted=:is_deleted, updated_at=:updated_at where id=:id",
            values=[
                {
                    "is_deleted": is_deleted,
                    "updated_at": updated_at,
                    "id": x,
                }
                for x in mock_ids
            ],
        )

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
        await self.db.execute(
            "insert into mocks "
            "(config_uuid, package_name, service_name, method_name, filter, request_schema, response_schema, "
            "response_mock, response_status, is_deleted) "
            "values (:config_uuid, :package_name, :service_name, :method_name, :mock_filter, :request_schema, :response_schema, "
            ":response_mock, :response_status, :is_deleted)",
            values=dict(
                config_uuid=config_uuid,
                package_name=package_name,
                service_name=service_name,
                method_name=method_name,
                mock_filter=mock_filter,
                request_schema=request_schema,
                response_schema=response_schema,
                response_mock=response_mock,
                response_status=response_status,
                is_deleted=False,
            ),
        )


class LogRepoPostgres(_RepoPostgres, LogRepo):
    async def get_route_log(
        self,
        package: str | None,
        service: str | None,
        method: str | None,
        config_uuid: str | None,
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
            f"select mocks.config_uuid, logs.request, logs.response, logs.response_status, logs.created_at from mocks "
            f"join logs on mocks.id=logs.mock_id "
            f"{clause}",
            values=query_params,
        )
        return [
            LogFromStorage(
                config_uuid=item.config_uuid,
                request=json.loads(item.request),
                response=json.loads(item.response),
                response_status=item.response_status,
                created_at=item.created_at,
            )
            for item in result
        ]

    async def store_log(
        self,
        mock_id: int,
        request_data: dict,
        response_data: dict,
        response_status: int,
    ) -> None:
        await self.db.execute(
            "insert into logs (mock_id, request, response, response_status) values (:mock_id, :request, :response, :response_status)",
            values={
                "mock_id": mock_id,
                "request": json.dumps(request_data, ensure_ascii=False),
                "response": json.dumps(response_data, ensure_ascii=False),
                "response_status": response_status,
            },
        )
