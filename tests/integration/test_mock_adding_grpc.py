import os

import psycopg2
import pytest
from dotenv import load_dotenv


load_dotenv()

@pytest.fixture()
def db_connection():
    conn = psycopg2.connect(os.getenv("GRPC_MOCK_DATABASE_URL"))
    # conn.autocommit=False
    yield conn
    conn.rollback()
    # conn.commit()
    conn.close()


@pytest.fixture()
def fill_db(db_connection):
    cur = db_connection.cursor()
    cur.execute(
        "insert into mocks "
            "(config_uuid, package_name, service_name, method_name, request_schema, response_schema, "
            "response_mock, response_status, is_deleted) "
        "values ('abcd', 'home', 'room', 'table', '{}', '{}', '{}', 7, false)"
    )
    cur.close()


def test_1(db_connection, fill_db):
    cur = db_connection.cursor()
    cur.execute("select * from mocks")
    assert cur.fetchall()
    cur.execute("select * from mocks")
    assert cur.fetchall()


def test_2(db_connection):
    cur = db_connection.cursor()
    cur.execute("select * from mocks")
    assert not cur.fetchall()

def test_3(db_connection):
    cur = db_connection.cursor()
    cur.execute("SHOW default_transaction_isolation")
    res = cur.fetchall()
    assert res
