# 06 — SQL Language

> Syllabus reference: P38–P56
>
> A practical reference to the parts of SQL that the exam (and real
> work) keeps asking about: DDL, DML, queries with joins / grouping /
> sub-queries, and DCL. Companion runnable files live in
> `exercises/`.

---

## 1. The Four Sub-Languages of SQL

| Sub-language | Stands for                  | Statements                              |
|--------------|-----------------------------|-----------------------------------------|
| **DDL**      | Data Definition Language    | `CREATE`, `ALTER`, `DROP`, `TRUNCATE`   |
| **DML**      | Data Manipulation Language  | `INSERT`, `UPDATE`, `DELETE`, `MERGE`   |
| **DQL**      | Data Query Language         | `SELECT` (often grouped under DML)      |
| **DCL**      | Data Control Language       | `GRANT`, `REVOKE`                       |
| **TCL**      | Transaction Control         | `COMMIT`, `ROLLBACK`, `SAVEPOINT`       |

> Exam tip: `GRANT` and `REVOKE` are **DCL**, not DML. `COMMIT` is
> **TCL**, not DML. A perennial multiple-choice trap.

---

## 2. DDL — Defining Things

### 2.1 Tables
```sql
CREATE TABLE student (
    sid     BIGINT      PRIMARY KEY,
    sname   VARCHAR(50) NOT NULL,
    dept    VARCHAR(20) DEFAULT 'CS',
    age     INT         CHECK (age BETWEEN 0 AND 150),
    email   VARCHAR(80) UNIQUE
);
```

### 2.2 Foreign keys
```sql
CREATE TABLE sc (
    sid   BIGINT,
    cid   BIGINT,
    grade DECIMAL(5,2),
    PRIMARY KEY (sid, cid),
    FOREIGN KEY (sid) REFERENCES student(sid)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (cid) REFERENCES course(cid)
);
```
Reference actions: `CASCADE`, `RESTRICT` / `NO ACTION`, `SET NULL`,
`SET DEFAULT`.

### 2.3 Altering
```sql
ALTER TABLE student ADD    COLUMN gender CHAR(1);
ALTER TABLE student DROP   COLUMN email;
ALTER TABLE student MODIFY COLUMN sname VARCHAR(80);    -- MySQL
ALTER TABLE student ALTER  COLUMN sname TYPE TEXT;      -- PostgreSQL
```

### 2.4 Dropping
```sql
DROP TABLE   student;
TRUNCATE TABLE sc;          -- empties the table, can't be rolled back in MySQL
```

### 2.5 Five Kinds of Integrity Constraints

| Kind             | Declared with        | Enforces                                |
|------------------|----------------------|-----------------------------------------|
| Entity           | `PRIMARY KEY`        | PK is non-NULL and unique               |
| Referential      | `FOREIGN KEY`        | FK matches a PK (or is NULL)            |
| Domain           | `CHECK`, type, `DEFAULT` | Value-level rules                   |
| User-defined     | `CHECK`, triggers    | Arbitrary business rules                |
| Uniqueness       | `UNIQUE`             | Column(s) unique across rows            |

---

## 3. DML — Modifying Rows

```sql
INSERT INTO student (sid, sname, dept) VALUES (1, 'Alice', 'CS');

INSERT INTO student (sid, sname)
SELECT sid, sname FROM legacy_student;        -- INSERT … SELECT

UPDATE student SET dept = 'IT' WHERE dept = 'CS';

DELETE FROM student WHERE age IS NULL;

-- MERGE (UPSERT) — vendor-specific syntax
INSERT INTO student (sid, sname)
VALUES (1, 'Alice')
ON DUPLICATE KEY UPDATE sname = VALUES(sname);   -- MySQL
```

---

## 4. SELECT — The Big One

### 4.1 Logical evaluation order
SQL is written `SELECT ... FROM ... WHERE ...` but logically it
executes in this order:

```
1. FROM            (and JOIN)
2. WHERE
3. GROUP BY
4. HAVING
5. SELECT          (compute the projection, including aggregates)
6. DISTINCT
7. ORDER BY
8. LIMIT / OFFSET
```

