from dataclasses import dataclass
from datetime import datetime, UTC
import json
from collections.abc import Mapping

from grpc_mock.db import DbConnection
from grpc_mock.proto_utils import (
    ProtoMethodStructure,
    parse_proto_file,
    ProtoMethod,
)
from grpc_mock.config import Config


class StorageError(Exception):
    pass


@dataclass
class StorageMock:
    id: int
    request_schema: dict
    response_schema: dict
    response_mock: dict


async def get_mock_from_storage(
    proto_structure: ProtoMethodStructure, config: Config,
) -> StorageMock:
    async with DbConnection(config) as db:
        db_data = await db.select_one(
            "select id, request_schema, response_schema, response_mock "
            "from mocks where package_name=:package_name and service_name=:service_name "
            "and method_name=:method_name and is_deleted is false",
            values=dict(
                package_name=proto_structure.package,
                service_name=proto_structure.service,
                method_name=proto_structure.method,
            ),
        )
    return StorageMock(
        id=db_data.id,
        request_schema=json.loads(db_data.request_schema),
        response_schema=json.loads(db_data.response_schema),
        response_mock=json.loads(db_data.response_mock),
    )


async def store_mock(mock_request_body: dict, config: Config):
    """
    Parse mocks from a configuration request and save them to the storage.
    """
    package_structure = parse_proto_file(mock_request_body["proto"])
    mock_mapping = {}
    for mock in mock_request_body["mocks"]:
        method_mock_mapping = mock_mapping.get(mock["service"], {})
        method_mock_mapping.update({mock["method"]: mock["response"]})
        mock_mapping[mock["service"]] = method_mock_mapping
    async with DbConnection(config) as db:
        for service_name, service in package_structure.services.items():
            for method_name, method in service.methods.items():
                await _add_mock_to_db(
                    db,
                    config_uuid=mock_request_body["config_uuid"],
                    package_name=package_structure.name,
                    service_name=service_name,
                    method_name=method_name,
                    method=method,
                    response_mock=mock_mapping[service_name][method_name],
                )


async def _add_mock_to_db(
    db: DbConnection,
    config_uuid: str,
    package_name: str,
    service_name: str,
    method_name: str,
    method: ProtoMethod,
    response_mock: dict,
):
    previous = await db.select_all(
        "select id from mocks where package_name=:package_name "
        "and service_name=:service_name and method_name=:method_name and is_deleted is false",
        values={
            "package_name": package_name,
            "service_name": service_name,
            "method_name": method_name,
        },
    )
    for item in previous:
        await db.execute(
            "update mocks set is_deleted=true, updated_at=:updated_at where id=:id",
            values={"updated_at": datetime.now(UTC), "id": item.id},
        )

    await db.execute(
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


async def get_route_log(query_params: Mapping, config: Config,) -> dict[str, list]:
    query_params = {
        "package_name": query_params.get("package"),
        "service_name": query_params.get("service"),
        "method_name": query_params.get("method"),
        "config_uuid": query_params.get("config_uuid"),
    }
    keys_to_remove = [key for key, value in query_params.items() if not value]
    for key in keys_to_remove:
        query_params.pop(key)
    clause = " and ".join([f"mocks.{key}=:{key}" for key in query_params])
    if clause:
        clause = f" where {clause}"
    async with DbConnection(config) as db:
        result = await db.select_all(
            f"select mocks.config_uuid, logs.request, logs.response, logs.created_at from mocks "
            f"join logs on mocks.id=logs.mock_id "
            f"{clause}",
            values=query_params,
        )
    return {
        "logs": [
            json.dumps(dict(x), ensure_ascii=False, default=str) for x in result
        ]
    }


async def store_log(mock_id: int, request_data: dict, response_data: dict, config: Config, ):
    async with DbConnection(config) as db:
        await db.execute(
            "insert into logs (mock_id, request, response) values (:mock_id, :request, :response)",
            values={
                "mock_id": mock_id,
                "request": json.dumps(request_data, ensure_ascii=False),
                "response": json.dumps(response_data, ensure_ascii=False),
            },
        )
