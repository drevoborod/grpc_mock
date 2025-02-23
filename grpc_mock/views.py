import re
from dataclasses import asdict

from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from grpc_mock.repo import LogRepo
from grpc_mock.response import GRPCResponse
from grpc_mock.schemas import (
    UploadRunsRequest,
    DownloadRunsRequest,
    DefaultResponse,
    ProtoMethodStructure,
    MockFromGetRequest,
)
from grpc_mock.services import GRPCService, MockService


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


async def process_grpc_request(request: Request) -> GRPCResponse:
    method_structure = get_proto_method_structure_from_request(request)
    payload = await request.body()
    grpc_service: GRPCService = request.scope["state"]["grpc_service"]
    result = await grpc_service.process_grpc(
        package=method_structure.package,
        service=method_structure.service,
        method=method_structure.method,
        payload=payload,
    )
    return GRPCResponse(
        result,
        media_type="application/grpc",
        headers={"grpc-status": "0"},
    )


async def process_add_mocks(request: Request) -> JSONResponse:
    body = await request.json()
    request_data = UploadRunsRequest(**body)
    mock_service: MockService = request.scope["state"]["mock_service"]
    await mock_service.store_mocks(
        protos=request_data.protos,
        config_uuid=request_data.config_uuid,
        mocks=request_data.mocks,
    )
    response_model = DefaultResponse(
        status="ok",
        message="Mock configuration added successfully",
    )

    return JSONResponse(
        response_model.model_dump(),
    )


async def process_get_log(request: Request) -> JSONResponse:
    params = DownloadRunsRequest(**request.query_params)
    log_repo: LogRepo = request.scope["state"]["log_repo"]
    response_data = await log_repo.get_route_log(
        package=params.package,
        service=params.service,
        method=params.method,
        config_uuid=params.config_uuid,
    )
    return JSONResponse([asdict(x) for x in response_data])


async def process_get_mocks(request: Request):
    params = MockFromGetRequest(**request.query_params)
    mock_service: MockService = request.scope["state"]["mock_service"]
    response_data = await mock_service.get_mocks(
        package=params.package, service=params.service, method=params.method
    )
    return JSONResponse([asdict(x) for x in response_data])


async def process_delete_mocks(request: Request):
    params = MockFromGetRequest(**request.query_params)
    mock_service: MockService = request.scope["state"]["mock_service"]
    await mock_service.delete_mocks(
        package=params.package, service=params.service, method=params.method
    )
    response_model = DefaultResponse(
        status="ok",
        message="Mock configuration deleted successfully",
    )
    return JSONResponse(
        response_model.model_dump(),
    )


def prepare_error_response(
    message: str, status_code: int = status.HTTP_400_BAD_REQUEST
) -> JSONResponse:
    model = DefaultResponse(status="error", message=message)
    return JSONResponse(model.model_dump(), status_code=status_code)
