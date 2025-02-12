-- 
-- depends: 20250212_03_XwiLN
CREATE TABLE logs (
    id SERIAL NOT NULL PRIMARY KEY,
    method_id INTEGER,
    mock_id INTEGER,
    request JSONB,
    response JSONB,
    FOREIGN KEY (method_id) REFERENCES methods (id),
    FOREIGN KEY (mock_id) REFERENCES mocks (id)
);
