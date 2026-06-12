# Module 10 — Capstone: Bookstore Application

> Goal: build a tiny, end-to-end online bookstore that uses **every**
> previous module so you can see the topics fit together in real code.

## Architecture

```
            Browser / curl
                │  HTTPS (module 06)
                ▼
        Spring Boot REST API
        ┌──────────────────────┐
        │ controllers/         │  (module 05)
        │ services/            │  (modules 07 design patterns)
        │ security/            │  (module 06 JWT, BCrypt)
        │ repositories/        │  (module 04 JDBC/MyBatis)
        └──────────────────────┘
                │
                ▼
            MySQL 8 (modules 01 + 02)
```

Java itself is module 03, tests are module 09, and the bookstore's
in-memory caches are built on the data structures from module 08.

## Features

* **Sign up & log in** — `/auth/register`, `/auth/login`, BCrypt-hashed
  passwords, JWT issued on login.
* **Browse books** — `GET /api/books`, `GET /api/books/{id}`,
  `GET /api/books?category={id}` with pagination.
* **Shopping cart** — kept in-memory keyed by user id (uses the
  hand-rolled `HashMap` from module 08 for fun).
* **Checkout** — runs through a Chain-of-Responsibility validator, a
  Strategy discount, picks a payment gateway via Factory Method, and a
  Facade orchestrates the whole flow.
* **Order history** — `GET /api/orders` (only the caller's own orders).
* **Admin** — `POST /api/admin/books` protected by an `ADMIN` role.

## How to run

```bash
# 1. start MySQL
docker compose -f ../tools/docker-compose.yml up -d
# 2. apply the schema/seed from module 02
mysql -h127.0.0.1 -ulab -plab lab < ../02-sql-fundamentals/schema.sql
mysql -h127.0.0.1 -ulab -plab lab < ../02-sql-fundamentals/seed.sql
# 3. run the app
mvn -pl 10-bookstore-app -am spring-boot:run
```

Then:

```bash
curl http://localhost:8080/api/books
```

## Where each module shows up

| Module                       | Used in the capstone as ...                   |
|------------------------------|-----------------------------------------------|
| 01 ER design                 | The schema you're talking to                  |
| 02 SQL                       | The DDL + ad-hoc reports                      |
| 03 Java core                 | Everything                                    |
| 04 JDBC / MyBatis            | `repositories/` package                       |
| 05 Web / HTTP                | REST controllers, status codes                |
| 06 Security / crypto         | BCrypt passwords, JWT auth, HTTPS             |
| 07 Design patterns           | Checkout pipeline                             |
| 08 Data structures           | In-memory cart                                |
| 09 Testing                   | `src/test/java`                               |
