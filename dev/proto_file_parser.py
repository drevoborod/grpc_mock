import json

from blackboxprotobuf.lib.protofile import PROTO_FILE_TYPE_TO_BBP, import_proto
from blackboxprotobuf.lib.config import default as default_config


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
  string book_uuid = 1;
  int64 user_id = 2;
  string timestamp = 3;
  optional BookMetadata metadata = 4;
  
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


# type ProtoElement = Message | Service | Package | File | Method
#
# class ProtoParser:
#     def __init__(self, proto: str) -> None:
#         """
#         Helps to prepare type definitions of all messages in provided proto file.
#         Type definitions are intended to use with blackboxprotobuf.
#
#         :param proto: .proto file contents.
#         """
#         self.proto_elements: list[ProtoElement] = Parser().parse(proto).file_elements
#         _packages: list[str] = []
#         self._services: dict[str, Service] = {}
#         self._messages: dict[str, Message] = {}
#         for item in self.proto_elements:
#             match item:
#                 case Package():
#                     _packages.append(item.name)
#                 case Service():
#                     self._services[item.name] = item
#                 case Message():
#                     self._messages[item.name] = item
#         if len(_packages) != 1:
#             raise ProtoParserError("Provided file contains incorrect quantity of package definitions.")
#         self.package_name = _packages[0]
#
#
#     def to_typedef(self) -> dict:
#         return {
#             "package": self.package_name,
#             "services": self._prepare_services()
#         }
#
#     def _prepare_services(self) -> dict:
#         return {key: self._prepare_methods_in_service(value) for key, value in self._services.items()}
#
#     def _prepare_methods_in_service(self, service: Service) -> dict:
#         methods = {}
#         for item in service.elements:
#             if isinstance(item, Method):
#                 methods[item.name] = self._prepare_method(item)
#         return {"methods": methods}
#
#     def _prepare_method(self, method: Method) -> dict:
#         return {
#             "request": self._prepare_message_type_definition(self._messages[method.input_type.type]),
#             "response": self._prepare_message_type_definition(self._messages[method.output_type.type]),
#         }
#
#     def _prepare_message_type_definition(self, message: Message) -> dict:
#         result = {}
#         # for item in message.elements:
#         #     if
#         #     result[str(item.number)] = {
#         #         "name":
#         #     }
#         return result

class ProtoParser:
    def __init__(self, proto: str) -> None:
        """
        Helps to prepare type definitions of all messages in provided proto file.
        Type definitions are intended to use with blackboxprotobuf.

        :param proto: .proto file contents.
        """
        self._raw_typedef = import_proto(default_config, input_string=proto)

    def to_typedef(self):
        new = {}
        for key, value in self._raw_typedef.items():
            new[key] = self._prepare_typedef_message(value)
        return new

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
    print(json.dumps(parser.to_typedef(), indent=4))