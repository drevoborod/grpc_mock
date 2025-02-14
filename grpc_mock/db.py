from databases import Database

from grpc_mock.config import Config


class DbConnection:
    def __init__(self, config: Config):
        self.db = Database(config.db_url)

    async def __aenter__(self):
        await self.db.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.disconnect()

    async def execute(self, query: str, values: dict):
        result = await self.db.execute(query=query, values=values)
        return result

    async def select_one(self, query: str, values: dict = None):
        result = await self.db.fetch_one(query=query, values=values)
        return result

    async def select_all(self, query: str, values: dict = None):
        result = await self.db.fetch_all(query=query, values=values)
        return result
