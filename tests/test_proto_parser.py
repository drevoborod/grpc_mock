from deepdiff import DeepDiff

from grpc_mock.proto_parser import (
    parse_proto_file,
)
from tests.data.protofiles import (
    LIBRARY_PROTO,
    LIBRARY_PROTO_PACKAGE_NAME_WITH_DOTS,
    MOCK_SERVICE_PROTO_2_SERVICES,
    PROTO_TO_BE_IMPORTED,
    PROTO_WITH_IMPORT,
)
from tests.data.typedefs import LIBRARY_REQUEST_TYPEDEF


def test__parse_proto_file__1_service__successfully():
    proto_root = parse_proto_file([LIBRARY_PROTO])
    typedef = (
        proto_root.packages["library"]
        .services["Books"]
        .methods["BookAddEndpoint"]
        .request
    )
    assert not DeepDiff(typedef, LIBRARY_REQUEST_TYPEDEF)


def test__parse_proto_file__2_services__1_package__successfully():
    proto_root = parse_proto_file([MOCK_SERVICE_PROTO_2_SERVICES])
    assert len(proto_root.packages["grpc_mock"].services) == 2


def test__parse_proto_file__package_name_with_dots__successfully():
    proto_root = parse_proto_file([LIBRARY_PROTO_PACKAGE_NAME_WITH_DOTS])
    typedef = (
        proto_root.packages["big.home.library"]
        .services["Books"]
        .methods["BookAddEndpoint"]
        .request
    )
    assert not DeepDiff(typedef, LIBRARY_REQUEST_TYPEDEF)


def test__parse_2_proto_files__same_package__successfully():
    proto_root = parse_proto_file([PROTO_TO_BE_IMPORTED, PROTO_WITH_IMPORT])
    assert len(proto_root.packages) == 1
    # ToDo: add verifying of the typedef structure


def test__parse_2_proto_files__different_packages__successfully():
    proto_root = parse_proto_file(
        [LIBRARY_PROTO, LIBRARY_PROTO_PACKAGE_NAME_WITH_DOTS]
    )
    typedef1 = (
        proto_root.packages["library"]
        .services["Books"]
        .methods["BookAddEndpoint"]
        .request
    )
    assert not DeepDiff(typedef1, LIBRARY_REQUEST_TYPEDEF)
    typedef2 = (
        proto_root.packages["big.home.library"]
        .services["Books"]
        .methods["BookAddEndpoint"]
        .request
    )
    assert not DeepDiff(typedef2, LIBRARY_REQUEST_TYPEDEF)
