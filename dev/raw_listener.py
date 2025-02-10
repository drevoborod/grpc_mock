import json
import re
import socket

import blackboxprotobuf
import h2.config
import h2.connection
import h2.events

from dev.proto_file_parser import ProtoParser

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


HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 3333  # Port to listen on (non-privileged ports are > 1023)

def http2_send_response(conn: h2.connection.H2Connection, event):
    stream_id = event.stream_id
    conn.send_headers(
        stream_id=stream_id,
        headers=[
            (":status", "200"),
            ('server', 'basic-h2-server/1.0'),
            ("grpc-status", "0"),
            ('content-type', 'application/grpc'),
            # ("grpc-encoding", "gzip"),
        ]
    )
    conn.send_data(stream_id=stream_id, data=b'it works!', end_stream=True)


def http2_handle(sock):
    config = h2.config.H2Configuration(client_side=False)
    conn = h2.connection.H2Connection(config=config)
    conn.initiate_connection()
    sock.sendall(conn.data_to_send())
    data_counter = 0
    prepared_events = {}
    while True:
        data = sock.recv(4096)
        if not data:
            break
        events = conn.receive_data(data)
        data_counter += 1
        # print("Data chunks received:", data_counter)
        print(events)
        # for event in events:
        #     if isinstance(event, h2.events.DataReceived):
        #         http2_send_response(conn, event)
        for event in events:
            if isinstance(event, h2.events.RequestReceived):
                prepared_events["request"] = event
                http2_send_response(conn, event)
            if isinstance(event, h2.events.DataReceived):
                prepared_events["data"] = event

        if len(prepared_events) == 2:
            parse_grpc_data(prepared_events["data"], prepare_typedef(PROTO, prepared_events["request"]))
        if data_to_send := conn.data_to_send():
            sock.sendall(data_to_send)


def prepare_typedef(proto: str, event: h2.events.RequestReceived):
    parser = ProtoParser(proto)
    typedef = parser.to_typedef()
    path: str = ""
    for header in event.headers:
        if header[0] == b":path":
            path = header[1].decode()
            break
    package, service, method = re.match(r"^/(.+)\.(.+)/(.+)$", path).groups()
    return typedef[package]["services"][service]["methods"][method]["request"]


def parse_grpc_data(event: h2.events.DataReceived, typedef: dict):
    message, _ = blackboxprotobuf.decode_message(event.data[5:], typedef)
    print(message)
    print(json.dumps(message, ensure_ascii=False, indent=4))


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    while True:
        tcp_conn, addr = s.accept()
        with tcp_conn:
            print(f"Connected by {addr}")
            http2_handle(tcp_conn)
