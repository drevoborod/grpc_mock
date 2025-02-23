FROM python:3.12-slim

RUN apt-get update; apt-get install -y --no-install-recommends make; \
	rm -rf /var/lib/apt/lists/*
RUN pip install uv

WORKDIR /app

COPY pyproject.toml /app/
COPY uv.lock /app/

RUN uv export > deps.txt && pip install -r deps.txt

COPY grpc_mock /app/grpc_mock
COPY Makefile /app/

ENV PYTHONUNBUFFERED=1

ENTRYPOINT []
CMD ["make", "run"]
