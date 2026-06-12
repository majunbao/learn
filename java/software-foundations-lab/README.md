# Software Foundations Lab

A hands-on, single-repository project for learning the fundamentals of software
engineering with **Java** as the implementation language. Every module is built
around a small, runnable example and a `README.md` that explains the theory.

The capstone (`10-bookstore-app`) is a tiny online bookstore that uses
every previous module so you can see the topics work together in a real app.

---

## Learning Roadmap

| Directory                  | What you learn                                                              |
|----------------------------|-----------------------------------------------------------------------------|
| `01-database`              | 18-chapter database textbook: models, algebra, SQL, normalisation, transactions, locking, distributed DB |
| `03-java-core`             | Java syntax, OOP, collections, generics, IO, concurrency, streams, JVM     |
| `04-jdbc-mybatis`          | Connecting Java to MySQL with raw JDBC and with MyBatis                    |
| `05-web-and-http`          | HTTP, TCP/UDP sockets, REST APIs with Spring MVC, WebSocket                |
| `06-security-crypto`       | Hashing, AES, RSA, digital signatures, TLS/HTTPS, JWT, common attacks      |
| `07-design-patterns`       | Classic GoF patterns illustrated with bookstore use-cases                  |
| `08-data-structures-algo`  | Linked list, stack, queue, hash map, tree, graph, sorting, searching, Big-O|
| `09-testing`               | JUnit 5, Mockito, integration tests                                        |
| `10-bookstore-app`         | Capstone: a Spring Boot bookstore that ties every module together         |

> Folder `01-database` is **docs only** — intentionally NOT a Maven module.
> The other 8 folders are Maven modules registered in the root `pom.xml`.

---

## Suggested Study Order

1. **Database foundations** — work through `01-database` chapter by chapter; this is the longest single module and underpins everything that follows.
2. **Speak the language** — `03-java-core` until the syntax feels boring.
3. **Connect the dots** — `04-jdbc-mybatis` and `05-web-and-http` (DB + network).
4. **Stay safe** — `06-security-crypto` covers everything security-related.
5. **Write code that lasts** — `07-design-patterns`, `08-data-structures-algo`, `09-testing`.
6. **Ship something** — assemble the capstone in `10-bookstore-app`.

Each module has its own `README.md` with concept notes, exercises and a
"further reading" section.

---

## Prerequisites

* **JDK 17** (LTS)
* **Maven 3.9+**
* **Docker** + **Docker Compose** (for MySQL in module 02 and the capstone)
* Any IDE that understands Maven (IntelliJ IDEA recommended)

---

## How to Build

```bash
# from the project root
mvn -q -DskipTests verify
```

Each module can be built or run on its own, e.g.:

```bash
mvn -pl 03-java-core -am compile
```

## How to Start MySQL Locally

```bash
docker compose -f tools/docker-compose.yml up -d
# MySQL will be available at localhost:3306
# user: lab     password: lab     database: lab
```

---

## Repository Layout

```
software-foundations-lab/
├── README.md
├── pom.xml                          # parent POM (multi-module Maven)
├── tools/
│   └── docker-compose.yml           # local MySQL for SQL & capstone modules
└── module-XX-.../                   # one folder per topic
    ├── README.md                    # theory + exercises
    └── ...                          # code / sql / docs
```

Happy learning!
