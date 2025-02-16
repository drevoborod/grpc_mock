import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    db_url: str
    api_host: str
    api_port: str


def create_config():
    load_dotenv()
    return Config(
        db_url=os.environ["GRPC_MOCK_DATABASE_URL"],
        api_host=os.environ["GRPC_MOCK_HOST"],
        api_port=os.environ["GRPC_MOCK_PORT"],
    )
