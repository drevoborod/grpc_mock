import httpx
from httpx import URL


url = URL(scheme="http", host="127.0.0.1", port=3333, path="/mocks")

params = {
            "package": "library",
            "service": "Books",
            "method": "BookAddEndpoint",
        }

res = httpx.delete(url, params=params)

print(res.status_code)
# print(res.content)
# print(res.json())
