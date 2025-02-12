-- 
-- depends: 20250212_01_8XSAK
CREATE TABLE methods (
    id SERIAL NOT NULL PRIMARY KEY,
    service_id INTEGER,
    method_name VARCHAR(255),
    request_schema JSONB,
    response_schema JSONB,
    FOREIGN KEY(service_id) REFERENCES services (id)
);