Knowing this answers a flood of exam questions, e.g. *"why can't I
reference a `SELECT` alias in `WHERE`?"* — because `WHERE` runs first.

### 4.2 WHERE — predicates

| Operator              | Example                                  |
|-----------------------|------------------------------------------|
| `=  <>  !=  <  <=  >  >=` | `age > 18`                            |
| `BETWEEN a AND b`     | `age BETWEEN 18 AND 25`                  |
| `IN (...)`            | `dept IN ('CS','EE')`                    |
| `LIKE`                | `name LIKE 'A%'` (`_` = 1 char, `%` = any) |
| `IS NULL` / `IS NOT NULL` | `email IS NULL`                      |
| `EXISTS (subquery)`   | semi-join                                |
| `ALL` / `ANY` / `SOME`| `salary > ALL (SELECT salary FROM ...)`  |

> `NULL` quirks: `NULL = NULL` is `UNKNOWN`, not `TRUE`. Always use
> `IS NULL`. Any arithmetic with `NULL` is `NULL`. Aggregates ignore
> `NULL` *except* `COUNT(*)`.

### 4.3 JOINs

```sql
SELECT s.sname, c.cname
FROM   student s
JOIN   sc       ON s.sid = sc.sid          -- INNER
LEFT   JOIN course c ON sc.cid = c.cid;    -- LEFT
```

| SQL syntax              | Relational algebra |
|-------------------------|--------------------|
| `INNER JOIN ... ON`     | `R ⋈_θ S`          |
| `LEFT JOIN`             | `R ⟕ S`            |
| `RIGHT JOIN`            | `R ⟖ S`            |
| `FULL OUTER JOIN`       | `R ⟗ S`            |
| `CROSS JOIN` / `FROM A, B` | `R × S`         |
| `NATURAL JOIN`          | `R ⋈ S`            |

### 4.4 GROUP BY and aggregates

Aggregate functions: `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`,
`STDDEV`, `VARIANCE`, and `COUNT(DISTINCT col)`.

```sql
SELECT dept, COUNT(*) AS num_students, AVG(age) AS avg_age
FROM   student
GROUP  BY dept
HAVING COUNT(*) > 10
ORDER  BY num_students DESC;
```

* `WHERE` filters **rows** *before* grouping.
* `HAVING` filters **groups** *after* grouping.
* Every non-aggregated column in `SELECT` must appear in `GROUP BY`
  (strict-mode SQL).

### 4.5 Sub-queries

```sql
-- scalar sub-query
SELECT sname FROM student WHERE age = (SELECT MAX(age) FROM student);

-- list (IN) sub-query
SELECT sname FROM student
WHERE  sid IN (SELECT sid FROM sc WHERE grade >= 90);

-- correlated sub-query (refers to outer table)
SELECT s.sname
FROM   student s
WHERE  EXISTS (SELECT 1 FROM sc WHERE sc.sid = s.sid AND grade >= 90);

-- inline view (sub-query in FROM)
SELECT t.dept, t.avg_age
FROM   (SELECT dept, AVG(age) AS avg_age FROM student GROUP BY dept) t
WHERE  t.avg_age > 20;

-- CTE (Common Table Expression)
WITH high_scorers AS (
    SELECT sid FROM sc WHERE grade >= 90
)
SELECT s.sname
FROM   student s
JOIN   high_scorers h ON s.sid = h.sid;
```

### 4.6 Set operators

```sql
SELECT sid FROM sc WHERE cid = 1
UNION           -- duplicates removed
SELECT sid FROM sc WHERE cid = 2;

SELECT sid FROM sc WHERE cid = 1
INTERSECT       -- in MySQL: use INNER JOIN; PG / Oracle support it
SELECT sid FROM sc WHERE cid = 2;

SELECT sid FROM student
EXCEPT          -- a.k.a. MINUS in Oracle
SELECT sid FROM sc;
```

