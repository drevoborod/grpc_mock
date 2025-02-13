import logging
import re

import blackboxprotobuf
from starlette import status
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from grpc_mock.proto_utils import (
    ProtoMethodStructure,
)
from grpc_mock.repository import (
    get_mock_from_storage,
    store_config,
    get_route_log,
    store_to_log,
    StorageError,
)


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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


async def process_grpc_request(request: Request) -> Response:
    method_structure = get_proto_method_structure_from_request(request)
    storage_mock = await get_mock_from_storage(method_structure)
    payload = await request.body()
    request_data = parse_grpc_data(payload, storage_mock.request_schema)
    logger.info(request_data)
    response_data = blackboxprotobuf.encode_message(storage_mock.response_mock, storage_mock.response_schema)
    await store_to_log(storage_mock.id, request_data, storage_mock.response_mock)
    return Response((0).to_bytes() + len(response_data).to_bytes(4, "big", signed=False) + response_data, media_type="application/grpc")


async def process_rest_request(request: Request) -> Response:
    match request.scope:
        case {"path": "/runs", "method": "POST"}:
            body = await request.json()
            try:
                await store_config(body)
            except StorageError as err:
                response = prepare_error_response(f"unable to store configuration: {err}")
            else:
                response = JSONResponse(
                    {"status": "ok", "message": "configuration stored"}
                )
        case {"path": "/runs", "method": "GET"}:
            response_data = await get_route_log(dict(request.query_params))
            response = JSONResponse(response_data)
        case _:
            response = prepare_error_response("unknown endpoint or unsupported method")
    return response


def prepare_error_response(message: str, status_code: status = status.HTTP_400_BAD_REQUEST) -> JSONResponse:
    return JSONResponse(
        {"status": "error", "message": message},
        status_code=status_code,
    )


async def app(scope, receive, send):
    logger.info(scope)
    match scope:
        case {"type": "http", "http_version": "2"}:
            response = await process_grpc_request(Request(scope, receive))
        case {"type": "http", "http_version": "1.1"}:
            response = await process_rest_request(Request(scope, receive))
        case _:
            response = prepare_error_response("This server supports only HTTP of versions 2 and 1.1")
    await response(scope, receive, send)


if __name__ == "__main__":
    import asyncio
    from hypercorn.config import Config
    from hypercorn.asyncio import serve

    config = Config()
    config.bind = "0.0.0.0:3333"
    asyncio.run(serve(app, config))
