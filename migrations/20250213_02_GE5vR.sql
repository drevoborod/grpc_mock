-- 
-- depends: 20250213_01_pIhgX
CREATE TABLE logs (
    id SERIAL NOT NULL PRIMARY KEY,
    mock_id INTEGER NOT NULL,
    request JSONB NOT NULL,
    response JSONB NOT NULL,
    response_status SMALLINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY(mock_id) REFERENCES mocks (id)
);
