import h2.exceptions
import priority
from hypercorn.protocol import H2Protocol
from hypercorn.protocol.events import Trailers
from hypercorn.protocol.h2 import BufferCompleteError
from hypercorn.protocol.http_stream import HTTPStream
from hypercorn.utils import build_and_validate_headers
from starlette.responses import Response
from starlette.types import Receive, Scope, Send


class GRPCResponse(Response):
    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.raw_headers,
                "trailers": True,
            }
        )
        await send({"type": "http.response.body", "body": self.body})
        await self._prepare_custom_trailers(
            {"type": "http.response.trailers", "headers": self.raw_headers},
            send.__self__,
        )

        if self.background is not None:
            await self.background()

    async def _prepare_custom_trailers(
        self, message: dict, http_stream_instance: HTTPStream
    ):
        # Had to copy-paste a part of hypercorn because at the time it's the only way
        # to make it work the way some GRPC clients expect.
        for name, value in http_stream_instance.scope["headers"]:
            if name == b"te" and value == b"trailers":
                headers = build_and_validate_headers(message["headers"])
                protocol_instance = http_stream_instance.send.__self__
                await self._send_custom_trailers(
                    Trailers(
                        stream_id=http_stream_instance.stream_id,
                        headers=headers,
                    ),
                    protocol_instance,
                )
                break

        if not message.get("more_trailers", False):
            await http_stream_instance._send_closed()

    async def _send_custom_trailers(
        self, event: Trailers, protocol_instance: H2Protocol
    ) -> None:
        try:
            protocol_instance.priority.unblock(event.stream_id)
            await protocol_instance.has_data.set()
            await protocol_instance.stream_buffers[event.stream_id].drain()
            # huge gratitude to the author of this: https://github.com/pgjones/hypercorn/pull/255
            protocol_instance.connection.send_headers(
                event.stream_id, event.headers, end_stream=True
            )
            await protocol_instance._flush()
        except (
            BufferCompleteError,
            KeyError,
            priority.MissingStreamError,
            h2.exceptions.ProtocolError,
        ):
            return
