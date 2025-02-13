from datetime import datetime, UTC
import json

from grpc_mock.db import DbConnection
from grpc_mock.proto_utils import ProtoMethodStructure, parse_proto_file, ProtoMethod


class StorageError(Exception): pass


async def get_proto(proto_path: ProtoMethodStructure) -> str:
    return """
syntax = "proto3";
package library;


message Author {
  string last_name = 1;
  string first_name = 2;
  optional string second_name = 3;
}

message BookMetadata {
  message Publisher {
    string name = 1;
  }

  string name = 1;
  int32 year = 2;
  repeated Author authors = 3;
  optional Publisher publisher = 4;
}

message BookAddRequest {
  message User {
    enum Sex {
      MALE = 0;
      FEMALE = 1;
    }
    string last_name = 1;
    string first_name = 2;
    optional string second_name = 3;
    optional Sex sex = 4;
  }

  string book_uuid = 1;
  int64 user_id = 2;
  string timestamp = 3;
  optional BookMetadata metadata = 4;
  optional User user = 5;
}

message BookAddReply {
  string transaction_uuid = 1;
}

message BookRemoveRequest {
  string book_uuid = 1;
  int64 user_id = 2;
  string timestamp = 3;
}

message BookRemoveReply {
  string transaction_uuid = 1;
}

// The library service definition.
service Books {
  rpc BookAddEndpoint (BookAddRequest) returns (BookAddReply) {}
  rpc BookRemoveEndpoint (BookRemoveRequest) returns (BookRemoveReply) {}
}
"""



async def store_config(config_request_body: dict):
    """
    Parse mocks from a configuration request and save them to the storage.
    """
    package_structure = parse_proto_file(config_request_body["proto"])
    mock_mapping = {}
    for mock in config_request_body["mocks"]:
        method_mock_mapping = mock_mapping.get(mock["service"], {})
        method_mock_mapping.update({mock["method"]: mock["response"]})
        mock_mapping[mock["service"]] = method_mock_mapping
    async with DbConnection() as db:
        for service_name, service in package_structure.services.items():
            for method_name, method in service.methods.items():
                await _add_config_to_db(
                    db, config_uuid=config_request_body["config_id"],
                    package_name=package_structure.name, service_name=service_name,
                    method_name=method_name, method=method,
                    response_mock=mock_mapping[service_name][method_name],
                )


async def _add_config_to_db(
        db: DbConnection,
        config_uuid: str,
        package_name: str,
        service_name: str,
        method_name: str,
        method: ProtoMethod,
        response_mock: dict,
):
    previous = await db.select(
        "select * from mocks where package_name=:package_name "
        "and service_name=:service_name and method_name=:method_name and is_deleted is false",
        values={"package_name": package_name, "service_name": service_name, "method_name": method_name}
    )
    for item in previous:
        await db.execute(
            "update mocks set is_deleted=true, updated_at=:updated_at where id=:id",
            values={"updated_at": datetime.now(UTC), "id": item.id}
        )

    await db.execute(
        "insert into mocks (config_uuid, package_name, service_name, method_name, request_schema, response_schema, response_mock, is_deleted) "
        "values (:config_uuid, :package_name, :service_name, :method_name, :request_schema, :response_schema, :response_mock, :is_deleted)",
        values=dict(
            config_uuid=config_uuid, package_name=package_name, service_name=service_name, method_name=method_name,
            request_schema=json.dumps(method.request), response_schema=json.dumps(method.response),
            response_mock=json.dumps(response_mock, ensure_ascii=False), is_deleted=False,
        )
    )


async def get_route_log(query_params: dict) -> dict:
    return {"data": 1234}


async def store_request_to_log(
    data: dict, method_structure: ProtoMethodStructure
):
    pass
