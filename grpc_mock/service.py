import logging

from databases import Database
from starlette import status
from starlette.requests import Request
from grpc_mock.config import create_config
from grpc_mock.views import process_grpc_request, process_rest_request, prepare_error_response

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def app(scope, receive, send):
    logger.info(scope)
    config = create_config()
    db = Database(config.db_url)
    await db.connect()
    try:
        match scope:
            case {"type": "http", "http_version": "2"}:
                response = await process_grpc_request(Request(scope, receive), db)
            case {"type": "http", "http_version": "1.1"}:
                response = await process_rest_request(Request(scope, receive), db)
            case _:
                response = prepare_error_response(
                    "This server supports HTTP versions 2 and 1.1 only"
                )
    except Exception as err:
        logger.error(err)
        response = prepare_error_response(f"Something went wrong: {err}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    await response(scope, receive, send)
