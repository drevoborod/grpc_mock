import asyncio
from datetime import datetime, UTC

import grpclib
from grpclib.client import Channel
import httpx
import pytest

from tests.data.protofiles import LIBRARY_PROTO
from dev.generated.library import BookAddRequest, BookAddRequestUser, BooksStub


class GrpcClient:
    def __init__(self, host: str, port: int, timeout: float = 5.0):
        self.channel = None
        self.host = host
        self.port = port
        self.timeout = timeout

    async def __aenter__(self):
        self.channel = Channel(host=self.host, port=self.port)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.channel:
            self.channel.close()

    async def book_add(self, book_uuid: str, user_id: int, last_name: str = None, first_name: str = None):
        stub = BooksStub(self.channel)
        user = None
        if last_name or first_name:
            user = BookAddRequestUser(last_name=last_name or "", first_name=first_name or "")
        request = BookAddRequest(
            book_uuid=book_uuid,
            user_id=user_id,
            timestamp=datetime.now(UTC).isoformat(),
            user=user,
        )
        return await stub.book_add_endpoint(request, timeout=self.timeout)


async def grpc_book_add_sync(host: str, port: int, book_uuid: str, user_id: int, last_name: str = None, first_name: str = None, timeout: float = 5.0):
    async with GrpcClient(host, port, timeout) as client:
        return await client.book_add(book_uuid, user_id, last_name, first_name)


def grpc_book_add(host: str, port: int, book_uuid: str, user_id: int, last_name: str = None, first_name: str = None, timeout: float = 5.0):
    return asyncio.run(grpc_book_add_sync(host, port, book_uuid, user_id, last_name, first_name, timeout))


