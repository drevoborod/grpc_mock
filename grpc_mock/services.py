import asyncio
import json
from datetime import datetime, UTC
import re

import blackboxprotobuf
from jsonpath import jsonpath

from grpc_mock.models import GrpcMockFromStorage, RestMockFromStorage
from grpc_mock.proto_parser import parse_proto_file, ProtoMethod
from grpc_mock.repo import MockRepo, LogRepo, DatabaseError, MockType
from grpc_mock.schemas import GrpcMockFromSetRequest, RestMockFromSetRequest, RestMockedResponse


class MockResponsePreparationError(Exception):
    pass


class GrpcMockService:
    def __init__(self, repo: MockRepo):
        self.repo = repo

    async def store_grpc_mocks(
        self,
        protos: list[str],
        config_uuid: str,
        mocks: list[GrpcMockFromSetRequest],
    ) -> None:
        """
        Parse mocks from a configuration request and save them to the storage.
        Before new mocks are saved, old ones are disabled.
        Old mocks are being located by package_name+service_name+method_name+filter.
        If no filter provided, corresponding mocks WITH filters will not be disabled!
        In such case, only ones that have no filter will be disabled.
        """
        root_structure = parse_proto_file(protos)
        for mock in mocks:
            await self._disable_old_grpc_mocks(
                package_name=mock.package,
                service_name=mock.service,
                method_name=mock.method,
                mock_filter=mock.filter,
            )

            method: ProtoMethod = (
                root_structure.packages[mock.package]
                .services[mock.service]
                .methods[mock.method]
            )

            await self.repo.add_grpc_mock_to_storage(
                config_uuid=config_uuid,
                package_name=mock.package,
                service_name=mock.service,
                method_name=mock.method,
                mock_filter=json.dumps(mock.filter),
                request_schema=json.dumps(method.request),
                response_schema=json.dumps(method.response),
                response_mock=json.dumps(mock.response, ensure_ascii=False),
                response_status=mock.response_status,
            )

    async def _disable_old_grpc_mocks(
        self,
        package_name: str,
        service_name: str,
        method_name: str,
        mock_filter: dict[str, str] | None,
    ):
        mocks = await self.get_grpc_mocks(
            package=package_name,
            service=service_name,
            method=method_name,
        )

        if mock_filter:
            mock_ids = [mock.id for mock in mocks if mock.filter == mock_filter]
        else:
            mock_ids = [mock.id for mock in mocks if not mock.filter]

        await self.repo.update_mock(
            MockType.grpc,
            mock_ids,
            updated_at=datetime.now(UTC),
            is_deleted=True,
        )

    async def get_grpc_mocks(
        self, package, service, method
    ) -> list[GrpcMockFromStorage]:
        try:
            res = await self.repo.get_grpc_mocks_from_storage(
                package=package, service=service, method=method
            )
        except DatabaseError:
            return []
        return res

    async def delete_grpc_mocks(self, package, service, method) -> None:
        ids = [x.id for x in await self.get_grpc_mocks(package=package, service=service, method=method)]
        await self.repo.update_mock(MockType.grpc, mock_ids=ids, updated_at=datetime.now(UTC), is_deleted=True)


