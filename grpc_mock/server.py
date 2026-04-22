import asyncio
import logging
import signal
import traceback
from collections.abc import Coroutine

import aiosqlite
from databases import Database
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from grpc_mock.config import create_config, DbType
from grpc_mock.prepare_sqlite_db import create_tables_sqlite, shutdown_sqlite
from grpc_mock.repo_postgres import MockRepoPostgres, LogRepoPostgres
from grpc_mock.repo_sqlite import MockRepoSqlite, LogRepoSqlite
from grpc_mock.services import GrpcMockService, GRPCService, RestMockService, RestService
from grpc_mock.views import (
    process_grpc_request,
    process_get_grpc_logs,
    process_add_grpc_mocks,
    process_get_grpc_mocks,
    process_delete_grpc_mocks,
    prepare_error_response, process_undetermined_rest_request, process_add_rest_mocks, process_get_rest_mocks,
    process_delete_rest_mocks, process_get_rest_logs,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def process_rest_requests(scope, receive) -> JSONResponse:
    match scope:
        case {
            "path": "/grpc_mocks",
            "method": "POST",
        }:
            method = process_add_grpc_mocks
        case {
            "path": "/grpc_mocks",
            "method": "GET",
        }:
            method = process_get_grpc_mocks
        case {
            "path": "/grpc_mocks",
            "method": "DELETE",
        }:
            method = process_delete_grpc_mocks
        case {
            "path": "/grpc_logs",
            "method": "GET",
        }:
            method = process_get_grpc_logs

        case {
            "path": "/rest_mocks",
            "method": "POST",
        }:
            method = process_add_rest_mocks
        case {
            "path": "/rest_mocks",
            "method": "GET",
        }:
            method = process_get_rest_mocks
        case {
            "path": "/rest_mocks",
            "method": "DELETE",
        }:
            method = process_delete_rest_mocks
        case {
            "path": "/rest_logs",
            "method": "GET",
        }:
            method = process_get_rest_logs
        case _:
            method = process_undetermined_rest_request

    return await method(Request(scope, receive))


async def lifespan(scope, receive, send) -> None:
    message = await receive()
    if message["type"] == "lifespan.startup":
        config = create_config()
        if config.db_type == DbType.POSTGRES:
            db = Database(config.db_url)
            await db.connect()
            mock_repo = MockRepoPostgres(db)
            log_repo = LogRepoPostgres(db)
        elif config.db_type == DbType.SQLITE:
            db = await aiosqlite.connect(config.sqlite_db_file_name)
            loop = asyncio.get_event_loop()
            loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(shutdown_sqlite(db)))
            db.row_factory = aiosqlite.Row
            await create_tables_sqlite(db)
            mock_repo = MockRepoSqlite(db)
            log_repo = LogRepoSqlite(db)
        else:
            logger.critical(f"Unsupported database type: {config.db_type}")
            raise ValueError("Unknown database type")
        grpc_mock_service = GrpcMockService(mock_repo)
        http_mock_service = RestMockService(mock_repo)
        grpc_service = GRPCService(mock_repo=mock_repo, log_repo=log_repo)
        rest_service = RestService(mock_repo=mock_repo, log_repo=log_repo)
        scope["state"].update(
            dict(
                grpc_service=grpc_service,
                rest_service = rest_service,
                grpc_mock_service=grpc_mock_service,
                http_mock_service=http_mock_service,
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
        logger.error(traceback.format_exc())
        response = prepare_error_response(
            f"Something went wrong: {err}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    await response(scope, receive, send)
