import os

from databases import Database


class DbConnection:
    def __init__(self):
        self.db = Database(os.environ["GRPC_MOCK_DB_URL"])

    async def __aenter__(self):
        await self.db.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.disconnect()

    async def execute(self, query: str, values: dict):
        result = await self.db.execute(query=query, values=values)
        return result

    async def select(self, query: str, values: dict = None):
        result = await self.db.fetch_all(query=query, values=values)
        return result
