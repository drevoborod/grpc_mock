from pydantic import BaseModel


class _BaseModel(BaseModel, extra="forbid"):
    pass


class DefaultResponse(_BaseModel):
    status: str
    message: str
    status_code: int


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
