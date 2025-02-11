from deepdiff import DeepDiff

from grpc_mock.proto_utils import (
    get_proto_metadata_from_request,
    ProtoMethodStructure,
    parse_proto_file,
    get_request_typedef_from_proto_package,
)
from tests.data.protofiles import LIBRARY_PROTO
from tests.data.typedefs import LIBRARY_REQUEST_TYPEDEF


class MockH2EventsRequestReceived:
    headers = [
        (b":method", b"POST"),
        (b":scheme", b"http"),
        (b":path", b"/library.Books/BookAddEndpoint"),
        (b":authority", b"server.example.com:3333"),
        (b"user-agent", b"grpc-python-grpclib/0.4.7 (linux; cpython/3.12.7)"),
    ]


def test__get_proto_metadata_from_request__data_found():
    result = get_proto_metadata_from_request(MockH2EventsRequestReceived)
    assert result == ProtoMethodStructure(
        host="server.example.com",
        package="library",
        service="Books",
        method="BookAddEndpoint",
    )


def test__parse_proto_file__check_typedef__successfully():
    proto_package = parse_proto_file(LIBRARY_PROTO)
    typedef = get_request_typedef_from_proto_package(
        proto_package,
        ProtoMethodStructure(
            host="server.example.com",
            package="library",
            service="Books",
            method="BookAddEndpoint",
        ),
    )
    assert not DeepDiff(typedef, LIBRARY_REQUEST_TYPEDEF)
