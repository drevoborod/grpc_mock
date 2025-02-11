
import logging
import re

import blackboxprotobuf
from starlette.requests import Request
from starlette.responses import Response

from grpc_mock.proto_utils import parse_proto_file, ProtoMethodStructure, get_request_typedef_from_proto_package
from grpc_mock.repository import get_proto

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


def get_proto_method_info_from_request(request: Request) -> ProtoMethodStructure:
    """
    Parses GRPC request object and returns a model representing protobuf method structure:
    host, package, service and method names.

    """
    package, service, method = re.match(r"^/(.+)\.(.+)/(.+)$", request.url.path).groups()
    return ProtoMethodStructure(
        host=request.headers["host"].split(":")[0], package=package, service=service, method=method
    )


async def prepare_typedef(request: Request) -> dict:
    proto_metadata = get_proto_method_info_from_request(request)
    proto_file = await get_proto(proto_metadata)
    proto_package = parse_proto_file(proto_file)
    return get_request_typedef_from_proto_package(proto_package, proto_metadata)


async def parse_grpc_data(data: bytes, typedef: dict) -> dict:
    message, _ = blackboxprotobuf.decode_message(data[5:], typedef)
    logger.info(message)
    return message


async def app(scope, receive, send):
    assert scope['type'] == 'http'
    request = Request(scope, receive)
    content = '%s %s' % (request.method, request.url.path)
    payload = await request.body()

    typedef = await prepare_typedef(request)
    request_message = await parse_grpc_data(payload, typedef)

    # grpc response
    response = Response(content, media_type='application/grpc')
    await response(scope, receive, send)


if __name__ == "__main__":
    import asyncio
    from hypercorn.config import Config
    from hypercorn.asyncio import serve

    config = Config()
    config.bind = "0.0.0.0:3333"
    asyncio.run(serve(app, config))
