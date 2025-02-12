-- 
-- depends: 
CREATE TABLE services (
  id SERIAL NOT NULL PRIMARY KEY,
  service_name VARCHAR(255),
  package_name VARCHAR(255)
);
