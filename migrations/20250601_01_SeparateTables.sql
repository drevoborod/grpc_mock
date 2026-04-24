-- 
CREATE TABLE grpc_mocks (
    id SERIAL NOT NULL PRIMARY KEY,
    config_uuid VARCHAR(255) NOT NULL,
    package_name VARCHAR(255) NOT NULL,
    service_name VARCHAR(255) NOT NULL,
    method_name VARCHAR(255) NOT NULL,
    request_schema JSONB NOT NULL,
    response_schema JSONB NOT NULL,
    response_mock JSONB NOT NULL,
    response_status SMALLINT NOT NULL,
    filter JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE rest_mocks (
    id SERIAL NOT NULL PRIMARY KEY,
    config_uuid VARCHAR(255) NOT NULL,
    endpoint VARCHAR(1024) NOT NULL,
    method VARCHAR(10) NOT NULL,
    query_params_filter JSONB,
    body_filter JSONB,
    headers_filter JSONB,
    response_body TEXT,
    response_headers JSONB,
    response_status SMALLINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE grpc_logs (
    id SERIAL NOT NULL PRIMARY KEY,
    mock_id INTEGER NOT NULL,
    request JSONB NOT NULL,
    response JSONB NOT NULL,
    response_status SMALLINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY(mock_id) REFERENCES grpc_mocks (id)
);

CREATE TABLE rest_logs (
    id SERIAL NOT NULL PRIMARY KEY,
    mock_id INTEGER NOT NULL,
    request JSONB NOT NULL,
    response JSONB NOT NULL,
    response_status SMALLINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY(mock_id) REFERENCES rest_mocks (id)
);
