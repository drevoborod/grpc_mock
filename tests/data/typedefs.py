LIBRARY_REQUEST_TYPEDEF = {
    "1": {"name": "book_uuid", "type": "string"},
    "2": {"name": "user_id", "type": "int"},
    "3": {"name": "timestamp", "type": "string"},
    "4": {
        "message_typedef": {
            "1": {"name": "name", "type": "string"},
            "2": {"name": "year", "type": "int"},
            "3": {
                "message_typedef": {
                    "1": {"name": "last_name", "type": "string"},
                    "2": {"name": "first_name", "type": "string"},
                    "3": {"name": "second_name", "type": "string"},
                },
                "name": "authors",
                "seen_repeated": True,
                "type": "message",
            },
            "4": {
                "message_typedef": {"1": {"name": "name", "type": "string"}},
                "name": "publisher",
                "type": "message",
            },
        },
        "name": "metadata",
        "type": "message",
    },
    "5": {
        "message_typedef": {
            "1": {"name": "last_name", "type": "string"},
            "2": {"name": "first_name", "type": "string"},
            "3": {"name": "second_name", "type": "string"},
            "4": {"name": "sex", "type": "uint"},
        },
        "name": "user",
        "type": "message",
    },
}
