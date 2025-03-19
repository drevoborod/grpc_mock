# GRPC mock service
Dynamically configurable GRPC mocking service

## Purpose
The service is intended to be used in isolated testing environments for testing microservices which connected to each other but cannot be controlled directly during testing process.
It is usable for integration automated testing.
The service can be configured in runtime to set up expected requests from another services and responses which have to be answered with.
Also, it stores requests made to it which can be later inspected to be sure that they are correct. 

Typical environment can be like:
* web application backend consisting of several microservices which communicate each other using GRPC.
* some of them require to be mocked because they aren't necessary for testing purpose (or it can be external system which should not be accessed during testing process.)

Typical automatic test scenario can be like:
1. The service to be tested (let's call it "service 1") is pre-configured to call GRPC-mock instead of real another service (let's call it "mocked service").
2. Before the test begins (during the setup process) mock service is configured by REST request to response to specific GRPC request by sending provided data.
3. During the test execution it takes some steps which involve service 1 indirectly so it requests mocked service for some data.
4. Instead of real mocked service, mock GRPC service responds with prepared mock data added to it during p.2.
5. Test code can request mock service using another REST endpoint for logged request made by service 1, which can be validated.

## Requirements
* Python 3.12+
* uv
* All packages listed in pyproject.toml (should be installed by running `uv sync`).

## Running
Actually the service needs to be integrated to your testing environment. But if you'd like to run it locally, it can be done with following commands:
1. Copy the file `.env.default` to `.env`. It's the place where configuration parameters are taken from.
2. `make db.run`
3. `make db.migrate`
4. `make dev.run`. The service will run in terminal and should be ready to accept connections.

To stop running service:
1. Control+C in the terminal.
2. `make db.clean` to stop and destroy database container.


## REST API
### Set mock service parameters including response
#### Example
```
POST /mocks
body: {
    "mocks": [
        {
            "package": "library",
            "service": "Books",
            "method": "BookAddEndpoint",
            "response": {},
            "response_status": 0
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
`config_uuid` is some string which can be unique for every test run so it can be used to easily obtain corresponding logs.
Actually, they do not really correspond to the specific test run but will be same until the configuration for provided package+service+method configuration changes. 

### Get mock service log for specific GRPC method or test run
#### Example
```
GET /logs
Query params: 
    {
        "package": "library",
        "service": "Books",
        "method": "BookAddEndpoint",
        "config_uuid": "UUID",
    }
```

### Get current mocks configuration
#### Example
```
GET /mocks
Query params: 
    {
        "package": "library",
        "service": "Books",
        "method": "BookAddEndpoint",
    }
```

### Delete mock for specific GRPC endpoint
#### Example
```
DELETE /mocks
Query params: 
    {
        "package": "library",
        "service": "Books",
        "method": "BookAddEndpoint",
    }
```


