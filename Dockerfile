FROM python:3.12-slim

RUN apt-get update; apt-get install -y --no-install-recommends make; \
	rm -rf /var/lib/apt/lists/*
RUN pip install uv

WORKDIR /app

COPY pyproject.toml /app/
COPY uv.lock /app/

RUN uv export > deps.txt && pip install -r deps.txt

COPY grpc_mock /app/grpc_mock

ENV PYTHONUNBUFFERED=1
ENV GRPC_MOCK_HOST=0.0.0.0
ENV GRPC_MOCK_PORT=3333

ENTRYPOINT ["hypercorn", "grpc_mock.server:app", "-b"]
CMD ["$(GRPC_MOCK_HOST):$(GRPC_MOCK_PORT)"]
