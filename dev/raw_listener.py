import socket

import h2.config
import h2.connection
import h2.events


HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 3333  # Port to listen on (non-privileged ports are > 1023)

def http2_send_response(conn: h2.connection.H2Connection, event):
    stream_id = event.stream_id
    conn.send_headers(
        stream_id=stream_id,
        headers=[
            (":status", "200"),
            ('server', 'basic-h2-server/1.0'),
        ]
    )
    conn.send_data(stream_id=stream_id, data=b'it works!', end_stream=True)


def http2_handle(sock):
    config = h2.config.H2Configuration(client_side=False)
    conn = h2.connection.H2Connection(config=config)
    conn.initiate_connection()
    sock.sendall(conn.data_to_send())
    data_counter = 0
    while True:
        data = sock.recv(4096)
        if not data:
            break
        events = conn.receive_data(data)
        data_counter += 1
        print("Data chunks received:", data_counter)
        print(events)
        # for event in events:
        #     if isinstance(event, h2.events.DataReceived):
        #         http2_send_response(conn, event)
        for event in events:
            if isinstance(event, h2.events.RequestReceived):
                http2_send_response(conn, event)
        if data_to_send := conn.data_to_send():
            sock.sendall(data_to_send)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    while True:
        tcp_conn, addr = s.accept()
        with tcp_conn:
            print(f"Connected by {addr}")
            http2_handle(tcp_conn)
