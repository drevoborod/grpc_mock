import asyncio
from datetime import datetime, UTC
from uuid import uuid4

from grpclib.client import Channel

from dev.generated.library import BookAddRequest, BooksStub


async def main():
    channel = Channel(host="127.0.0.1", port=3333)
    service = BooksStub(channel)
    response = await service.book_add_endpoint(
        book_add_request=BookAddRequest(
            book_uuid=str(uuid4()),
            user_id=123,
            timestamp=datetime.now(UTC).isoformat()
        )
    )
    print(response)
    channel.close()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
