import asyncio
from datetime import datetime, UTC
from uuid import uuid4

from grpclib.client import Channel

from dev.generated.library import BookAddRequest, BooksStub, BookMetadata, Author, BookMetadataPublisher, BookAddRequestUser, BookAddRequestUserSex


async def send(service, request):
    response = await service.book_add_endpoint(
        book_add_request=request
    )
    print(response)


async def main():
    channel = Channel(host="127.0.0.1", port=3333)
    service = BooksStub(channel)

    await send(
        service,
        BookAddRequest(
            book_uuid=str(uuid4()),
            user_id=123,
            timestamp=datetime.now(UTC).isoformat(),
            metadata=BookMetadata(
                name="Война и мир",
                year=1884,
                authors=[
                    Author(last_name="Толстой", first_name="Лео"),
                    Author(last_name="Работник", first_name="Литературный", second_name="1"),
                ],
                publisher=BookMetadataPublisher(name="Рога и копыта")
            ),
            user=BookAddRequestUser(
                last_name="Васечкин",
                first_name="Петя",
                sex=BookAddRequestUserSex(BookAddRequestUserSex.FEMALE),
            )
        )
    )

    await send(
        service,
        BookAddRequest(
            book_uuid=str(uuid4()),
            user_id=123,
            timestamp=datetime.now(UTC).isoformat(),
            metadata=BookMetadata(
                name="Война и мир",
                year=1884,
                authors=[
                    Author(last_name="Толстой", first_name="Лео"),
                    Author(last_name="Работник", first_name="Литературный", second_name="1"),
                ],
                publisher=BookMetadataPublisher(name="Рога и копыта")
            ),
            user=BookAddRequestUser(
                last_name="John the third",
                first_name="Dobby",
                sex=BookAddRequestUserSex(BookAddRequestUserSex.FEMALE),
            )
        )
    )

    channel.close()


if __name__ == "__main__":
    asyncio.run(main())
