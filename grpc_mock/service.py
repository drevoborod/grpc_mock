import logging
import re

import blackboxprotobuf
from starlette import status
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from grpc_mock.proto_utils import (
    parse_proto_file,
    ProtoMethodStructure,
    get_request_typedef_from_proto_package,
)
from grpc_mock.repository import (
    get_proto,
    set_route_config,
    get_route_log,
    store_request_to_log,
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
        host=request.headers["host"].split(":")[0],
        package=package,
        service=service,
        method=method,
    )


async def prepare_typedef(method_structure: ProtoMethodStructure) -> dict:
    proto_file = await get_proto(method_structure)
    proto_package = parse_proto_file(proto_file)
    return get_request_typedef_from_proto_package(
        proto_package, method_structure
    )


async def parse_grpc_data(data: bytes, typedef: dict) -> dict:
    message, _ = blackboxprotobuf.decode_message(data[5:], typedef)
    logger.info(message)
    return message


def http_params_to_grpc_method_structure(
    request: Request,
) -> ProtoMethodStructure:
    pass


async def process_grpc_request(request: Request) -> Response:
    method_structure = get_proto_method_structure_from_request(request)
    typedef = await prepare_typedef(method_structure)
    payload = await request.body()
    request_data = await parse_grpc_data(payload, typedef)
    await store_request_to_log(request_data, method_structure)
    content = "%s %s" % (request.method, request.url.path)
    return Response(content, media_type="application/grpc")


async def process_rest_request(request: Request) -> Response:
    match request.scope["path"]:
        case "/config":
            body = await request.json()
            await set_route_config(body)
            response = JSONResponse(
                {"status": "ok", "message": "configuration stored"}
            )
        case "/log":
            method_structure = http_params_to_grpc_method_structure(request)
            response_data = await get_route_log(method_structure)
            response = JSONResponse(response_data)
        case _:
            response = JSONResponse(
                {"status": "error", "message": "unknown endpoint"},
                status_code=status.HTTP_404_NOT_FOUND,
            )
    return response


async def app(scope, receive, send):
    logger.info(scope)
    if scope["type"] != "http":
        response = JSONResponse(
            {"status": "error", "message": "this server supports HTTP only"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    else:
        request = Request(scope, receive)
        if scope["http_version"] == "2":
            # log and response to GRPC request
            response = await process_grpc_request(request)
        elif scope["http_version"] == "1.1":
            # log and response to REST request
            response = await process_rest_request(request)
        else:
            response = JSONResponse(
                {"status": "error", "message": "Unknown HTTP version"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
    await response(scope, receive, send)


if __name__ == "__main__":
    import asyncio
    from hypercorn.config import Config
    from hypercorn.asyncio import serve

    config = Config()
    config.bind = "0.0.0.0:3333"
    asyncio.run(serve(app, config))
