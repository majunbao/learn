# 05 — Translating Relational Algebra to SQL

> Syllabus reference: P30–P37
>
> The exam regularly gives you a relational-algebra expression and asks
> for the equivalent SQL — or vice-versa. This chapter is the
> **one-to-one translation table** plus worked examples in both
> directions.

---

## 1. Direct Mapping Table

| Algebra              | SQL keyword / construct                       |
|----------------------|-----------------------------------------------|
| `σ_θ(R)`             | `WHERE θ`                                     |
| `π_L(R)`             | `SELECT L` (use `DISTINCT` to mirror set semantics) |
| `ρ_X(R)`             | `AS X`                                        |
| `R ∪ S`              | `UNION`                                       |
| `R ∩ S`              | `INTERSECT` (or `INNER JOIN` on the keys)     |
| `R − S`              | `EXCEPT` / `MINUS` (or `NOT EXISTS`)          |
| `R × S`              | `FROM R, S` with no `WHERE`                   |
| `R ⋈ S`              | `JOIN ... ON` / `NATURAL JOIN`                |
| `R ⟕ S` / `⟖` / `⟗`   | `LEFT` / `RIGHT` / `FULL OUTER JOIN`          |
| `R ⋉ S`              | `WHERE EXISTS (SELECT 1 FROM S ...)`          |
| `R ▷ S`              | `WHERE NOT EXISTS (...)`                      |
| `R ÷ S`              | "double NOT EXISTS" (see §3.4)                |

> Two subtle but important differences between algebra and SQL:
>
> 1. SQL is **multiset (bag) semantics by default** — duplicates are
>    kept unless you write `DISTINCT`. Algebra is **set semantics**.
> 2. SQL has `NULL`; algebra (in its pure form) does not.

---

## 2. Common Schema for Examples

```
STUDENT(sid PK, sname, dept, age)
COURSE (cid PK, cname, credit, dept)
SC     (sid FK, cid FK, grade)
```

---

## 3. Worked Translations — Algebra → SQL

### 3.1 Simple selection / projection
```
π_{sname, age}( σ_{dept='CS'}(STUDENT) )
```
```sql
SELECT DISTINCT sname, age
FROM   STUDENT
WHERE  dept = 'CS';
```

### 3.2 Join + selection
```
π_{sname, cname}(
    σ_{grade ≥ 90}(
        STUDENT ⋈ SC ⋈ COURSE
    )
)
```
```sql
SELECT DISTINCT s.sname, c.cname
FROM   STUDENT s
JOIN   SC ON s.sid = SC.sid
JOIN   COURSE c ON SC.cid = c.cid
WHERE  SC.grade >= 90;
```

### 3.3 Self-join via rename
"Find pairs of students in the same department."
```
ρ_{X}(STUDENT) ⋈_{X.dept = Y.dept ∧ X.sid < Y.sid} ρ_{Y}(STUDENT)
```
```sql
SELECT x.sid, y.sid
FROM   STUDENT x
JOIN   STUDENT y ON x.dept = y.dept AND x.sid < y.sid;
```

### 3.4 Division — "every course of the CS department"
```
π_{sid, cid}(SC)  ÷  π_{cid}(σ_{dept='CS'}(COURSE))
```
SQL via **double NOT EXISTS** (the canonical pattern):
```sql
SELECT sid
FROM   STUDENT s
WHERE  NOT EXISTS (
    SELECT 1
    FROM   COURSE c
    WHERE  c.dept = 'CS'
      AND  NOT EXISTS (
          SELECT 1
          FROM   SC
          WHERE  SC.sid = s.sid AND SC.cid = c.cid
      )
);
```
Read it as: "no CS course is missing from this student's enrolment list".