class RestMockService:
    def __init__(self, repo: MockRepo):
        self.repo = repo

    async def store_rest_mocks(
        self,
        config_uuid: str,
        mocks: list[RestMockFromSetRequest],
    ) -> None:
        """
        Parse mocks from a configuration request and save them to the storage.
        Before new mocks are saved, old ones are disabled.
        Old mocks are being located by endpoint+method+query_params_filter+body_filter+headers_filter.
        If no filter provided, corresponding mocks WITH filters will not be disabled!
        In such case, only ones that have no filter will be disabled.
        """
        tasks = [
            self._disable_old_rest_mocks(
                endpoint=mock.endpoint,
                method=mock.method,
                query_params_filter=mock.query_params_filter,
                body_filter=mock.body_filter,
                headers_filter=mock.headers_filter
            )
            for mock in mocks
        ]
        await asyncio.gather(*tasks)

        tasks = [
            self.repo.add_rest_mock_to_storage(
                config_uuid=config_uuid,
                endpoint=mock.endpoint,
                method=mock.method,
                query_params_filter=json.dumps(mock.query_params_filter, ensure_ascii=False),
                body_filter=json.dumps(mock.body_filter, ensure_ascii=False),
                headers_filter=json.dumps(mock.headers_filter, ensure_ascii=False),
                response_body=json.dumps(mock.response_body, ensure_ascii=False),
                response_headers=json.dumps(mock.response_headers, ensure_ascii=False),
                response_status=mock.response_status,
            )
            for mock in mocks
        ]
        await asyncio.gather(*tasks)

    async def _disable_old_rest_mocks(
        self,
        endpoint: str,
        method: str,
        query_params_filter: dict[str, str] | None,
        body_filter: dict[str, str] | None,
        headers_filter: dict[str, str] | None,
    ):
        params = locals()
        filters = {
            k: v for k, v in params.items()
            if k in ("query_params_filter", "body_filter", "headers_filter") and v
        }
        mocks: list[RestMockFromStorage] = await self.get_rest_mocks(endpoint=endpoint, method=method)
        if filters:
            filtered_mocks = filter(
                lambda x: all(
                    getattr(x, filter_name) == filter_value for filter_name, filter_value in filters.items()
                ), mocks
            )
        else:
            filtered_mocks = filter(
                lambda x: all(
                    getattr(x, filter_name) is None for filter_name in filters
                ), mocks
            )
        mock_ids = [x.id for x in filtered_mocks]
        await self.repo.update_mock(
            MockType.rest,
            mock_ids,
            updated_at=datetime.now(UTC),
            is_deleted=True,
        )

    async def get_rest_mocks(
        self, endpoint: str, method: str
    ) -> list[RestMockFromStorage]:
        try:
            res = await self.repo.get_rest_mocks_from_storage(
                endpoint=endpoint, method=method
            )
        except DatabaseError:
            return []
        return res

    async def delete_rest_mocks(self, endpoint: str, method: str) -> None:
        ids = [x.id for x in await self.get_rest_mocks(endpoint=endpoint, method=method)]
        await self.repo.update_mock(MockType.rest, mock_ids=ids, updated_at=datetime.now(UTC), is_deleted=True)


class GRPCService:
    def __init__(self, mock_repo: MockRepo, log_repo: LogRepo):
        self.mock_repo = mock_repo
        self.log_repo = log_repo

    async def process_grpc(
        self, package: str, service: str, method: str, payload: bytes
    ) -> tuple[bytes, int]:
        storage_mocks = (
            await self.mock_repo.get_grpc_mocks_from_storage(
                package=package,
                service=service,
                method=method,
            )
        )

        # Let's assume that any corresponding DB record does contain a suitable schema:
        request_data, _ = blackboxprotobuf.decode_message(
            payload[5:], storage_mocks[0].request_schema
        )
        for mock in storage_mocks:
            if mock.filter:
                if _compare_request_to_filter(request_data, mock.filter):
                    break
        else:
            try:
                mock = next(x for x in storage_mocks if not x.filter)
            except StopIteration:
                raise MockResponsePreparationError("Unable to find suitable mock for the request")

        await self.log_repo.store_log(
            MockType.grpc,
            mock_id=mock.id,
            request_data=request_data,
            response_data=mock.response_mock,
            response_status=mock.response_status,
        )
        try:
            response_data = blackboxprotobuf.encode_message(
                mock.response_mock, mock.response_schema
            )
        except Exception as err:
            raise MockResponsePreparationError(
                f"Unable to prepare response. "
                f"Probably provided response structure does not suit .proto file structure:\n{err}"
            )
        return (
            (
                (0).to_bytes()
                + len(response_data).to_bytes(4, "big", signed=False)
                + response_data
            ),
            mock.response_status,
        )


