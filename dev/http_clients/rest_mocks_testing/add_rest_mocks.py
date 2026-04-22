import httpx
from httpx import URL


payload = {
    "mocks": [
        {
            "endpoint": "/api/v1/library",
            "method": "POST",
            "response_body": {"transaction_uuid": "111", "user_id": 190},
            "response_status": 201
        },
    ],
    "protos": [PROTO],
    "config_uuid": "UUID"
}
url = URL(scheme="http", host="127.0.0.1", port=3333, path="/http_mocks")

res = httpx.post(url, json=payload)

print(res.status_code)
# print(res.content)
print(res.json())
