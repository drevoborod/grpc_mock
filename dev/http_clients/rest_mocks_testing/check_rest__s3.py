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
            "response_headers": {"Content-type": "application/octet-stream"}
        },
    ],
    "config_uuid": "REST_DEFAULT_UUID"
}
url = URL(scheme="http", host="127.0.0.1", port=3333, path="/rest_mocks")

res = httpx.post(url, json=payload)

print(res.status_code)
# print(res.content)
print(res.json())