### 4.7 ORDER BY / LIMIT
```sql
SELECT * FROM student
ORDER BY age DESC, sname ASC
LIMIT 10 OFFSET 20;     -- MySQL / PG / SQLite
-- Oracle 12c+: FETCH FIRST 10 ROWS ONLY
-- SQL Server:  TOP 10 / OFFSET … FETCH NEXT …
```

---

## 5. DCL — Data Control Language (Privileges)

DCL controls **who can do what** on which database objects. The exam
loves DCL — `GRANT` / `REVOKE` are simple statements with many subtle
options.

### 5.1 The privilege model

A SQL privilege is a triple:

```
(privilege  ON  object  TO  grantee)
```

| Component   | Examples                                         |
|-------------|--------------------------------------------------|
| Privilege   | `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `EXECUTE`, `CREATE`, `DROP`, `ALL PRIVILEGES` |
| Object      | Table, view, column, stored procedure, schema, database |
| Grantee     | A user, a role, or `PUBLIC` (everyone)           |

### 5.2 Eight common privileges

| Privilege    | Allows the grantee to…                         |
|--------------|------------------------------------------------|
| `SELECT`     | Read rows from a table or view                 |
| `INSERT`     | Add new rows                                   |
| `UPDATE`     | Modify existing rows (column-level possible)   |
| `DELETE`     | Remove rows                                    |
| `REFERENCES` | Create a foreign key referencing the object    |
| `EXECUTE`    | Call a stored procedure or function            |
| `USAGE`      | Use a sequence / domain / type                 |
| `ALL PRIVILEGES` | All of the above, on the named object      |

### 5.3 GRANT — basic syntax

```sql
GRANT  privilege_list
ON     object
TO     grantee_list
[WITH GRANT OPTION];
```

Examples:

```sql
-- Single privilege, single user
GRANT SELECT ON student TO 'app_reader'@'%';

-- Multiple privileges, multiple users
GRANT SELECT, INSERT, UPDATE
ON student
TO 'alice'@'%', 'bob'@'%';

-- All privileges on every table in a database
GRANT ALL PRIVILEGES ON dbname.* TO 'admin'@'%';

-- Grant to PUBLIC (everyone)
GRANT SELECT ON course TO PUBLIC;
```

### 5.4 Column-level privileges

`SELECT` / `INSERT` / `UPDATE` / `REFERENCES` can be limited to
**specific columns**:

```sql
-- Reader can only see name and dept; not age or email
GRANT SELECT (sname, dept) ON student TO 'public_reader'@'%';

-- HR can update salary but nothing else
GRANT UPDATE (salary) ON employee TO 'hr_user'@'%';
```

This is how databases enforce **column-level access control** without
using views.

### 5.5 WITH GRANT OPTION — delegation

`WITH GRANT OPTION` allows the grantee to **re-grant** the privilege
to others.

```sql
GRANT SELECT ON student TO 'alice'@'%' WITH GRANT OPTION;

-- Alice can now do:
GRANT SELECT ON student TO 'bob'@'%';
```

> Exam trap: **without** `WITH GRANT OPTION`, the grantee can use the
> privilege but cannot pass it on. Forgetting this is a classic
> multiple-choice mistake.

### 5.6 REVOKE — taking privileges back

```sql
REVOKE  privilege_list
ON     object
FROM   grantee_list
[CASCADE | RESTRICT];
```

Examples:

```sql
REVOKE INSERT ON student FROM 'app_user'@'%';

REVOKE ALL PRIVILEGES ON dbname.* FROM 'old_admin'@'%';

REVOKE SELECT ON student FROM 'alice'@'%' CASCADE;
```

### 5.7 CASCADE vs RESTRICT on REVOKE

When the user being revoked has **re-granted** the privilege via
`WITH GRANT OPTION`, what happens to those downstream grants?

| Option       | Behaviour                                                       |
|--------------|-----------------------------------------------------------------|
| `CASCADE`    | Revoke the privilege from the user **and** from everyone they granted it to (recursively). |
| `RESTRICT`   | Refuse to revoke if downstream grants exist. Default in many engines. |

```sql
-- DBA → Alice (with grant option) → Bob → Carol
REVOKE SELECT ON student FROM 'alice'@'%' CASCADE;
-- Result: Alice, Bob, and Carol all lose SELECT.

