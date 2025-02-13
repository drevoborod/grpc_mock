import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve

from grpc_mock.service import app


if __name__ == "__main__":
    config = Config()
    config.bind = "0.0.0.0:3333"
    asyncio.run(serve(app, config))
