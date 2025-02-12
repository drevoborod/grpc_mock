from deepdiff import DeepDiff

from grpc_mock.proto_utils import (
    ProtoMethodStructure,
    parse_proto_file,
    get_request_typedef_from_proto_package,
)
from tests.data.protofiles import LIBRARY_PROTO, MOCK_SERVICE_PROTO
from tests.data.typedefs import LIBRARY_REQUEST_TYPEDEF


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


def test__parse_proto_file__2_services__successfully():
    proto_package = parse_proto_file(MOCK_SERVICE_PROTO)
    assert len(proto_package.services) == 2
