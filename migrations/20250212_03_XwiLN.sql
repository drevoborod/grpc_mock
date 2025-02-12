-- 
-- depends: 20250212_02_bx534
CREATE TABLE mocks (
    id SERIAL NOT NULL PRIMARY KEY,
    method_id INTEGER,
    body JSONB,
    FOREIGN KEY (method_id) REFERENCES methods (id)
);
