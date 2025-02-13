import asyncio
import os
from datetime import datetime, UTC

from grpc_mock.db import DbConnection


os.environ["GRPC_MOCK_DB_URL"] = "postgresql://grpc_mock:8_djss6hdsSYbdt_63_sdasKR@localhost:14432/grpc_mock"

async def main():
    async with DbConnection() as db:
        # await db.insert(
        #     "insert into mocks (package_name, service_name, method_name, is_deleted, updated_at) "
        #     "values (:package_name, :service_name, :method_name, :is_deleted, :updated_at)",
        #     values={
        #         "package_name": "lib", "service_name": "AssHole",
        #         "method_name": "AddBook", "is_deleted": True, "updated_at": datetime.now(UTC),
        #     }
        # )
        result = await db.select_all(
            "select * from mocks",
            values={}
        )
        print([x.id for x in result])
        print(len(result))

asyncio.run(main())