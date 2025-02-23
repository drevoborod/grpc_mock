import httpx
from httpx import URL


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
  int64 user_id = 2;
}

message BookRemoveRequest {
  string book_uuid = 1;
  int64 user_id = 2;
  string timestamp = 3;
}

message BookRemoveReply {
  string transaction_uuid = 1;
  int64 user_id = 2;
}

// The library service definition.
service Books {
  rpc BookAddEndpoint (BookAddRequest) returns (BookAddReply) {}
  rpc BookRemoveEndpoint (BookRemoveRequest) returns (BookRemoveReply) {}
}

"""

payload = {
    "mocks": [
        {
            "package": "library",
            "service": "Books",
            "method": "BookAddEndpoint",
            "response": {"transaction_uuid": "111", "user_id": 190}
        },
        {
            "package": "library",
            "service": "Books",
            "method": "BookRemoveEndpoint",
            "response": {"transaction_uuid": "333", "user_id": 222}
        }
    ],
    "protos": [PROTO],
    "config_uuid": "UUID"
}
url = URL(scheme="http", host="127.0.0.1", port=3333, path="/mocks")

res = httpx.post(url, json=payload)

print(res.status_code)
# print(res.content)
print(res.json())