REVOKE SELECT ON student FROM 'alice'@'%' RESTRICT;
-- Result: error, because Alice has granted to Bob.
```

### 5.8 Roles (角色) — grouping privileges

Real systems have hundreds of users; granting privileges one at a
time does not scale. **Roles** group privileges and can be assigned
to many users.

```sql
-- 1. Create a role
CREATE ROLE app_reader;

-- 2. Grant privileges to the role
GRANT SELECT ON student TO app_reader;
GRANT SELECT ON course  TO app_reader;
GRANT SELECT ON sc      TO app_reader;

-- 3. Grant the role to users
GRANT app_reader TO 'alice'@'%', 'bob'@'%';

-- 4. (MySQL) the user must activate the role
SET DEFAULT ROLE app_reader TO 'alice'@'%';

-- 5. Revoke a role
REVOKE app_reader FROM 'bob'@'%';

-- 6. Drop a role (revokes from all members)
DROP ROLE app_reader;
```

### 5.9 The four standard access-control models

| Model | Chinese | How it decides |
|-------|---------|----------------|
| **DAC** — Discretionary Access Control | 自主访问控制 | The object owner grants/revokes (`GRANT`/`REVOKE`) |
| **MAC** — Mandatory Access Control     | 强制访问控制 | The system enforces labels (e.g. SECRET, TOP SECRET) |
| **RBAC** — Role-Based Access Control   | 基于角色的访问控制 | Privileges → roles → users |
| **ABAC** — Attribute-Based Access Control | 基于属性的访问控制 | Decision based on attributes (department, time, IP) |

> Exam tip: standard SQL `GRANT`/`REVOKE` implements **DAC**.
> Adding `CREATE ROLE` makes it **RBAC**.

### 5.10 Object owner privileges

| Action            | Permitted to            |
|-------------------|-------------------------|
| `CREATE TABLE`    | Anyone with `CREATE` on the schema |
| Modify the table  | The owner, or anyone with `ALL PRIVILEGES` |
| Drop the table    | The owner, or a privileged admin |
| Grant on the table | The owner, or anyone with the privilege `WITH GRANT OPTION` |

The owner of an object **cannot** be removed from it via REVOKE — the
owner's rights are intrinsic until the object is dropped or owner
changed (e.g. PostgreSQL `ALTER TABLE … OWNER TO …`).

### 5.11 PUBLIC and special grantees

| Grantee   | Meaning                                            |
|-----------|----------------------------------------------------|
| A user    | Specific account                                   |
| A role    | Set of privileges, given to many users             |
| `PUBLIC`  | Every existing and future user                     |
| `CURRENT_USER` | The session's current authentication identity |

```sql
-- Make a course catalogue readable to everyone
GRANT SELECT ON course TO PUBLIC;
```

### 5.12 Inspecting privileges

```sql
-- MySQL: list all grants on a user
SHOW GRANTS FOR 'alice'@'%';

-- MySQL: privileges on a table
SELECT * FROM information_schema.table_privileges
WHERE  table_schema = 'dbname' AND table_name = 'student';

-- PostgreSQL: privileges on a table
SELECT grantee, privilege_type
FROM   information_schema.role_table_grants
WHERE  table_name = 'student';
```

### 5.13 Worked example — building a tiered access model

A small e-shop wants three roles: `app_reader` (read-only API),
`app_writer` (can write to orders), `dba` (full control).

```sql
-- Roles
CREATE ROLE app_reader;
CREATE ROLE app_writer;
CREATE ROLE dba;

-- Privileges per role
GRANT SELECT                       ON ALL TABLES IN SCHEMA shop TO app_reader;
GRANT SELECT, INSERT, UPDATE       ON shop.orders                TO app_writer;
GRANT app_reader                   TO app_writer;             -- writers can read too
GRANT ALL PRIVILEGES ON shop.*     TO dba WITH GRANT OPTION;

