import re
import socket

import blackboxprotobuf
import h2.config
import h2.connection
import h2.events

from grpc_mock.proto_parser import (
    ProtoMethodStructure,
    get_request_typedef_from_proto_package,
    parse_proto_file,
)
from grpc_mock.repository import get_mock_from_storage


HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 3333  # Port to listen on (non-privileged ports are > 1023)


def get_proto_metadata_from_request(
    event: h2.events.RequestReceived,
) -> ProtoMethodStructure:
    """
    Parses GRPC request object and returns a model representing protobuf metadata:
    package, service and method names.

    """
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
    return ProtoMethodStructure(
        host=host, package=package, service=service, method=method
    )


def http2_send_response(conn: h2.connection.H2Connection, event):
    stream_id = event.stream_id
    conn.send_headers(
        stream_id=stream_id,
        headers=[
            (":status", "200"),
            ("server", "basic-h2-server/1.0"),
            ("grpc-status", "0"),
            ("content-type", "application/grpc"),
            # ("grpc-encoding", "gzip"),
        ],
    )
    conn.send_data(stream_id=stream_id, data=b"it works!", end_stream=True)


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

        if data_to_send := conn.data_to_send():
            sock.sendall(data_to_send)

    if len(prepared_events) == 2:
        proto_path = get_proto_metadata_from_request(prepared_events["request"])
        proto_package = parse_proto_file(get_mock_from_storage(proto_path))
        parse_grpc_data(
            prepared_events["data"],
            get_request_typedef_from_proto_package(proto_package, proto_path),
        )


def parse_grpc_data(event: h2.events.DataReceived, typedef: dict):
    message, _ = blackboxprotobuf.decode_message(event.data[5:], typedef)
    print(message)
    # print(json.dumps(message, ensure_ascii=False, indent=4))


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    while True:
        tcp_conn, addr = s.accept()
        with tcp_conn:
            print(f"Connected by {addr}")
            http2_handle(tcp_conn)
