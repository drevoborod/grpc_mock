from grpc_mock.proto_utils import ProtoMethodStructure
from grpc_mock.service import get_proto_method_structure_from_request


class MockRequestUrl:
    path = "/library.Books/BookAddEndpoint"


class MockH2EventsRequestReceived:
    headers = {
        "host": "server.example.com:3333",
        "user-agent": "grpc-python-grpclib/0.4.7 (linux; cpython/3.12.7)",
    }
    url = MockRequestUrl


def test__get_proto_method_info_from_request__data_found():
    result = get_proto_method_structure_from_request(
        MockH2EventsRequestReceived
    )
    assert result == ProtoMethodStructure(
        host="server.example.com",
        package="library",
        service="Books",
        method="BookAddEndpoint",
    )
