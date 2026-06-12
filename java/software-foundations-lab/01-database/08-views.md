# 08 — Views

> Syllabus reference: P61–P63
>
> A **view** is a virtual table defined by a query. It doesn't store
> data of its own (with the exception of materialised views — see §6);
> querying a view re-runs the underlying query.

---

## 1. Why Views Exist — Three Reasons

1. **Simplification** — package a complex join behind a simple name.
2. **Security** — expose only the columns/rows a user is allowed to see;
   `GRANT SELECT ON v_student_public ...` instead of granting on the
   raw table.
3. **Logical data independence** (chapter 03) — if the conceptual
   schema changes, redefine the view; applications stay unchanged.

---

## 2. Creating, Querying and Dropping

```sql
CREATE VIEW v_cs_students AS
SELECT sid, sname, age
FROM   student
WHERE  dept = 'CS';

SELECT * FROM v_cs_students WHERE age < 20;

DROP VIEW v_cs_students;

-- Replace (most dialects)
CREATE OR REPLACE VIEW v_cs_students AS
SELECT sid, sname FROM student WHERE dept = 'CS';
```

You can build views on top of other views — but deep stacks hurt
performance and debuggability.

---

## 3. Updatable vs. Read-Only Views

A view is **updatable** (you can `INSERT`/`UPDATE`/`DELETE` through it)
only if the DBMS can deterministically map a row in the view back to
exactly one row in a base table.

### Conditions a view must usually satisfy to be updatable

* It's defined on **a single base table** (or a single updatable view).
* Its `SELECT` list contains **no aggregates** (`SUM`, `COUNT`, ...) and
  **no `DISTINCT`**.
* It has **no `GROUP BY` or `HAVING`**.
* It has **no `UNION` / `INTERSECT` / `EXCEPT`**.
* Every column not in the view must allow `NULL` or have a `DEFAULT`
  (so that inserts work).

### Example — non-updatable

```sql
CREATE VIEW v_dept_avg AS
SELECT dept, AVG(age) AS avg_age FROM student GROUP BY dept;
```

`UPDATE v_dept_avg SET avg_age = 22 WHERE dept = 'CS';` is rejected:
the DBMS cannot decide which of N students should change.

### `WITH CHECK OPTION`

```sql
CREATE VIEW v_cs_students AS
SELECT sid, sname, dept FROM student WHERE dept = 'CS'
WITH CHECK OPTION;
```

This forbids inserting/updating rows through the view that would
**not satisfy the view's WHERE clause** (e.g. inserting a student
whose `dept` is `'EE'` via `v_cs_students`). Without it, the row
would silently disappear from the view.

---

## 4. Pros & Cons Cheat-Sheet

| Pros                                       | Cons                                          |
|--------------------------------------------|-----------------------------------------------|
| Query simplification, naming               | Performance — view is re-evaluated each call  |
| Security boundary                          | Updatability restrictions can confuse devs    |
| Logical data independence                  | Hidden complexity — devs may not see joins    |
| Encapsulation of business logic            | View-on-view-on-view leads to fragile schemas |

---

## 5. Worked Examples

### 5.1 Hide salary from HR app
```sql
CREATE VIEW v_employee_public AS
SELECT emp_id, name, dept, hire_date
FROM   employee;

GRANT SELECT ON v_employee_public TO hr_app;
REVOKE ALL ON employee FROM hr_app;
```

### 5.2 Per-row security
```sql
CREATE VIEW v_my_orders AS
SELECT * FROM "order"
WHERE  user_id = CURRENT_USER_ID();        -- pseudo-function for illustration
```

### 5.3 A reporting view to simplify a 4-way join
```sql
CREATE VIEW v_student_grades AS
SELECT s.sid, s.sname, c.cname, sc.grade
FROM   student s
JOIN   sc       ON s.sid = sc.sid
JOIN   course c ON sc.cid = c.cid;
```

Now reporting code is:
```sql
SELECT cname, AVG(grade) FROM v_student_grades GROUP BY cname;
```

---

## 6. Materialised Views (物化视图) — A Quick Note

Some DBMSs (Oracle, PostgreSQL, BigQuery) support **materialised
views** that physically store the query result.

* Querying them is fast (no recomputation).
* They must be **refreshed** (`REFRESH MATERIALIZED VIEW`) — manually
  or on a schedule.
* MySQL does **not** have materialised views built in; you simulate
  them with a regular table + scheduled job.

Use materialised views for expensive aggregates that don't need to be
millisecond-fresh (dashboards, weekly reports).

---

## 7. Exam-Style Questions

**Q1.** A view is best described as:
A. a copy of a table  B. a virtual table defined by a query
C. an index on a table  D. a backup of a table
> Answer: B.

**Q2.** Which of the following operations **cannot** be performed
through all views?
A. `SELECT`  B. `INSERT`  C. `UPDATE`  D. `DELETE`
> Answer: B, C, D may all be restricted; only `SELECT` is guaranteed.

**Q3.** Which option, when added to `CREATE VIEW`, rejects updates
that would make rows fall outside the view's filter?
> `WITH CHECK OPTION`.

**Q4.** Views provide which kind of data independence?
> **Logical** data independence.

**Q5.** Which of the following views is definitely **not** updatable?
A. one based on a single table with all columns
B. one with a `GROUP BY`
C. one with `WHERE` only
D. one with an inner join
> Answer: B (aggregates make individual rows non-traceable).

---

## 8. Further Reading

* SQL Standard ISO/IEC 9075 — Part 1, §4.15 "Views".
* PostgreSQL docs: *Materialized Views*.
* Oracle Database SQL Reference: *CREATE VIEW*.
