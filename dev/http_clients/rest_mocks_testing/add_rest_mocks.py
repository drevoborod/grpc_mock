import httpx
from httpx import URL


payload = {
    "mocks": [
        {
            "endpoint": "/ppp",
            "method": "POST",
            "response_body": '{"transaction_uuid": "111", "user_id": 190}',
            "response_status": 201
        },
        {
            "endpoint": "/api/v1/library",
            "method": "GET",
            "response_body": None,
            "response_headers": {"content-type": "application/octet-stream"}
        },
        #########
        {
            "endpoint": "/api/v1/body_filtered",
            "method": "POST",
            "response_body": {"status": "filter found"},
            "response_headers": {"content-type": "application/octet-stream"},
            "body_filter": {"$.user.last_name": "John.*"},
        },
        {
            "endpoint": "/api/v1/query_filtered",
            "method": "POST",
            "response_body": {"status": "filter found"},
            "response_headers": {"content-type": "application/octet-stream"},
            "query_params_filter": {"$.parameter": "^*.vizli-putzli$"},
        },
        {
            "endpoint": "/api/v1/headers_filtered",
            "method": "GET",
            "response_body": {"status": "filter found"},
            "response_headers": {"content-type": "application/octet-stream"},
            "headers_filter": {"content-type": "application/pdf"},
        },
        {
            "endpoint": "/api/v1/multi_filtered",
            "method": "GET",
            "response_body": {"status": "filter found"},
            "response_headers": {"Content-type": "application/octet-stream"},
            "query_params_filter": {"$.parameter": "^*.vizli-putzli$"},
            "headers_filter": {"content-type": "application/pdf"},
        },
        {
            "endpoint": "/api/v1/multi_filtered",
            "method": "GET",
            "response_body": {"status": "default filter found"},
            "response_headers": {"content-type": "application/octet-stream"},
        },
        {
            "endpoint": "/file_body",
            "method": "GET",
            "response_body": "dohlopuhl abrikosovich",
            "response_headers": {"content-type": "application/octet-stream"},
        },
    ],
    "config_uuid": "REST_DEFAULT_UUID"
}
url = URL(scheme="http", host="127.0.0.1", port=3333, path="/rest_mocks")

res = httpx.post(url, json=payload)

print(res.status_code)
# print(res.content)
print(res.json())
