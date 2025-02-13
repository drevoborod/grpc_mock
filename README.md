# grpc_mock
Dynamically configurable GRPC mocking service


## REST API
### Set mock service parameters including response

```
POST /runs
body: {
    "mocks": [
        {
            "service": "Books",
            "method": "BookAddEndpoint",
            "response": {}
        },
        {
            "service": "Books",
            "method": "BookRemoveEndpoint",
            "response": {}
        }
    ],
    "proto": "<proto file contents>",
    "config_uuid": "UUID"
}
```


### Get mock service log for specific GRPC method, test run or time period
```
GET /runs
params: 
    {
        "package": "library",
        "service": "Books",
        "method": "BookAddEndpoint",
        "config_uuid": "UUID",
        "from": "2025-01-18T12:33:01.432Z",
        "to": "2025-01-18T12:35:01.432Z"
    }
```
