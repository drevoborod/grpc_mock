-- 
-- depends: 20250213_02_GE5vR
truncate table logs;
delete from mocks where filter is not null;
alter table mocks drop filter;

