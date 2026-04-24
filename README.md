# GRPC mock service
Dynamically configurable gRPC and REST (HTTP) mocking service

# Purpose
The service is intended to be used in isolated testing environments for testing microservices which connected to each other but cannot be controlled directly during testing process.
It is usable for integration automated testing.
The service can be configured in runtime to set up expected requests from another services and responses which have to be answered with.
Also, it stores requests made to it which can be later inspected to be sure that they are correct. 

Typical environment can be like:
* web application backend consisting of several microservices which communicate with each other using gRPC over HTTP 2.0 or HTTP 1.1 with REST.
* some of them require to be mocked because they aren't required for testing purposes (or it can be an external system which should not be accessed during testing process.)

Typical automatic test scenario can be like:
1. The service to be tested (let's call it "service 1") is pre-configured to call mock server instead of another actual service (let's call it "mocked service").
2. Before the test begins (during the setup process) mock service is configured by REST requests to respond to specific gRPC or REST request by sending provided data (using POST /grpc_mock or /rest_mock endpoints).
3. During the test execution it takes some steps which involve service 1 indirectly so it requests mocked service for some data.
4. Instead of real mocked service, mock service responds with prepared mock data added to it during p.2.
5. Test code can request mock service using another REST endpoint for logged request made by service 1, which can be validated later (these are GET /grpc_logs or /rest_logs depending on which mock type you are using).


# Running
Actually the service needs to be integrated to your testing environment. But if you'd like to run it locally, 
it can be done by following different ways. The service support different kinds of databases: SQLite and Postgres, 
so the way you start it depends on the chosen database. To stop running service, enter Control+C in the terminal.

## Run in Docker with Postgres support
1. Copy the file `.env.default_postgres` to `.env`. It's the place where configuration parameters are taken from.
2. `make run-postgres`

## Run in Docker with Sqlite support
1. Copy the file `.env.default_sqlite` to `.env`. It's the place where configuration parameters are taken from.
2. `make run-sqlite`

## Run locally with Sqlite support
### Requirements
* Python 3.12+
* uv
* All packages listed in pyproject.toml (should be installed by executing `uv sync`).

1. Satisfy all requirements.
2. Copy the file `.env.default_sqlite` to `.env`. It's the place where configuration parameters are taken from.
3. `make run`


# Usage (RESTful API)
Default base URL is: `http://localhost:3333`. 
The port can be changed in `.env` file by altering `GRPC_MOCK_PORT` value.

The actual configuration endpoints are listed in `docs/openapi/swagger.yaml`.
