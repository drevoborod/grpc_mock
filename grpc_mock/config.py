from enum import StrEnum
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


class DbType(StrEnum):
    POSTGRES = "postgres"
    SQLITE = "sqlite"


@dataclass
class Config:
    api_host: str
    api_port: str
    db_type: DbType
    db_url: str = field(default="")
    sqlite_db_file_name: str = field(default="")


def create_config():
    load_dotenv()
    return Config(
        api_host=os.environ["GRPC_MOCK_HOST"],
        api_port=os.environ["GRPC_MOCK_PORT"],
        db_type=DbType(os.environ["GRPC_MOCK_DB_TYPE"].lower()),
        db_url=os.environ.get("GRPC_MOCK_DATABASE_URL") or "",
        sqlite_db_file_name=os.environ.get("GRPC_MOCK_SQLITE_DB_FILE_NAME") or ":memory:",
    )
