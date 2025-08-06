from dataclasses import dataclass


from blackboxprotobuf.lib.protofile import PROTO_FILE_TYPE_TO_BBP
from proto_schema_parser import Parser
from proto_schema_parser.ast import (
    Package,
    Message,
    Service,
    File,
    Method,
    Enum,
    Field,
    OneOf,
    FieldCardinality,
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
        proto_element_lists = [
            Parser().parse(proto).file_elements for proto in protos
        ]
        self._proto_ast_dict = {}
        self._packages_dict: dict[str, dict[str, Service]] = {}
        for elem_list in proto_element_lists:
            values_iterator = iter(elem_list)
            package_name = next(x.name for x in values_iterator if isinstance(x, Package))
            self._prepare_ast_dict(package_name, values_iterator)
            self._add_package_to_packages_dict(elem_list)

    def _prepare_ast_dict(self, name, elem_list) -> None:
        for item in elem_list:
            match item:
                case Message():
                    self._proto_ast_dict[f"{name}.{item.name}"] = item
                    self._prepare_ast_dict(f"{name}.{item.name}", item.elements)
                case Enum():
                    self._proto_ast_dict[f"{name}.{item.name}"] = item

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
                message_type_path=f"{package_name}.{method.input_type.type}",
            ),
            response = self._prepare_typedef_message(
                message_type_path=f"{package_name}.{method.output_type.type}",
            )

        )

    def _prepare_typedef_message(self, message_type_path: str):
        ast_item = self._proto_ast_dict[message_type_path]
        match ast_item:
            case Enum():
                return {}
            case Message():
                new = {}
                self._prepare_typedef_element(new, ast_item.elements, message_type_path)
                return new
            case _:
                raise ProtoParserError(f"Unexpected field type for the path {message_type_path} inside proto file")

    def _prepare_typedef_element(self, elems_dict: dict, elements: list, message_type_path: str):
        for element in elements:
            match element:
                case Field():
                    el_num = str(element.number)
                    elems_dict[el_num] = {"name": element.name}
                    if element.cardinality == FieldCardinality.REPEATED:
                        elems_dict[el_num]["seen_repeated"] = True

                    if el_type := PROTO_FILE_TYPE_TO_BBP.get(element.type):
                        elems_dict[el_num]["type"] = el_type
                    # it means that the type came from another .proto file
                    elif self._proto_ast_dict.get(element.type):
                        elems_dict[el_num]["type"] = "message"
                        elems_dict[el_num]["message_typedef"] = self._prepare_typedef_message(
                            message_type_path=element.type
                        )
                    # in other case the type definition is hopefully accessible by full path:
                    else:
                        new_element = self._prepare_typedef_message(
                            message_type_path=self._locate_field_in_ast(message_type_path, element.type)
                        )
                        # assume that it's actually an enum:
                        if not new_element:
                            elems_dict[el_num]["type"] = "uint"
                        # otherwise it definitely should be a message:
                        else:
                            elems_dict[el_num]["type"] = "message"
                            elems_dict[el_num]["message_typedef"] = new_element
                # if it's oneof, all its elements should be added to the same dict:
                case OneOf():
                    self._prepare_typedef_element(elems_dict, element.elements, message_type_path)
                # ToDo: support maps as field values like: map<string, TariffSchemaEntity> tariff_input_parameter_list = 5;

    def _locate_field_in_ast(self, path: str, expected_field_name: str):
        path_fragments = path.split(".")
        while True:
            path_part = ".".join(path_fragments)
            if path_part in self._packages_dict:
                path_part = ".".join(path_fragments + [expected_field_name])
            message = self._proto_ast_dict.get(path_part)
            if not message:
                raise ProtoParserError(f"Field type not found in provided proto files: {expected_field_name}")
            if isinstance(message, (Message, Enum)):
                if message.name == expected_field_name:
                    return path_part
            for element in message.elements:
                if isinstance(element, (Message, Enum)):
                    if element.name == expected_field_name:
                        return f"{path_part}.{element.name}"
            path_fragments.pop()


def parse_proto_file(protos: list[str]) -> ProtoRootStructure:
    parser = ProtoFileParser(protos)
    return parser.parse_protos()