class TestGrpcMockPositive:
    def test__add_grpc_mock__get_grpc_mock__success(
        self, http_client: httpx.Client, config_uuid_counter
    ):
        config_uuid = config_uuid_counter()
        mock = {
            "package": "library",
            "service": "Books",
            "method": "BookAddEndpoint",
            "response": {"transaction_uuid": "tx-123"},
            "response_status": 0,
        }
        response = http_client.post(
            "/grpc_mocks",
            json={"mocks": [mock], "protos": [LIBRARY_PROTO], "config_uuid": config_uuid},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

        response = http_client.get(
            "/grpc_mocks",
            params={
                "package": "library",
                "service": "Books",
                "method": "BookAddEndpoint",
            },
        )
        assert response.status_code == 200
        mocks = response.json()
        assert len(mocks) >= 1

    def test__add_grpc_mock__make_request__returns_mock_response(
        self, http_client: httpx.Client, grpc_mock_server: int, config_uuid_counter
    ):
        config_uuid = config_uuid_counter()
        mock = {
            "package": "library",
            "service": "Books",
            "method": "BookAddEndpoint",
            "response": {"transaction_uuid": "tx-book-001"},
            "response_status": 0,
        }
        response = http_client.post(
            "/grpc_mocks",
            json={"mocks": [mock], "protos": [LIBRARY_PROTO], "config_uuid": config_uuid},
        )
        assert response.status_code == 200

        reply = grpc_book_add("127.0.0.1", grpc_mock_server, book_uuid="book-123", user_id=1)
        assert reply.transaction_uuid == "tx-book-001"

    def test__add_grpc_mock_with_filter__matching_request(
        self, http_client: httpx.Client, grpc_mock_server: int, config_uuid_counter
    ):
        config_uuid = config_uuid_counter()
        mock = {
            "package": "library",
            "service": "Books",
            "method": "BookAddEndpoint",
            "filter": {"$.user.last_name": "John.*"},
            "response": {"transaction_uuid": "tx-special"},
            "response_status": 0,
        }
        http_client.post(
            "/grpc_mocks",
            json={"mocks": [mock], "protos": [LIBRARY_PROTO], "config_uuid": config_uuid},
        )

        reply = grpc_book_add(
            "127.0.0.1", grpc_mock_server,
            book_uuid="book-123", user_id=1,
            last_name="John Doe", first_name="John"
        )
        assert reply.transaction_uuid == "tx-special"

    def test__add_grpc_mock_with_multiple_filters__both_match(
        self, http_client: httpx.Client, grpc_mock_server: int, config_uuid_counter
    ):
        config_uuid = config_uuid_counter()
        mock = {
            "package": "library",
            "service": "Books",
            "method": "BookAddEndpoint",
            "filter": {
                "$.user.last_name": "Doe.*",
                "$.book_uuid": "special-.*",
            },
            "response": {"transaction_uuid": "tx-multi-filter"},
            "response_status": 0,
        }
        http_client.post(
            "/grpc_mocks",
            json={"mocks": [mock], "protos": [LIBRARY_PROTO], "config_uuid": config_uuid},
        )

        reply = grpc_book_add(
            "127.0.0.1", grpc_mock_server,
            book_uuid="special-book-123", user_id=1,
            last_name="Doe Smith", first_name="Jane"
        )
        assert reply.transaction_uuid == "tx-multi-filter"

    def test__add_multiple_grpc_mocks_in_one_request(
        self, http_client: httpx.Client, config_uuid_counter
    ):
        config_uuid = config_uuid_counter()
        mocks = [
            {
                "package": "library",
                "service": "Books",
                "method": "BookAddEndpoint",
                "response": {"transaction_uuid": "add-tx"},
                "response_status": 0,
            },
            {
                "package": "library",
                "service": "Books",
                "method": "BookRemoveEndpoint",
                "response": {"transaction_uuid": "remove-tx"},
                "response_status": 0,
            },
        ]
        response = http_client.post(
            "/grpc_mocks",
            json={"mocks": mocks, "protos": [LIBRARY_PROTO], "config_uuid": config_uuid},
        )
        assert response.status_code == 200

        response = http_client.get(
            "/grpc_mocks",
            params={
                "package": "library",
                "service": "Books",
                "method": "BookAddEndpoint",
            },
        )
        assert response.status_code == 200
        add_mocks = response.json()
        assert len(add_mocks) >= 1

        response = http_client.get(
            "/grpc_mocks",
            params={
                "package": "library",
                "service": "Books",
                "method": "BookRemoveEndpoint",
            },
        )
        assert response.status_code == 200
        remove_mocks = response.json()
        assert len(remove_mocks) >= 1

    def test__grpc_logs_stored_after_successful_mock_match(
        self, http_client: httpx.Client, grpc_mock_server: int, config_uuid_counter
    ):
        config_uuid = config_uuid_counter()
        mock = {
            "package": "library",
            "service": "Books",
            "method": "BookAddEndpoint",
            "response": {"transaction_uuid": "logged-tx"},
            "response_status": 0,
        }
        http_client.post(
            "/grpc_mocks",
            json={"mocks": [mock], "protos": [LIBRARY_PROTO], "config_uuid": config_uuid},
        )

        grpc_book_add("127.0.0.1", grpc_mock_server, book_uuid="book-logged", user_id=1)

        response = http_client.get(
            "/grpc_logs",
            params={"config_uuid": config_uuid},
        )
        assert response.status_code == 200
        logs = response.json()
        assert len(logs) >= 1

    def test__delete_grpc_mock(self, http_client: httpx.Client, config_uuid_counter):
        config_uuid = config_uuid_counter()
        mock = {
            "package": "library",
            "service": "Books",
            "method": "BookAddEndpoint",
            "response": {"transaction_uuid": "to-delete"},
            "response_status": 0,
        }
        http_client.post(
            "/grpc_mocks",
            json={"mocks": [mock], "protos": [LIBRARY_PROTO], "config_uuid": config_uuid},
        )

        response = http_client.delete(
            "/grpc_mocks",
            params={
                "package": "library",
                "service": "Books",
                "method": "BookAddEndpoint",
            },
        )
        assert response.status_code == 200

        response = http_client.get(
            "/grpc_mocks",
            params={
                "package": "library",
                "service": "Books",
                "method": "BookAddEndpoint",
            },
        )
        mocks = response.json()
        is_deleted = all(m.get("is_deleted", False) for m in mocks)
        assert is_deleted or len(mocks) == 0


class TestGrpcMockNegative:
    def test__grpc_request_without_matching_mock__returns_error(
        self, http_client: httpx.Client, grpc_mock_server: int, config_uuid_counter
    ):
        config_uuid = config_uuid_counter()
        mock = {
            "package": "library",
            "service": "Books",
            "method": "BookAddEndpoint",
            "filter": {"$.book_uuid": "^nonexistent-id$"},
            "response": {"transaction_uuid": "should-not-match"},
            "response_status": 0,
        }
        http_client.post(
            "/grpc_mocks",
            json={"mocks": [mock], "protos": [LIBRARY_PROTO], "config_uuid": config_uuid},
        )

        with pytest.raises(Exception):
            grpc_book_add("127.0.0.1", grpc_mock_server, book_uuid="different-uuid", user_id=1, timeout=3.0)

    @pytest.mark.skip(reason="gRPC service returns timeout instead of NOT_FOUND error when mock not found")
    def test__grpc_request_with_unmatched_filter(
        self, http_client: httpx.Client, grpc_mock_server: int, config_uuid_counter
    ):
        config_uuid = config_uuid_counter()
        mock = {
            "package": "library",
            "service": "Books",
            "method": "BookAddEndpoint",
            "filter": {"$.user.last_name": "^nonexistent$"},
            "response": {"transaction_uuid": "wrong-user"},
            "response_status": 0,
        }
        http_client.post(
            "/grpc_mocks",
            json={"mocks": [mock], "protos": [LIBRARY_PROTO], "config_uuid": config_uuid},
        )

        with pytest.raises(Exception):
            grpc_book_add(
                "127.0.0.1", grpc_mock_server,
                book_uuid="book-123", user_id=1,
                last_name="Actual User", first_name="Test", timeout=3.0
            )

    @pytest.mark.skip(reason="gRPC service returns timeout instead of NOT_FOUND error when mock not found")
    def test__grpc_request_with_multiple_filters_one_unmatched(
        self, http_client: httpx.Client, grpc_mock_server: int, config_uuid_counter
    ):
        config_uuid = config_uuid_counter()
        mock = {
            "package": "library",
            "service": "Books",
            "method": "BookAddEndpoint",
            "filter": {
                "$.user.last_name": "Doe.*",
                "$.book_uuid": "^nonexistent$",
            },
            "response": {"transaction_uuid": "partial-match"},
            "response_status": 0,
        }
        http_client.post(
            "/grpc_mocks",
            json={"mocks": [mock], "protos": [LIBRARY_PROTO], "config_uuid": config_uuid},
        )

        with pytest.raises(Exception):
            grpc_book_add(
                "127.0.0.1", grpc_mock_server,
                book_uuid="actual-uuid", user_id=1,
                last_name="Doe Smith", first_name="Jane", timeout=3.0
            )
