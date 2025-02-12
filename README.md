# grpc_mock
Dynamically configurable GRPC mocking service


## REST API
### Set mock service parameters including response

```
POST /config
body: {
    "package": "library",
    "service": "Books",
    "method": "BookAddEndpoint",
    "proto": "<proto file contents>",
    "response": {}
}
```


### Get mock service log for specific GRPC method
```
GET /log?package=library&service=Books&method=BookAddEndpoint
```
