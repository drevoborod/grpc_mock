LIBRARY_PROTO = """
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

MOCK_SERVICE_PROTO = """
syntax = "proto3";
package grpc_mock;


service Configurator {
  rpc SetConfig (ConfigRequest) returns (ConfigResponse) {}
}

service Logger {
  rpc GetLog (LogRequest) returns (LogResponse) {}
}


message ProtoStructure {
  string package = 1;
  string service = 2;
  string method = 3;
  optional string host = 4;
}

message ConfigRequest {
  ProtoStructure proto_structure = 1;
  string proto = 2;
  string response_json = 3;
}

message ConfigResponse {}

message LogRequest {
  ProtoStructure proto_structure = 1;
}

message LogResponse {
  string request_json = 1;
}
"""
