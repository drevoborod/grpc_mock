import httpx
from httpx import URL


port = 3333
scheme = "http"
host = "127.0.0.1"

requests = [
    {
        "url": URL(scheme=scheme, host=host, port=port, path="/ppp"),
        "method": "POST",
        "json": {"aaaaa": 111}
    },
    {
        "url": URL(scheme=scheme, host=host, port=port, path="/ppp"),
        "method": "POST",
        "data": "AAAAAA!~!!!!"
    },
    {
        "url": URL(scheme=scheme, host=host, port=port, path="/api/v1/library"),
        "method": "GET",
        "data": None,
        "params": {"param_22": "param33"}
    },
    {
        "url": URL(scheme=scheme, host=host, port=port, path="/unknown_path"),
        "method": "GET",
        "data": None,
    },
    {
        "url": URL(scheme=scheme, host=host, port=port, path="/unknown_path"),
        "method": "GET",
        "params": {"param_1": "param"}
    },
    {
        "url": URL(scheme=scheme, host=host, port=port, path="/api/v1/body_filtered"),
        "method": "GET",
        "params": {"param_1": "param"},
        "data": "KROKODILA!",
    },
    {
        "url": URL(scheme=scheme, host=host, port=port, path="/api/v1/body_filtered"),
        "method": "GET",
        "params": {"param_1": "param"},
        "json": {"KROKODILA!": "BEGEMOTA!", "user": {"last_name": "Peter"}},
    },
    {
        "url": URL(scheme=scheme, host=host, port=port, path="/api/v1/body_filtered"),
        "method": "GET",
        "params": {"param_11": "param11"},
        "json": {"KROKODILA!": "BEGEMOTA!", "user": {"last_name": "John Doe"}},
    },
    {
        "url": URL(scheme=scheme, host=host, port=port, path="/api/v1/body_filtered"),
        "method": "POST",
        "params": {"param_11": "param11"},
        "json": {"KROKODILA!": "BEGEMOTA!", "user": {"last_name": "John Doe"}},
    },
    {
        "url": URL(scheme=scheme, host=host, port=port, path="/api/v1/query_filtered"),
        "method": "GET",
        "params": {"param_11": "param11"},
        "json": {"KROKODILA!": "BEGEMOTA!", "user": {"last_name": "John Doe"}},
    },
    {
        "url": URL(scheme=scheme, host=host, port=port, path="/api/v1/query_filtered"),
        "method": "GET",
        "params": {"param_11": "param11", "parameter": "bububu_vizli-putzli"},
        "json": {"KROKODILA!": "BEGEMOTA!", "user": {"last_name": "John Doe"}},
    },
    {
        "url": URL(scheme=scheme, host=host, port=port, path="/api/v1/headers_filtered"),
        "method": "GET",
        "params": {"param_11": "param11", "parameter": "bububu_vizli-putzli"},
        "json": {"KROKODILA!": "BEGEMOTA!", "user": {"last_name": "John Doe"}},
        "headers": {"content-type": "application/pdf"}
    },
    {
        "url": URL(scheme=scheme, host=host, port=port, path="/api/v1/multi_filtered"),
        "method": "GET",
        "params": {"param_11": "param11", "parameter": "bububu_vizli-putzli"},
        "json": {"KROKODILA!": "BEGEMOTA!", "user": {"last_name": "John Doe"}},
        "headers": {"Content-type": "application/pdf"}
    },
    {
        "url": URL(scheme=scheme, host=host, port=port, path="/api/v1/multi_filtered"),
        "method": "GET",
        "params": {"param_11": "param11", "parameter": "eggs"},
        "json": {"KROKODILA!": "BEGEMOTA!", "user": {"last_name": "John Doe"}},
        "headers": {"Content-type": "application/pdf"}
    },
    {
        "url": URL(scheme=scheme, host=host, port=port, path="/file_body"),
        "method": "GET",
        "params": {"param_11": "param11", "parameter": "bububu_vizli-putzli"},
        "json": {"KROKODILA!": "BEGEMOTA!", "user": {"last_name": "John Doe"}},
        "headers": {"content-type": "application/pdf"}
    },
]


for r in requests:
    res = httpx.request(**r)
    print(r)

    print(res.status_code)
    # print(res.content)
    print(res.json())
    print()
