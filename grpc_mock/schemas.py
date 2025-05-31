from pydantic import BaseModel


class _BaseModel(BaseModel, extra="forbid"):
    pass


class DefaultResponse(_BaseModel):
    status: str
    message: str


class MockFromSetRequest(_BaseModel):
    package: str
    service: str
    method: str
    response: dict
    filter: dict[str, str] | None = None
    response_status: int | None = 0


class MockFromGetRequest(_BaseModel):
    package: str
    service: str
    method: str
    filter: dict[str, str] | None = None


class UploadMocksRequest(_BaseModel):
    mocks: list[MockFromSetRequest]
    protos: list[str]
    config_uuid: str


class DownloadMocksRequest(_BaseModel):
    package: str | None = None
    service: str | None = None
    method: str | None = None
    config_uuid: str | None = None


class ProtoMethodStructure(_BaseModel):
    """
    Represents GRPC method parts which allow to identify the method inside a protobuf definition file.
    """

    package: str
    service: str
    method: str
