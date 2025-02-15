import asyncio
from hypercorn.config import Config as HypercornConfig
from hypercorn.asyncio import serve

from grpc_mock.server import app
from grpc_mock.config import create_config



if __name__ == "__main__":
    config = create_config()
    hyper_config = HypercornConfig()
    hyper_config.bind = f"{config.api_host}:{config.api_port}"
    asyncio.run(serve(app, hyper_config))
