import re
from dataclasses import asdict

import blackboxprotobuf
from databases import Database
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from grpc_mock.proto_parser import ProtoMethodStructure
from grpc_mock.repo import (
    MockRepo,
    LogRepo,
    StorageError,
)
from grpc_mock.schemas import UploadRunsRequest, DownloadRunsRequest
from grpc_mock.services import prepare_error_response, prepare_default_response, MockService


def get_proto_method_structure_from_request(
    request: Request,
) -> ProtoMethodStructure:
    """
    Parses GRPC request object and returns a model representing protobuf method structure:
    host, package, service and method names.

    """
    package, service, method = re.match(
        r"^/(.+)\.(.+)/(.+)$", request.url.path
    ).groups()
    return ProtoMethodStructure(
        package=package,
        service=service,
        method=method,
    )


def parse_grpc_data(data: bytes, typedef: dict) -> dict:
    message, _ = blackboxprotobuf.decode_message(data[5:], typedef)
    return message


async def process_grpc_request(request: Request, db: Database) -> Response:
    method_structure = get_proto_method_structure_from_request(request)
    mock_repo = MockRepo(db)
    storage_mock = await mock_repo.get_mock_from_storage(
        package=method_structure.package,
        service=method_structure.service,
        method=method_structure.method,
    )
    payload = await request.body()
    request_data = parse_grpc_data(payload, storage_mock.request_schema)
    response_data = blackboxprotobuf.encode_message(
        storage_mock.response_mock, storage_mock.response_schema
    )
    log_repo = LogRepo(db)
    await log_repo.store_log(
        storage_mock.id, request_data, storage_mock.response_mock
    )
    return Response(
        (0).to_bytes()
        + len(response_data).to_bytes(4, "big", signed=False)
        + response_data,
        media_type="application/grpc",
        headers={"grpc-status": "0"},
    )


async def process_rest_request(request: Request, mock_service: MockService, log_repo: LogRepo) -> Response:
    match request.scope:
        case {"path": "/runs", "method": "POST"}:
            body = await request.json()
            request_data = UploadRunsRequest(**body)
            await mock_service.store_mock(
                proto=request_data.proto, config_uuid=request_data.config_uuid, mocks=request_data.mocks,
            )
            response_model = prepare_default_response("configuration stored")
            return JSONResponse(
                response_model.model_dump(),
                status_code=response_model.status_code,
            )
        case {"path": "/runs", "method": "GET"}:
            params = DownloadRunsRequest(**request.query_params)
            response_data = await log_repo.get_route_log(
                package=params.package, service=params.service, method=params.method, config_uuid=params.config_uuid,
            )
            response = JSONResponse([asdict(x) for x in response_data])
        case _:
            response_model = prepare_error_response("unknown endpoint or unsupported method")
            response = JSONResponse(
                response_model.model_dump(),
                status_code=response_model.status_code,
            )
    return response
