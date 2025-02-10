import json

from blackboxprotobuf.lib.protofile import PROTO_FILE_TYPE_TO_BBP, import_proto
from blackboxprotobuf.lib.config import default as default_config
from proto_schema_parser import Parser
from proto_schema_parser.ast import Package, Message, Service, File, Method, Enum

PROTO = """
syntax = "proto3";
package library;


message Author {
  string last_name = 1;
  string first_name = 2;
  optional string second_name = 3;
}

message BookMetadata {
  message Publisher {
    string name = 1;
  }

  string name = 1;
  int32 year = 2;
  repeated Author authors = 3;
  optional Publisher publisher = 4;
}

message BookAddRequest {
  message User {
    enum Sex {
      MALE = 0;
      FEMALE = 1;
    }
    string last_name = 1;
    string first_name = 2;
    optional string second_name = 3;
    optional Sex sex = 4;
  }

  string book_uuid = 1;
  int64 user_id = 2;
  string timestamp = 3;
  optional BookMetadata metadata = 4;
  optional User user = 5;
}

message BookAddReply {
  string transaction_uuid = 1;
}

message BookRemoveRequest {
  string book_uuid = 1;
  int64 user_id = 2;
  string timestamp = 3;
}

message BookRemoveReply {
  string transaction_uuid = 1;
}

// The library service definition.
service Books {
  rpc BookAddEndpoint (BookAddRequest) returns (BookAddReply) {}
  rpc BookRemoveEndpoint (BookRemoveRequest) returns (BookRemoveReply) {}
}

"""

class ProtoParserError(Exception): pass

type ProtoElement = Message | Service | Package | File | Method | Enum


class ProtoParser:
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
        self._messages: dict[str, Message] = {}
        for item in self._proto_elements:
            match item:
                case Package():
                    _packages.append(item.name)
                case Service():
                    self._services[item.name] = item
                case Message():
                    self._messages[item.name] = item
        if len(_packages) != 1:
            raise ProtoParserError("Provided file contains incorrect quantity of package definitions.")
        self.package_name = _packages[0]

    def to_typedef(self) -> dict:
        return {
            self.package_name: {
                "services": self._prepare_services()
            }
        }

    def _prepare_services(self) -> dict:
        return {key: self._prepare_methods_in_service(value) for key, value in self._services.items()}

    def _prepare_methods_in_service(self, service: Service) -> dict:
        methods = {}
        for item in service.elements:
            if isinstance(item, Method):
                methods[item.name] = self._prepare_method(item)
        return {"methods": methods}

    def _prepare_method(self, method: Method) -> dict:
        return {
            "request": self._prepare_typedef_message(self._raw_typedef[f"{self.package_name}.{method.input_type.type}"]),
            "response": self._prepare_typedef_message(self._raw_typedef[f"{self.package_name}.{method.output_type.type}"]),
        }

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



if __name__ == "__main__":
    parser = ProtoParser(PROTO)
    # print(json.dumps(parser._raw_typedef, indent=4))
    print(json.dumps(parser.to_typedef(), indent=4))
