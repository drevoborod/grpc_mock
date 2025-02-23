import logging

from databases import Database
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from grpc_mock.config import create_config
from grpc_mock.repo import MockRepo, LogRepo
from grpc_mock.services import MockService, GRPCService
from grpc_mock.views import (
    process_grpc_request,
    process_get_log,
    process_add_mocks,
    process_get_mocks,
    process_delete_mocks,
    prepare_error_response,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def process_rest_requests(scope, receive) -> JSONResponse:
    match scope:
        case {
            "path": "/mocks",
            "method": "POST",
        }:
            return await process_add_mocks(Request(scope, receive))
        case {
            "path": "/logs",
            "method": "GET",
        }:
            return await process_get_log(Request(scope, receive))
        case {
            "path": "/mocks",
            "method": "GET",
        }:
            return await process_get_mocks(Request(scope, receive))
        case {
            "path": "/mocks",
            "method": "DELETE",
        }:
            return await process_delete_mocks(Request(scope, receive))
        case _:
            return prepare_error_response(
                "Unknown endpoint",
                status_code=status.HTTP_404_NOT_FOUND,
            )


async def lifespan(scope, receive, send) -> None:
    message = await receive()
    if message["type"] == "lifespan.startup":
        config = create_config()
        db = Database(config.db_url)
        await db.connect()
        mock_repo = MockRepo(db)
        log_repo = LogRepo(db)
        mock_service = MockService(mock_repo)
        grpc_service = GRPCService(mock_repo=mock_repo, log_repo=log_repo)
        scope["state"].update(
            dict(
                grpc_service=grpc_service,
                mock_service=mock_service,
                db=db,
                log_repo=log_repo,
            )
        )
        await send({"type": "lifespan.startup.complete"})
    elif message["type"] == "lifespan.shutdown":
        await send({"type": "lifespan.shutdown.complete"})


async def app(scope, receive, send):
    logger.info(scope)
    try:
        match scope:
            case {"type": "lifespan"}:
                await lifespan(scope, receive, send)
                return
            case {"type": "http", "http_version": "2"}:
                response = await process_grpc_request(Request(scope, receive))
            case {"type": "http", "http_version": "1.1"}:
                response = await process_rest_requests(scope, receive)
            case _:
                response = prepare_error_response("Unsupported protocol")

    except Exception as err:
        logger.error(err)
        response = prepare_error_response(
            f"Something went wrong: {err}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    await response(scope, receive, send)
