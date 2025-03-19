-- 
-- depends: 
CREATE TABLE mocks (
    id SERIAL NOT NULL PRIMARY KEY,
    config_uuid VARCHAR(255) NOT NULL,
    package_name VARCHAR(255) NOT NULL,
    service_name VARCHAR(255) NOT NULL,
    method_name VARCHAR(255) NOT NULL,
    request_schema JSONB NOT NULL,
    response_schema JSONB NOT NULL,
    response_mock JSONB NOT NULL,
    response_status SMALLINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted BOOLEAN
);