class RestService:
    def __init__(self, mock_repo: MockRepo, log_repo: LogRepo):
        self.mock_repo = mock_repo
        self.log_repo = log_repo

    async def process_rest_request(
        self,
        endpoint: str,
        method: str,
        headers: dict,
        body: dict,
        query_params: dict,
    ) -> RestMockedResponse:
        try:
            mocks: list[RestMockFromStorage] = await self.mock_repo.get_rest_mocks_from_storage(endpoint=endpoint, method=method)
        except DatabaseError:
            raise MockResponsePreparationError("Unable to find suitable mock for the request")

        # Let's try to locate any mock WITH filters and also create list of mocks WITHOUT filters:
        mocks_without_filters = []
        for mock in mocks:
            has_filters = False
            for request_part, mock_filter in (
                    (headers, mock.headers_filter),
                    (query_params, mock.query_params_filter),
                    (body, mock.body_filter)
            ):
                if mock_filter:
                    has_filters = True
                    if not _compare_request_to_filter(request_part, mock_filter):
                        # If a filter exists, but does not match, let's stop checking filters:
                        break
            # If some filters exist and all filters pass, it's our candidate,
            # and we just can stop searching, and use "mock" later:
            else:
                 break
            # If no filters found, let's add the mock to the list of mocks without filters:
            if not has_filters:
                mocks_without_filters.append(mock)

        #### Simpler implementation of the mock selection algorithm.
        #### Can be useful if separated rules for different filters need to be implemented.
        # for mock in mocks:
        #     has_filters = False
        #     if mock.headers_filter:
        #         has_filters = True
        #         if not _compare_request_to_filter(headers, mock.headers_filter):
        #             # If a filter exists, but does not match, let's move on to another mock:
        #             continue
        #     if mock.query_params_filter:
        #         has_filters = True
        #         if not _compare_request_to_filter(query_params, mock.query_params_filter):
        #             # If a filter exists, but does not match, let's move on to another mock:
        #             continue
        #     if mock.body_filter:
        #         has_filters = True
        #         if not _compare_request_to_filter(body, mock.body_filter):
        #             # If a filter exists, but does not match, let's move on to another mock:
        #             continue
        #     # If some filters exist and all filters pass, it's our candidate,
        #     # and we just can stop searching, and use "mock" later:
        #     if has_filters:
        #         break
        #     # if no filters found, let's add the mock to the list of mocks without filters:
        #     else:
        #         mocks_without_filter.append(mock)
        #####

        # If no mock with filters found, let's use the first one without them if one exist or give up if none found:
        else:
            mock = next(iter(mocks_without_filters), None)
            if not mock:
                raise MockResponsePreparationError("Unable to find suitable mock for the request")

        # Add mock request to the log:
        await self.log_repo.store_log(
            MockType.rest,
            mock_id=mock.id,
            response_status=mock.response_status,
            request_data={
                "endpoint": endpoint,
                "method": method,
                "headers": headers,
                "query_params": query_params,
                "body": body,
            },
            response_data={
                "headers": mock.response_headers,
                "body": mock.response_body,
            },
        )

        try:
            prepared_body = json.loads(mock.response_body)
        except Exception:   # yeah, too broad, I know, but who cares?
            prepared_body = mock.response_body
        return RestMockedResponse(headers=mock.response_headers, body=prepared_body)


def _compare_request_to_filter(request: dict, mock_filter: dict) -> bool:
    """
    Verifies request against all values in the filter.

    :param request: data as a dictionary.
    :param mock_filter: dictionary which keys are JSON path strings and values are regular expressions.
    """

    for json_path, regexp in mock_filter.items():
        data = jsonpath(request, json_path)
        if not data:
            return False
        # jsonpath returns a list, so we need to check its first item:
        if not re.match(regexp, str(data[0])):
            return False
    return True
