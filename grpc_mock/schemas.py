from typing import Any

from pydantic import BaseModel


class _BaseModel(BaseModel, extra="forbid"):
    pass


class DefaultResponse(_BaseModel):
    status: str
    message: str


class GrpcMockFromSetRequest(_BaseModel):
    package: str
    service: str
    method: str
    response: dict
    filter: dict[str, str] | None = None
    response_status: int | None = 0


class GrpcUploadMocksRequestBody(_BaseModel):
    mocks: list[GrpcMockFromSetRequest]
    protos: list[str]
    config_uuid: str


class GrpcMockFromGetRequest(_BaseModel):
    package: str
    service: str
    method: str


class GrpcDownloadLogsRequest(_BaseModel):
    package: str | None = None
    service: str | None = None
    method: str | None = None
    config_uuid: str | None = None


class RestMockFromSetRequest(_BaseModel):
    endpoint: str
    method: str
    query_params_filter: dict[str, str] | None = None
    body_filter: dict[str, str] | None = None
    headers_filter: dict[str, str] | None = None
    response_body: str | dict | None = None
    response_headers: dict | None = None
    response_status: int = 200
    is_binary: bool = False

    def model_post_init(self, context: Any, /) -> None:
        # Because headers are case-insensitive, it's possible that someone will try to locate them using another case,
        # so let's prevent such situation by making both headers and the headers filter lowercase:
        if self.response_headers:
            self.response_headers = {k.lower(): v for k, v in self.response_headers.items()}
        if self.headers_filter:
            self.headers_filter = {k.lower(): v for k, v in self.headers_filter.items()}


class RestUploadMocksRequestBody(_BaseModel):
    mocks: list[RestMockFromSetRequest]
    config_uuid: str


class RestMockFromGetRequest(_BaseModel):
    endpoint: str
    method: str


class RestDownloadLogsRequest(_BaseModel):
    endpoint: str | None = None
    method: str | None = None
    config_uuid: str | None = None


class RestMockedResponse(_BaseModel):
    headers: dict | None
    body: dict | str | bytes | None
    is_binary: bool = False


class ProtoMethodStructure(_BaseModel):
    """
    Represents GRPC method parts which allow to identify the method inside a protobuf definition file.
    """

    package: str
    service: str
    method: str
