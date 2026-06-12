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

## 5. DCL — Privileges

```sql
GRANT SELECT, INSERT ON student TO 'app_user'@'%';
GRANT  ALL PRIVILEGES ON dbname.* TO 'admin'@'%' WITH GRANT OPTION;
REVOKE INSERT ON student FROM 'app_user'@'%';
```

`WITH GRANT OPTION` lets the grantee re-grant the privilege to others.
A common multiple-choice trap.

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