### 3.5 Difference / Anti-join
"Students who took NO course at all."
```
π_{sid}(STUDENT) − π_{sid}(SC)
```
```sql
SELECT sid FROM STUDENT
EXCEPT
SELECT sid FROM SC;

-- or, portably:
SELECT s.sid
FROM   STUDENT s
WHERE  NOT EXISTS (SELECT 1 FROM SC WHERE SC.sid = s.sid);
```

### 3.6 Outer join
"List every student and their average grade if any."
```
π_{sname, avg_grade}(
    STUDENT ⟕ γ_{sid; AVG(grade)→avg_grade}(SC)
)
```
*(γ is the grouping operator — many books include it.)*
```sql
SELECT s.sname, AVG(SC.grade) AS avg_grade
FROM   STUDENT s
LEFT   JOIN SC ON s.sid = SC.sid
GROUP  BY s.sid, s.sname;
```

---

## 4. Worked Translations — SQL → Algebra

### 4.1
```sql
SELECT sname FROM STUDENT WHERE age < 20;
```
```
π_{sname}( σ_{age < 20}(STUDENT) )
```

### 4.2
```sql
SELECT s.sname, c.cname
FROM   STUDENT s, SC, COURSE c
WHERE  s.sid = SC.sid
  AND  SC.cid = c.cid
  AND  s.dept = 'CS';
```
```
π_{sname, cname}(
    σ_{s.dept='CS'}( STUDENT ⋈ SC ⋈ COURSE )
)
```

### 4.3
```sql
SELECT sid FROM SC GROUP BY sid HAVING COUNT(*) >= 5;
```
Using the grouping operator γ:
```
σ_{cnt ≥ 5}( γ_{sid; COUNT(*)→cnt}(SC) )
```
Then project `sid` if you only want the id.

---

## 5. Tips That Save You In The Exam

1. **Always project last** unless asked otherwise. Selections first
   reduce data, projections last avoid losing attributes you still need
   for joins.
2. **`DISTINCT` matters when going from SQL back to algebra**. SQL
   without `DISTINCT` ≠ pure projection.
3. **For "every"/"all" questions, reach for division** or its double
   `NOT EXISTS` form. Don't try to do it with `IN` — that's "any/exists".
4. **Self-joins need explicit rename** (`ρ` in algebra, `AS x, AS y`
   in SQL).
5. **Cartesian product (`R × S`) without a join condition is almost
   always a bug** in real systems. The exam will sometimes deliberately
   write `FROM R, S` and ask you to fix it.

---

## 6. Exam-Style Questions

**Q1.** Translate to SQL:
```
π_{sname}( σ_{credit>=4}(COURSE) ⋈ SC ⋈ STUDENT )
```
> ```sql
> SELECT DISTINCT s.sname
> FROM   STUDENT s JOIN SC ON s.sid = SC.sid
>                  JOIN COURSE c ON SC.cid = c.cid
> WHERE  c.credit >= 4;
> ```

**Q2.** Translate to algebra:
```sql
SELECT s.sid
FROM   STUDENT s
WHERE  s.sid IN (SELECT sid FROM SC WHERE grade >= 90);
```
> `π_{sid}( STUDENT ⋉ σ_{grade ≥ 90}(SC) )`  (semi-join).

**Q3.** Translate "students who took **all** 3-credit courses" to SQL.
> ```sql
> SELECT s.sid
> FROM   STUDENT s
> WHERE  NOT EXISTS (
>     SELECT 1 FROM COURSE c WHERE c.credit = 3
>       AND NOT EXISTS (
>           SELECT 1 FROM SC WHERE SC.sid = s.sid AND SC.cid = c.cid
>       )
> );
> ```

**Q4.** Which SQL clause corresponds to relational selection `σ`?
> `WHERE`.

**Q5.** Which SQL clause corresponds to relational projection `π`?
> The `SELECT` column list — and don't forget `DISTINCT` for true set
> semantics.

---

## 7. Further Reading

* Garcia-Molina et al., *Database Systems: The Complete Book*, ch. 6.
* Date, *An Introduction to Database Systems*, ch. 8.
