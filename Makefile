test:
	pytest

format:
	ruff format .

migrate:
	yoyo apply

run:
	python -m grpc_mock