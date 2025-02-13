test:
	@pytest

format:
	@ruff format .

db.run:
	@docker compose up -d db

migrate:
	@yoyo apply

clean:
	@docker compose down -t 1

run:
	@python -m grpc_mock