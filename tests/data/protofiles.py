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

LIBRARY_PROTO_PACKAGE_NAME_WITH_DOTS = """
syntax = "proto3";
package big.home.library;


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


MOCK_SERVICE_PROTO_2_SERVICES = """
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

PROTO_TO_BE_IMPORTED = """
syntax = "proto3";

package employer.calculator;

message AnyType {
  message ArrayInt64 {
    repeated int64 values = 1;
  }

  message ArrayString {
    repeated string values = 1;
  }

  oneof value {
    int64 int64 = 1;
    string decimal = 2;
    string text = 3;
    bool bool = 4;
    ArrayInt64 array_int64 = 5;
    ArrayString array_text = 6;
  }
}
"""

PROTO_WITH_IMPORT = """
syntax = "proto3";

package employer.calculator;

import "employer.calculator.common.proto";

import "google/protobuf/timestamp.proto";


service TariffService {
  rpc TariffInfo(TariffInfoRequest) returns (TariffInfoReply) {}
  rpc TariffSchemaInfo(TariffSchemaInfoRequest) returns (TariffSchemaInfoReply) {}
}

message TariffInfoRequest {
  message Parameters {
    int64 calculator_type = 1; // @gotags: validate:"required"
    optional string tariff_id = 2;
    // tariff_ts calculation_time
    optional google.protobuf.Timestamp tariff_ts = 3;
    // meta_data metadata
    // map<string, AnyType> meta_data = 4;
  }

  repeated Parameters parameters = 1;
}

message TariffInfoReply {
  enum ERR_INFO_REASON {
    UNSPECIFIED = 0;
    VALIDATION_ERROR = 1;
    NOT_FOUND = 2;
  }

  message Tariff {
    int64 calculator_type = 1;
    string tariff_id = 2;
    google.protobuf.Timestamp started_at = 3;
    optional google.protobuf.Timestamp finished_at = 4;
    map<string, AnyType> tariff_parameters = 5;
  }
  repeated Tariff tariffs = 1;
}

message TariffSchemaInfoRequest {
  message Parameters {
    int64 calculator_type = 1; // @gotags: validate:"required"
    optional string tariff_id = 2;
    optional google.protobuf.Timestamp tariff_ts = 3;
  }

  repeated Parameters parameters = 1;
}

message TariffSchemaInfoReply {
  enum ERR_INFO_REASON {
    UNSPECIFIED = 0;
    VALIDATION_ERROR = 1;
    NOT_FOUND = 2;
  }

  message TariffSchema {
    message TariffSchemaEntity {
      string description = 1;
      string type = 2;
      bool required = 3;
    }

    int64 calculator_type=1;
    string tariff_id =  2;
    google.protobuf.Timestamp started_at= 3;
    optional google.protobuf.Timestamp finished_at =4;
    map<string, TariffSchemaEntity> tariff_input_parameter_list = 5;
    map<string, TariffSchemaEntity> tariff_output_parameter_list = 6;
  }
  repeated TariffSchema tariff_schemas = 1;
}
"""
