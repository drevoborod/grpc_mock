import httpx
from httpx import URL


payload = {"param1": "test"}
url = URL(scheme="http", host="127.0.0.1", port=3333, path="/config")
res = httpx.post(url, json=payload)
print(res.status_code)
# print(res.content)

print(res.json())