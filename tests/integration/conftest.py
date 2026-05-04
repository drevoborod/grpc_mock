import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest


sys.path.insert(0, str(Path(__file__).parent.parent.parent))


BASE_URL = "http://127.0.0.1:3333"
REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def pytest_addoption(parser):
    parser.addoption(
        "--db-type",
        action="store",
        default="both",
        choices=["sqlite", "postgres", "both"],
        help="Database type to run tests against: sqlite, postgres, or both",
    )


def wait_for_service(url: str, timeout: int = 30) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = httpx.get(f"{url}/rest_mocks", params={"endpoint": "/", "method": "GET"}, timeout=2)
            if response.status_code in (200, 400, 404, 500):
                return True
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout):
            time.sleep(0.5)
    return False


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def pytest_collection_modifyitems(config, items):
    db_type = config.getoption("--db-type")
    for item in items:
        if db_type != "postgres" and "db_type" not in item.fixturenames:
            if "test_mock_adding_grpc" in str(item.fspath):
                item.add_marker(pytest.mark.skip(reason="Test requires PostgreSQL"))


@pytest.fixture(scope="session")
def db_type(request):
    return request.config.getoption("--db-type")


@pytest.fixture(scope="session")
def env_config(tmp_path_factory, db_type):
    env_file = tmp_path_factory.mktemp("env") / ".env"

    if db_type == "postgres":
        compose_file = Path(__file__).parent.parent.parent / "docker-compose_postgres.yml"
        subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "up", "-d", "db"],
            check=True,
            capture_output=True,
        )
        time.sleep(5)

        env_content = """\
GRPC_MOCK_DB_TYPE=postgres
GRPC_MOCK_DATABASE_NAME=grpc_mock
GRPC_MOCK_DATABASE_USER=grpc_mock
GRPC_MOCK_DATABASE_ADDRESS=localhost
GRPC_MOCK_DATABASE_PORT=14432
GRPC_MOCK_DATABASE_PASSWORD=8_djss6hdsSYbdt_63_sdasKR
GRPC_MOCK_DATABASE_URL=postgresql://grpc_mock:8_djss6hdsSYbdt_63_sdasKR@localhost:14432/grpc_mock
GRPC_MOCK_HOST=127.0.0.1
GRPC_MOCK_PORT=3333
"""
    else:
        db_dir = tmp_path_factory.mktemp("db")
        db_file = db_dir / "test.db"
        env_content = f"""\
GRPC_MOCK_DB_TYPE=sqlite
GRPC_MOCK_SQLITE_DB_FILE_NAME={db_file}
GRPC_MOCK_HOST=127.0.0.1
GRPC_MOCK_PORT=3333
"""

    env_file.write_text(env_content)
    return env_file


@pytest.fixture(scope="session")
def grpc_mock_server(env_config, db_type):
    port = 3333
    if is_port_in_use(port):
        raise RuntimeError(f"Port {port} is already in use. Please stop any running instance.")

    server_env = os.environ.copy()
    server_env["GRPC_MOCK_HOST"] = "127.0.0.1"
    server_env["GRPC_MOCK_PORT"] = str(port)

    dotenv_content = env_config.read_text()
    for line in dotenv_content.splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            server_env[key] = value

    process = subprocess.Popen(
        ["python", "-m", "grpc_mock"],
        env=server_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if not wait_for_service(BASE_URL):
        process.terminate()
        process.wait()
        stdout, stderr = process.communicate()
        raise RuntimeError(
            f"Service failed to start.\nSTDOUT: {stdout.decode()}\nSTDERR: {stderr.decode()}"
        )

    yield port

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()

    if db_type == "postgres":
        compose_file = Path(__file__).parent.parent.parent / "docker-compose_postgres.yml"
        subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "down", "-t", "1"],
            check=False,
            capture_output=True,
        )


@pytest.fixture
def http_client(grpc_mock_server):
    with httpx.Client(base_url=BASE_URL, timeout=10) as client:
        yield client


@pytest.fixture
def config_uuid_counter():
    counter = [0]

    def next_uuid():
        counter[0] += 1
        return f"test-config-{counter[0]}"

    return next_uuid


def pytest_runtest_teardown(item, nextitem):
    pass
