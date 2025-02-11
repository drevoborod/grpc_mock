import re
from dataclasses import dataclass

from blackboxprotobuf.lib.protofile import import_proto
from blackboxprotobuf.lib.config import default as default_config
import h2.events
from proto_schema_parser import Parser
from proto_schema_parser.ast import Package, Message, Service, File, Method, Enum


class ProtoParserError(Exception): pass


@dataclass
class ProtoMethodStructure:
    host: str
    package: str
    service: str
    method: str


@dataclass
class ProtoMethod:
    request: dict
    response: dict

@dataclass
class ProtoService:
    methods: dict[str, ProtoMethod]

@dataclass
class ProtoPackage:
    name: str
    services: dict[str, ProtoService]


type ProtoElement = Message | Service | Package | File | Method | Enum


class ProtoFileParser:
    def __init__(self, proto: str) -> None:
        """
        Helps to prepare type definitions of all messages in provided proto file.
        Type definitions are intended to use with blackboxprotobuf.

        :param proto: .proto file contents.
        """
        self._raw_typedef = import_proto(default_config, input_string=proto)
        self._proto_elements: list[ProtoElement] = Parser().parse(proto).file_elements
        _packages: list[str] = []
        self._services: dict[str, Service] = {}
        for item in self._proto_elements:
            match item:
                case Package():
                    _packages.append(item.name)
                case Service():
                    self._services[item.name] = item
        if len(_packages) != 1:
            raise ProtoParserError("Provided file contains incorrect quantity of package definitions.")
        self.package_name = _packages[0]

    def to_typedef(self) -> ProtoPackage:
        return ProtoPackage(
            name=self.package_name,
            services=self._prepare_services()
        )

    def _prepare_services(self) -> dict[str, ProtoService]:
        return {key: self._prepare_methods_in_service(value) for key, value in self._services.items()}

    def _prepare_methods_in_service(self, service: Service) -> ProtoService:
        methods = {}
        for item in service.elements:
            if isinstance(item, Method):
                methods[item.name] = self._prepare_method(item)
        return ProtoService(methods=methods)

    def _prepare_method(self, method: Method) -> ProtoMethod:
        return ProtoMethod(
            request=self._prepare_typedef_message(self._raw_typedef[f"{self.package_name}.{method.input_type.type}"]),
            response=self._prepare_typedef_message(self._raw_typedef[f"{self.package_name}.{method.output_type.type}"]),
        )

    def _prepare_typedef_message(self, data: dict) -> dict:
        new = {}
        for key, value in data.items():
            new[key] = self._prepare_typedef_message_data(value)
        return new

    def _prepare_typedef_message_data(self, data: dict) -> dict:
        new = {}
        for key, value in data.items():
            if key == "message_type_name":
                new["message_typedef"] = self._prepare_typedef_message(self._raw_typedef[value])
            else:
                new[key] = value
        return new


def parse_proto_file(proto: str) -> ProtoPackage:
    parser = ProtoFileParser(proto)
    return parser.to_typedef()


def get_request_typedef_from_proto_package(package: ProtoPackage, proto_path: ProtoMethodStructure) -> dict:
    return package.services[proto_path.service].methods[proto_path.method].request


def get_proto_path_from_request(event: h2.events.RequestReceived) -> ProtoMethodStructure:
    host = ""
    path = ""
    for header in event.headers:
        if header[0] == b":path":
            path = header[1].decode()
        if header[0] == b":authority":
            host = header[1].decode().split(":")[0]
        if host and path:
            break
    package, service, method = re.match(r"^/(.+)\.(.+)/(.+)$", path).groups()
    return ProtoMethodStructure(host=host, package=package, service=service, method=method)
