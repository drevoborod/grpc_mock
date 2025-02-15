from pydantic import BaseModel


class _BaseModel(BaseModel, extra="forbid"):
    pass


class DefaultResponse(_BaseModel):
    status: str
    message: str


class RequestMock(_BaseModel):
    service: str
    method: str
    response: dict


class UploadRunsRequest(_BaseModel):
    mocks: list[RequestMock]
    proto: str
    config_uuid: str


class DownloadRunsRequest(_BaseModel):
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
