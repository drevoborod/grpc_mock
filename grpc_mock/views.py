import re
from dataclasses import asdict

from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from grpc_mock.repo import LogRepo
from grpc_mock.response import GRPCResponse
from grpc_mock.schemas import (
    GrpcUploadMocksRequestBody,
    GrpcDownloadLogsRequest,
    DefaultResponse,
    ProtoMethodStructure,
    GrpcMockFromGetRequest, RestUploadMocksRequestBody, RestMockFromGetRequest, RestDownloadLogsRequest,
)
from grpc_mock.services import GRPCService, GrpcMockService, RestMockService, RestService, MockResponsePreparationError


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
    response_body, response_status = await grpc_service.process_grpc(
        package=method_structure.package,
        service=method_structure.service,
        method=method_structure.method,
        payload=payload,
    )
    return GRPCResponse(
        response_body,
        media_type="application/grpc",
        headers={"grpc-status": str(response_status)},
    )


async def process_add_grpc_mocks(request: Request) -> JSONResponse:
    body = await request.json()
    request_data = GrpcUploadMocksRequestBody(**body)
    mock_service: GrpcMockService = request.scope["state"]["grpc_mock_service"]
    await mock_service.store_grpc_mocks(
        protos=request_data.protos,
        config_uuid=request_data.config_uuid,
        mocks=request_data.mocks,
    )
    response_model = DefaultResponse(
        status="ok",
        message="GRPC mock configuration added successfully",
    )

    return JSONResponse(
        response_model.model_dump(),
    )


async def process_get_grpc_mocks(request: Request) -> JSONResponse:
    params = GrpcMockFromGetRequest(**request.query_params)
    mock_service: GrpcMockService = request.scope["state"]["grpc_mock_service"]
    response_data = await mock_service.get_grpc_mocks(
        package=params.package, service=params.service, method=params.method
    )
    return JSONResponse([asdict(x) for x in response_data])


async def process_delete_grpc_mocks(request: Request) -> JSONResponse:
    params = GrpcMockFromGetRequest(**request.query_params)
    mock_service: GrpcMockService = request.scope["state"]["grpc_mock_service"]
    await mock_service.delete_grpc_mocks(
        package=params.package, service=params.service, method=params.method
    )
    response_model = DefaultResponse(
        status="ok",
        message="GRPC mock configuration deleted successfully",
    )
    return JSONResponse(
        response_model.model_dump(),
    )


async def process_get_grpc_logs(request: Request) -> JSONResponse:
    params = GrpcDownloadLogsRequest(**request.query_params)
    log_repo: LogRepo = request.scope["state"]["log_repo"]
    response_data = await log_repo.get_grpc_log(
        package=params.package,
        service=params.service,
        method=params.method,
        config_uuid=params.config_uuid,
    )
    return JSONResponse([asdict(x) for x in response_data])


async def process_add_rest_mocks(request: Request) -> JSONResponse:
    body = await request.json()
    request_data = RestUploadMocksRequestBody(**body)
    mock_service: RestMockService = request.scope["state"]["http_mock_service"]
    await mock_service.store_rest_mocks(
        config_uuid=request_data.config_uuid,
        mocks=request_data.mocks,
    )
    response_model = DefaultResponse(
        status="ok",
        message="REST mock configuration added successfully",
    )
    return JSONResponse(
        response_model.model_dump(),
    )


async def process_get_rest_mocks(request: Request) -> JSONResponse:
    params = RestMockFromGetRequest(**request.query_params)
    mock_service: RestMockService = request.scope["state"]["http_mock_service"]
    response_data = await mock_service.get_rest_mocks(
        endpoint=params.endpoint, method=params.method
    )
    return JSONResponse([asdict(x) for x in response_data])


async def process_delete_rest_mocks(request: Request) -> JSONResponse:
    params = RestMockFromGetRequest(**request.query_params)
    mock_service: RestMockService = request.scope["state"]["rest_mock_service"]
    await mock_service.delete_rest_mocks(
        endpoint=params.endpoint, method=params.method
    )
    response_model = DefaultResponse(
        status="ok",
        message="REST mock configuration deleted successfully",
    )
    return JSONResponse(
        response_model.model_dump(),
    )


async def process_get_rest_logs(request: Request) -> JSONResponse:
    params = RestDownloadLogsRequest(**request.query_params)
    log_repo: LogRepo = request.scope["state"]["log_repo"]
    response_data = await log_repo.get_rest_log(
        endpoint=params.endpoint,
        method=params.method,
        config_uuid=params.config_uuid,
    )
    return JSONResponse([asdict(x) for x in response_data])


async def process_undetermined_rest_request(request: Request):
    service: RestService = request.scope["state"]["rest_service"]
    body = await request.body()
    try:
        result = await service.process_rest_request(
            endpoint=request.url.path,
            method=request.method,
            headers=dict(request.headers),
            body=body,
            query_params=dict(request.query_params)
        )
    except MockResponsePreparationError:
        return prepare_error_response(
            f"Unknown endpoint: {request.url.path}", status_code=status.HTTP_404_NOT_FOUND)
    return JSONResponse(result.body, headers=result.headers)


def prepare_error_response(
    message: str, status_code: int = status.HTTP_400_BAD_REQUEST
) -> JSONResponse:
    model = DefaultResponse(status="error", message=message)
    return JSONResponse(model.model_dump(), status_code=status_code)
