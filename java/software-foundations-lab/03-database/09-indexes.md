# 09 — Indexes

> Syllabus reference: P64–P66
>
> An **index** is an auxiliary data structure that lets the DBMS find
> rows without scanning the whole table. Indexes are the single most
> important performance tool in any relational DB — and the single most
> common topic where junior engineers go wrong.

---

## 1. Why Indexes Help

Without an index, finding `WHERE name = 'Alice'` requires a **full
table scan**: read every page, compare every row. With an index on
`name`, the DBMS walks a small B+ tree and jumps straight to the
matching row(s).

Rough orders of magnitude on a 1-million-row table:

| Access path                | I/O reads | Wall-clock                     |
|----------------------------|-----------|--------------------------------|
| Full table scan            | thousands | seconds                        |
| B+ tree index lookup       | ~3–4      | < 1 ms                         |

---

## 2. Index Types You Must Know

### 2.1 By data structure

| Structure   | Sweet spot                                  | DBMS examples                   |
|-------------|---------------------------------------------|---------------------------------|
| **B+ tree** | Range + equality on ordered keys            | MySQL InnoDB, PostgreSQL, Oracle |
| Hash        | Equality only (`=`)                         | MySQL MEMORY, PG `hash`         |
| Bitmap      | Low-cardinality columns, OLAP                | Oracle, vertica-like systems    |
| Inverted    | Full-text search                            | Elasticsearch, PG `tsvector`    |
| R-tree      | Spatial / geometric queries                 | PostGIS, MySQL spatial          |
| LSM tree    | Heavy writes                                | RocksDB, Cassandra, HBase       |

> Exam tip: when nothing else is stated, "index" means **B+ tree**.

### 2.2 By layout relative to data

| Type           | What it stores in leaves               | Per table   |
|----------------|----------------------------------------|-------------|
| **Clustered**  | The actual rows (data lives in the index) | At most 1 |
| **Non-clustered (secondary)** | Pointers / PK values back to the row | Many    |
| **Covering**   | Indexed columns include every column the query needs | depends |

In InnoDB, the **primary key is the clustered index**; secondary
indexes contain PK values, not row pointers, so a secondary lookup
costs one extra B+ tree walk ("back to clustered").

### 2.3 By uniqueness

| Kind        | Allows duplicates? |
|-------------|--------------------|
| `UNIQUE`    | No                 |
| Non-unique  | Yes                |
| Primary     | No (implicit `UNIQUE NOT NULL`) |

---

## 3. Creating, Inspecting, Dropping

```sql
CREATE INDEX idx_student_name              ON student(sname);
CREATE UNIQUE INDEX uq_email               ON student(email);
CREATE INDEX idx_sc_sid_cid_grade          ON sc(sid, cid, grade);   -- composite

SHOW INDEX FROM student;          -- MySQL
\d student                         -- PostgreSQL

DROP INDEX idx_student_name ON student;
```

---

## 4. Composite (Multi-column) Indexes — The "Leftmost Prefix" Rule

```sql
CREATE INDEX idx_abc ON t(a, b, c);
```

The DBMS can use the index for queries that filter on:

* `a`
* `a, b`
* `a, b, c`

It **cannot** use the index for:

* `b` alone
* `b, c`
* `c` alone

The first column of the composite index must appear in the predicate
(equality preferred). This is the **leftmost-prefix rule**, the most
asked-about index concept on the exam.

---

## 5. When Indexes Hurt

| Situation                                         | Why it hurts                         |
|---------------------------------------------------|--------------------------------------|
| Write-heavy table with many indexes               | Every INSERT/UPDATE touches every index |
| Very small tables (few hundred rows)              | A full scan is already cheap          |
| Low-cardinality columns (e.g. `gender CHAR(1)`)   | Optimiser ignores the index           |
| Functions applied to indexed column in `WHERE`    | `WHERE YEAR(date) = 2024` won't use index on `date` — use a sargable rewrite |
| Implicit type conversion in `WHERE`               | Same problem — index disabled         |

---

## 6. Reading an `EXPLAIN` Plan (MySQL)

```sql
EXPLAIN SELECT * FROM student WHERE sname = 'Alice';
```

Key columns:

| Column         | Meaning                                                       |
|----------------|---------------------------------------------------------------|
| `type`         | Access method (best → worst): `system, const, eq_ref, ref, range, index, ALL` |
| `possible_keys`| Indexes that could be used                                    |
| `key`          | Index actually used                                           |
| `rows`         | Estimated rows examined                                       |
| `Extra`        | Notes: `Using index` = covering, `Using filesort`, `Using temporary` |

`type = ALL` means full table scan — usually a red flag.

---

## 7. Worked Optimisation Example

Slow query (4-second execution):
```sql
SELECT *
FROM   order_item
WHERE  book_id = 1234
ORDER  BY order_id DESC
LIMIT  10;
```

`order_item` has 50 M rows and only a primary key on `(order_id, book_id)`.

Add a covering index:
```sql
CREATE INDEX idx_oi_book_order
    ON order_item(book_id, order_id DESC);
```

* The index sorts naturally by `book_id` then descending `order_id`,
  matching both the filter and the `ORDER BY`.
* Plan now: `type=ref`, `Extra=Using index`, rows ≈ 10.

---

## 8. Index Maintenance & Statistics

* The optimiser uses **statistics** (row count, histogram of values).
* Stale stats → bad plans. Force a refresh:
  * MySQL: `ANALYZE TABLE t;`
  * PostgreSQL: `ANALYZE t;`
* Indexes can be **rebuilt** when they fragment heavily.

---

## 9. Exam-Style Questions

**Q1.** A table can have at most how many clustered indexes?
> **1.** Because the table data is physically ordered by the clustered key.

**Q2.** Given `INDEX idx(a, b, c)`, which query **cannot** use the index?
A. `WHERE a=1 AND b=2`
B. `WHERE a=1 AND c=3`  (uses partial — a only)
C. `WHERE b=2 AND c=3`
D. `WHERE a=1`
> Answer: C. (`b, c` alone can't be served because the leftmost column
> `a` isn't in the predicate.)
> Note for B: the index can be used on `a` only; the `c=3` is a
> residual filter.

**Q3.** Which type of index is most suitable for full-text search?
A. B+ tree  B. Hash  C. Inverted  D. R-tree
> Answer: C.

**Q4.** Adding an index will **always**:
A. speed up queries
B. speed up `SELECT`s on the indexed column
C. slow down `INSERT/UPDATE/DELETE`
D. occupy extra space
> Answers C and D are guaranteed; A and B are common but not absolute.

**Q5.** `EXPLAIN` shows `type = ALL`. Best next action?
> Identify the column being filtered; check whether a useful index
> exists / can be added; check for `WHERE` clauses that disable index
> use (functions, implicit conversions).

---

## 10. Further Reading

* Markus Winand, *Use The Index, Luke!* (free online).
* MySQL Reference Manual — Optimization → Indexes.
* PostgreSQL docs — Indexes (B-tree, Hash, GIN, GiST, BRIN, SP-GiST).
