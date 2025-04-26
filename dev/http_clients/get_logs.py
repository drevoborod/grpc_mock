import json

import httpx
from httpx import URL


url = URL(scheme="http", host="127.0.0.1", port=3333, path="/logs")
res = httpx.get(url=url, params={"config_uuid": "UUID", "method": "BookAddEndpoint"})

print(res.status_code)
# print(res.content)
print(json.dumps(res.json(), indent=4))
