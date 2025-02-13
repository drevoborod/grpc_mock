-- 
-- depends: 20250213_01_pIhgX
CREATE TABLE logs (
    id SERIAL NOT NULL PRIMARY KEY,
    mock_id INTEGER NOT NULL,
    request JSONB NOT NULL,
    response JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT (now() at time zone 'utc'),
    FOREIGN KEY(mock_id) REFERENCES mocks (id)
);
