from aiosqlite import Connection

from grpc_mock.db_structure import TableNames

GRPC_MOCKS_TABLE = \
f"""
CREATE TABLE IF NOT EXISTS {TableNames.GRPC_MOCKS} (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    config_uuid TEXT NOT NULL,
    package_name TEXT NOT NULL,
    service_name TEXT NOT NULL,
    method_name TEXT NOT NULL,
    filter JSONB,
    request_schema JSONB NOT NULL,
    response_schema JSONB NOT NULL,
    response_mock JSONB NOT NULL,
    response_status INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT false
);
"""

GRPC_LOGS_TABLE = \
f"""
CREATE TABLE IF NOT EXISTS {TableNames.GRPC_LOGS} (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    mock_id INTEGER NOT NULL,
    request JSONB NOT NULL,
    response JSONB NOT NULL,
    response_status INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(mock_id) REFERENCES {TableNames.GRPC_MOCKS} (id)
);
"""

REST_MOCKS_TABLE = \
f"""
CREATE TABLE IF NOT EXISTS {TableNames.REST_MOCKS} (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    config_uuid TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    query_params_filter JSONB,
    body_filter JSONB,
    headers_filter JSONB,
    response_body TEXT,
    response_headers JSONB,
    response_status INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT false
);
"""

REST_LOGS_TABLE = \
f"""
CREATE TABLE IF NOT EXISTS {TableNames.REST_LOGS} (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    mock_id INTEGER NOT NULL,
    request JSONB NOT NULL,
    response JSONB NOT NULL,
    response_status INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(mock_id) REFERENCES {TableNames.REST_MOCKS} (id)
);
"""

async def create_tables_sqlite(db: Connection):
    for table in (GRPC_MOCKS_TABLE, GRPC_LOGS_TABLE, REST_MOCKS_TABLE, REST_LOGS_TABLE):
        cursor = await db.execute(table)
        await cursor.close()


async def shutdown_sqlite(db: Connection):
    await db.close()
