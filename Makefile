-include .env
export

test:
	@pytest

format:
	@ruff format .

db.run:
	@docker compose up -d db

db.migrate:
	@yoyo apply -d $(GRPC_MOCK_DATABASE_URL)

db.clean:
	@docker compose down -t 1

dev.run:
	@python -m grpc_mock

run:
	@hypercorn grpc_mock.service:app -b $(GRPC_MOCK_HOST):$(GRPC_MOCK_PORT)
