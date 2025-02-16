from dataclasses import dataclass

from blackboxprotobuf.lib.protofile import import_proto
from blackboxprotobuf.lib.config import default as default_config
from proto_schema_parser import Parser
from proto_schema_parser.ast import (
    Package,
    Message,
    Service,
    File,
    Method,
    Enum,
)


class ProtoParserError(Exception):
    pass


@dataclass
class ProtoMethod:
    name: str
    request: dict
    response: dict


@dataclass
class ProtoService:
    name: str
    methods: dict[str, ProtoMethod]


@dataclass
class ProtoPackage:
    name: str
    services: dict[str, ProtoService]


@dataclass
class ProtoRootStructure:
    packages: dict[str, ProtoPackage]


type ProtoElement = Message | Service | Package | File | Method | Enum


class ProtoFileParser:
    def __init__(self, protos: list[str]) -> None:
        """
        Helps to prepare type definitions of all messages in provided proto files.
        Type definitions are intended to use with blackboxprotobuf.

        :param protos: list of .proto files contents.
        """
        raw_typedefs = [
            import_proto(default_config, input_string=proto) for proto in protos
        ]
        self._raw_typedef = {}
        for typedef in raw_typedefs:
            self._raw_typedef.update(typedef)
        proto_element_lists = [
            Parser().parse(proto).file_elements for proto in protos
        ]
        self._packages_dict: dict[str, dict[str, Service]] = {}
        for elem_list in proto_element_lists:
            self._add_package_to_packages_dict(elem_list)

    def _add_package_to_packages_dict(
        self, proto_element_list: list[ProtoElement]
    ) -> None:
        package_name = next(
            (
                item.name
                for item in proto_element_list
                if isinstance(item, Package)
            ),
            "",
        )
        if not package_name:
            raise ProtoParserError("There is no package in provided proto file")
        self._packages_dict[package_name] = {}
        for item in proto_element_list:
            if isinstance(item, Service):
                self._packages_dict[package_name][item.name] = item

    def parse_protos(self) -> ProtoRootStructure:
        return ProtoRootStructure(packages=self._prepare_packages())

    def _prepare_packages(self) -> dict[str, ProtoPackage]:
        result = {}
        for package_name, services_dict in self._packages_dict.items():
            result[package_name] = ProtoPackage(
                name=package_name,
                services=self._prepare_services(package_name, services_dict),
            )
        return result

    def _prepare_services(
        self, package_name: str, services_dict: dict[str, Service]
    ) -> dict[str, ProtoService]:
        return {
            key: self._prepare_methods_in_service(value, package_name)
            for key, value in services_dict.items()
        }

    def _prepare_methods_in_service(
        self, service: Service, package_name: str
    ) -> ProtoService:
        methods = {}
        for item in service.elements:
            if isinstance(item, Method):
                methods[item.name] = self._prepare_method(item, package_name)
        return ProtoService(name=service.name, methods=methods)

    def _prepare_method(self, method: Method, package_name: str) -> ProtoMethod:
        return ProtoMethod(
            name=method.name,
            request=self._prepare_typedef_message(
                self._raw_typedef[f"{package_name}.{method.input_type.type}"]
            ),
            response=self._prepare_typedef_message(
                self._raw_typedef[f"{package_name}.{method.output_type.type}"]
            ),
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
                new["message_typedef"] = self._prepare_typedef_message(
                    self._raw_typedef[value]
                )
            else:
                new[key] = value
        return new


def parse_proto_file(protos: list[str]) -> ProtoRootStructure:
    parser = ProtoFileParser(protos)
    return parser.parse_protos()
