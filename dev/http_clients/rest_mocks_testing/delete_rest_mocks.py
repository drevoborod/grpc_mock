from uuid import uuid4

import httpx
from httpx import URL


payload = [
        {
            "endpoint": "/ppp",
            "method": "POST",
        },
        {
            "endpoint": "/api/v1/library",
            "method": "GET",
        },
    ]

url = URL(scheme="http", host="127.0.0.1", port=3333, path="/rest_mocks")


for params in payload:
    res = httpx.delete(url, params=params)

    print(res.status_code)
    # print(res.content)
    print(res.json())
