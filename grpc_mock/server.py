import logging

from databases import Database
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from grpc_mock.config import create_config
from grpc_mock.repo import MockRepo, LogRepo
from grpc_mock.services import MockService
from grpc_mock.views import process_grpc_request, process_rest_request, prepare_error_response

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def lifespan(scope, receive, send) -> None:
    message = await receive()
    if message["type"] == 'lifespan.startup':
        config = create_config()
        db = Database(config.db_url)
        await db.connect()
        mock_repo = MockRepo(db)
        log_repo = LogRepo(db)
        mock_service = MockService(mock_repo)
        scope["state"].update(dict(mock_service=mock_service, db=db, log_repo=log_repo))
        await send({"type": "lifespan.startup.complete"})
    elif message["type"] == 'lifespan.shutdown':
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
                response = await process_rest_request(Request(scope, receive))
            case _:
                response_model = prepare_error_response(
                    "This server supports HTTP versions 2 and 1.1 only"
                )
                response = JSONResponse(response_model.model_dump(), status_code=response_model.status_code)

    except Exception as err:
        logger.error(err)
        response_model = prepare_error_response(f"Something went wrong: {err}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        response = JSONResponse(response_model.model_dump(), status_code=response_model.status_code)
    await response(scope, receive, send)