-- Users
CREATE USER 'reporting_bot'@'%' IDENTIFIED BY '...';
CREATE USER 'order_service'@'%' IDENTIFIED BY '...';
CREATE USER 'mary_admin'@'%'    IDENTIFIED BY '...';

-- Assign roles
GRANT app_reader TO 'reporting_bot'@'%';
GRANT app_writer TO 'order_service'@'%';
GRANT dba        TO 'mary_admin'@'%';
```

### 5.14 Common pitfalls (exam favourites)

| Pitfall | Explanation |
|---------|-------------|
| Forgetting `WITH GRANT OPTION` | Grantee then cannot re-grant — silent failure |
| `REVOKE` without `CASCADE` | Refused if downstream grants exist (RESTRICT default) |
| Granting on `database.*` vs `database.table` | `*` covers existing **and future** tables (MySQL) |
| Granting to `'user'@'%'` vs `'user'@'localhost'` | MySQL treats them as different accounts |
| Forgetting `FLUSH PRIVILEGES` after manual `mysql.user` edits | Changes won't take effect until the cache is reloaded |

---

## 6. NULL Behaviour — Memorise These Rules

| Expression                  | Result        |
|-----------------------------|---------------|
| `x = NULL`                  | `UNKNOWN`     |
| `x IS NULL`                 | `TRUE/FALSE`  |
| `NULL AND TRUE`             | `UNKNOWN`     |
| `NULL AND FALSE`            | `FALSE`       |
| `NULL OR TRUE`              | `TRUE`        |
| `NULL OR FALSE`             | `UNKNOWN`     |
| `COUNT(*)`                  | counts NULLs  |
| `COUNT(col)`                | ignores NULLs |
| `SUM` / `AVG` / `MIN` / `MAX` | ignores NULLs |
| `GROUP BY col`              | NULLs are grouped together |

---

## 7. Exam-Style Questions

**Q1.** Which of the following is **DCL**?
A. `UPDATE`  B. `GRANT`  C. `CREATE`  D. `COMMIT`
> Answer: B.

**Q2.** Which clause is evaluated last?
A. `WHERE`  B. `GROUP BY`  C. `ORDER BY`  D. `SELECT`
> Answer: C. (Among the four; `LIMIT` is even later.)

**Q3.** Result of `SELECT COUNT(*) FROM t WHERE col = NULL;` when t has
many rows?
> 0 — `col = NULL` is `UNKNOWN`, no rows match. Should use `col IS NULL`.

**Q4.** Which of the following adds a unique constraint to an existing
table?
> `ALTER TABLE t ADD CONSTRAINT uq_t_col UNIQUE (col);`

**Q5.** What is the difference between `DELETE FROM t` and
`TRUNCATE TABLE t`?
> `DELETE` is logged row-by-row, can be rolled back, and fires per-row
> triggers. `TRUNCATE` deallocates pages, is much faster, resets
> AUTO_INCREMENT, and in MySQL cannot be rolled back inside an InnoDB
> transaction (the implicit COMMIT happens).

---

## 8. Companion Runnable Files

| File                                  | Topic                                |
|---------------------------------------|--------------------------------------|
| `exercises/01-select-where.sql`       | SELECT, WHERE, BETWEEN, IN, LIKE     |
| `exercises/02-joins.sql`              | INNER/LEFT/RIGHT/CROSS/SELF joins    |
| `exercises/03-group-having.sql`       | GROUP BY, HAVING, aggregates         |
| `exercises/04-subquery-cte.sql`       | Scalar, IN, EXISTS, correlated, CTE  |
| `exercises/05-window-functions.sql`   | ROW_NUMBER, RANK, LAG/LEAD           |
| `exercises/schema.sql`                | The shared `student / course / sc` schema |
| `exercises/seed.sql`                  | Sample data                          |

Open them after starting MySQL from `tools/docker-compose.yml`.
