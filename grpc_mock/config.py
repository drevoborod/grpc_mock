import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    db_url: str
    db_password: str
    api_host: str
    api_port: str

    def __post_init__(self):
        self.db_url = self.db_url.format(password=self.db_password)

def create_config():
    load_dotenv()
    return Config(
        db_url=os.environ["GRPC_MOCK_DATABASE_URL"],
        db_password=os.environ["GRPC_MOCK_DATABASE_PASSWORD"],
        api_host=os.environ["GRPC_MOCK_HOST"],
        api_port=os.environ["GRPC_MOCK_PORT"],
    )