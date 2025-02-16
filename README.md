# grpc_mock
Dynamically configurable GRPC mocking service


## REST API
### Set mock service parameters including response

```
POST /runs
body: {
    "mocks": [
        {
            "package": "library",
            "service": "Books",
            "method": "BookAddEndpoint",
            "response": {}
        },
        {
            "package": "library",
            "service": "Books",
            "method": "BookRemoveEndpoint",
            "response": {}
        }
    ],
    "protos": ["<proto file1 contents>", "<proto file2 contents>"],
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
    }
```
