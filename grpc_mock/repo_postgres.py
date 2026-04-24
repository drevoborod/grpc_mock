import json
from datetime import datetime

from databases import Database

from grpc_mock.db_structure import TableNames
from grpc_mock.models import (
    GrpcMockFromStorage,
    LogFromStorage,
    RestMockFromStorage,
)
from grpc_mock.repo import DatabaseError, LogRepo, MockRepo, MockType


class _RepoPostgres:
    def __init__(self, db: Database) -> None:
        self.db = db


class MockRepoPostgres(_RepoPostgres, MockRepo):
    async def get_grpc_mocks_from_storage(
        self, package: str, service: str, method: str
    ) -> list[GrpcMockFromStorage]:
        db_data = await self.db.fetch_all(
            f"select id, request_schema, response_schema, response_mock, response_status, filter "
            f"from {TableNames.GRPC_MOCKS} where package_name=:package_name and service_name=:service_name "
            f"and method_name=:method_name and is_deleted is false",
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
            GrpcMockFromStorage(
                id=x.id,
                request_schema=json.loads(x.request_schema),
                response_schema=json.loads(x.response_schema),
                response_mock=json.loads(x.response_mock),
                filter=json.loads(x.filter),
                response_status=x.response_status,
            )
            for x in db_data
        ]

    async def get_rest_mocks_from_storage(
        self, endpoint: str, method: str
    ) -> list[RestMockFromStorage]:
        db_data = await self.db.fetch_all(
            f"select id, query_params_filter, body_filter, headers_filter, "
            f"response_body, response_headers, response_status "
            f"from {TableNames.REST_MOCKS} where endpoint=:endpoint and method=:method and is_deleted is false",
            values=dict(
                endpoint=endpoint,
                method=method,
            ),
        )
        if not db_data:
            raise DatabaseError(
                f"Mocks not found. Search fields: endpoint={endpoint}, method={method}"
            )
        return [
            RestMockFromStorage(
                id=x.id,
                query_params_filter=json.loads(x.query_params_filter),
                body_filter=json.loads(x.body_filter),
                headers_filter=json.loads(x.headers_filter),
                response_body=x.response_body,
                response_headers=json.loads(x.response_headers),
                response_status=x.response_status,
            )
            for x in db_data
        ]

    async def update_mock(
        self, mock_type: MockType, mock_ids: list[int], updated_at: datetime, is_deleted: bool = True
    ) -> None:
        table = TableNames.GRPC_MOCKS if mock_type == MockType.grpc else TableNames.REST_MOCKS
        await self.db.execute_many(
            f"update {table} set is_deleted=:is_deleted, updated_at=:updated_at where id=:id",
            values=[
                {
                    "is_deleted": is_deleted,
                    "updated_at": updated_at,
                    "id": mock_id,
                }
                for mock_id in mock_ids
            ],
        )

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
        await self.db.execute(
            f"insert into {TableNames.GRPC_MOCKS} "
            "(config_uuid, package_name, service_name, method_name, filter, request_schema, response_schema, "
            "response_mock, response_status, is_deleted) "
            "values (:config_uuid, :package_name, :service_name, :method_name, :filter, :request_schema, :response_schema, "
            ":response_mock, :response_status, :is_deleted)",
            values=dict(
                config_uuid=config_uuid,
                package_name=package_name,
                service_name=service_name,
                method_name=method_name,
                filter=mock_filter,
                request_schema=request_schema,
                response_schema=response_schema,
                response_mock=response_mock,
                response_status=response_status,
                is_deleted=False,
            ),
        )

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
        await self.db.execute(
            f"insert into {TableNames.REST_MOCKS} "
            "(config_uuid, endpoint, method, query_params_filter, body_filter, headers_filter, response_body, "
            "response_headers, response_status, is_deleted) "
            "values (:config_uuid, :endpoint, :method, :query_params_filter, :body_filter, :headers_filter, "
            ":response_body, :response_headers, :response_status, :is_deleted)",
            values=dict(
                config_uuid=config_uuid,
                endpoint=endpoint,
                method=method,
                query_params_filter=query_params_filter,
                body_filter=body_filter,
                headers_filter=headers_filter,
                response_body=response_body,
                response_headers=response_headers,
                response_status=response_status,
                is_deleted=False,
            ),
        )


class LogRepoPostgres(_RepoPostgres, LogRepo):
    async def get_grpc_log(
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

        clause = " and ".join([f"{TableNames.GRPC_MOCKS}.{key}=:{key}" for key in query_params])
        if clause:
            clause = f" where {clause}"

        result = await self.db.fetch_all(
            f"select {TableNames.GRPC_MOCKS}.config_uuid, {TableNames.GRPC_LOGS}.request, "
            f"{TableNames.GRPC_LOGS}.response, {TableNames.GRPC_LOGS}.response_status, "
            f"{TableNames.GRPC_LOGS}.created_at from {TableNames.GRPC_MOCKS} "
            f"join {TableNames.GRPC_LOGS} on {TableNames.GRPC_MOCKS}.id={TableNames.GRPC_LOGS}.mock_id "
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

    async def get_rest_log(
        self,
        endpoint: str | None,
        method: str | None,
        config_uuid: str | None,
    ) -> list[LogFromStorage]:
        query_params = {}
        if endpoint:
            query_params["endpoint"] = endpoint
        if method:
            query_params["method"] = method
        if config_uuid:
            query_params["config_uuid"] = config_uuid

        clause = " and ".join([f"{TableNames.REST_MOCKS}.{key}=:{key}" for key in query_params])
        if clause:
            clause = f" where {clause}"

        result = await self.db.fetch_all(
            f"select {TableNames.REST_MOCKS}.config_uuid, {TableNames.REST_LOGS}.request, "
            f"{TableNames.REST_LOGS}.response, {TableNames.REST_LOGS}.response_status, "
            f"{TableNames.REST_LOGS}.created_at from {TableNames.REST_MOCKS} "
            f"join {TableNames.REST_LOGS} on {TableNames.REST_MOCKS}.id={TableNames.REST_LOGS}.mock_id "
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
        mock_type: MockType,
        mock_id: int,
        request_data: dict,
        response_data: dict,
        response_status: int,
    ) -> None:
        table = TableNames.GRPC_LOGS if mock_type == MockType.grpc else TableNames.REST_LOGS
        await self.db.execute(
            f"insert into {table} (mock_id, request, response, response_status) values (:mock_id, :request, :response, :response_status)",
            values={
                "mock_id": mock_id,
                "request": json.dumps(request_data, ensure_ascii=False),
                "response": json.dumps(response_data, ensure_ascii=False),
                "response_status": response_status,
            },
        )
