import asyncio

from aiosqlite import Connection

MOCKS_TABLE = \
"""
CREATE TABLE IF NOT EXISTS mocks (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    config_uuid TEXT NOT NULL,
    package_name TEXT NOT NULL,
    service_name TEXT NOT NULL,
    method_name TEXT NOT NULL,
    request_schema JSONB NOT NULL,
    response_schema JSONB NOT NULL,
    response_mock JSONB NOT NULL,
    response_status INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN
);
"""

LOGS_TABLE = \
"""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    mock_id INTEGER NOT NULL,
    request JSONB NOT NULL,
    response JSONB NOT NULL,
    response_status INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(mock_id) REFERENCES mocks (id)
);
"""


async def create_tables_sqlite(db: Connection):
    cursor = await db.execute(MOCKS_TABLE)
    await cursor.close()
    cursor = await db.execute(LOGS_TABLE)
    await cursor.close()
