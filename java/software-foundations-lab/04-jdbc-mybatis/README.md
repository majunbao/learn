# Module 04 — JDBC & MyBatis

> Goal: connect Java code to MySQL — first the verbose, hand-written way
> (JDBC), then the idiomatic mapper-based way (MyBatis).

Run `tools/docker-compose.yml` and load
`02-sql-fundamentals/schema.sql` + `seed.sql` first.

## Sub-packages

| Package            | What it teaches                                              |
|--------------------|--------------------------------------------------------------|
| `jdbc.raw`         | `DriverManager`, `Connection`, `PreparedStatement`, `ResultSet`, transactions, connection pooling with HikariCP. |
| `mybatis.demo`     | `SqlSessionFactory`, mapper interface, XML mapper, parameter / result mapping. |

## What you'll be able to do

* Open a connection, run a parameterised query, map a row to a POJO.
* Explain why `Statement` is dangerous (SQL injection) and `PreparedStatement` is not.
* Roll your own DAO; then refactor it to a MyBatis mapper and notice how
  many lines vanish.
* Configure a pool and explain why "one connection per request" is wrong.

## Exercises

1. Add a `findBooksByCategoryId` method on a JDBC DAO.
2. Re-implement the same method as a MyBatis mapper.
3. Force a SQL injection on a deliberately-broken `Statement` version, then
   fix it.
