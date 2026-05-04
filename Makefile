-include .env
export


test:
	@pytest

format:
	@ruff format .

postgres-up:
	@docker compose -f docker-compose_postgres.yml up -d db

postgres-migrate:
	@yoyo apply -d $(GRPC_MOCK_DATABASE_URL)

postgres-down:
	@docker compose -f docker-compose_postgres.yml down -t 1

sqlite-down:
	@docker compose -f docker-compose_sqlite.yml down

dev.run:
	@python -m grpc_mock

run:
	@hypercorn grpc_mock.server:app -b $(GRPC_MOCK_HOST):$(GRPC_MOCK_PORT)

run-postgres: postgres-up
	@sleep 3
	-@$(MAKE) postgres-migrate
	-@docker compose -f docker-compose_postgres.yml up --build api
	-@$(MAKE) postgres-down

run-sqlite:
	-@docker compose -f docker-compose_sqlite.yml up --build
	-@$(MAKE) sqlite-down

test-integration-sqlite:
	mkdir -p tests/reports
	@pytest tests/integration/ --db-type=sqlite -v --tb=short --junit-xml=tests/reports/test_sqlite_results.xml --html=tests/reports/test_sqlite_results.html --self-contained-html

test-integration-postgres: postgres-up
	@sleep 5
	mkdir -p tests/reports
	@pytest tests/integration/ --db-type=postgres -v --tb=short --junit-xml=tests/reports/test_postgres_results.xml --html=tests/reports/test_postgres_results.html --self-contained-html
	@$(MAKE) postgres-down

test-integration: test-integration-sqlite test-integration-postgres
	@echo "All integration tests completed. Reports saved to tests/reports/"

