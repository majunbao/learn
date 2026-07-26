# 04 — Relational Algebra

> Syllabus reference: P11–P29
>
> Relational algebra is the **mathematical query language** behind SQL.
> Every SQL `SELECT` can be rewritten as a relational-algebra expression,
> and exam questions love asking you to do that translation in both
> directions. Master this chapter and SQL becomes trivial.

---

## 1. Notation Used in This Chapter

| Symbol  | Name             | Meaning                                |
|---------|------------------|----------------------------------------|
| `R, S`  | Relations        | Tables                                 |
| `t`     | Tuple            | A row in a relation                    |
| `A, B`  | Attribute names  | Column names                           |
| `θ`     | A predicate      | A condition such as `age > 18`         |
| `|R|`   | Cardinality      | Number of tuples in R                  |
| `deg(R)`| Degree           | Number of attributes in R              |

---

## 2. The Eight Operators

Relational algebra has **8 standard operators**, divided into two groups:

### 2.1 Set-theoretic operators (5)

| Operator       | Symbol | Requires                                | What it returns                                |
|----------------|--------|------------------------------------------|------------------------------------------------|
| Union          | `R ∪ S`| Same schema (union-compatible)           | Rows in R or S (duplicates removed)            |
| Intersection   | `R ∩ S`| Same schema                              | Rows in both R and S                           |
| Difference     | `R − S`| Same schema                              | Rows in R but not in S                         |
| Cartesian product | `R × S` | (no restriction)                       | Every combination of (r, s)                    |
| Rename         | `ρ_{A→B}(R)` | —                                  | R with attribute A renamed to B                |

### 2.2 Relational-specific operators (3)

| Operator       | Symbol     | Description                                                  |
|----------------|------------|--------------------------------------------------------------|
| Selection      | `σ_θ(R)`   | Keep only rows satisfying predicate θ (think `WHERE`)        |
| Projection     | `π_{A,B}(R)` | Keep only attributes A, B (think `SELECT A, B`)            |
| Join           | `R ⋈ S`    | Combine matching rows (see §4)                               |

Plus a derived but very common operator: **Division** `R ÷ S` (§5).

---

## 3. Selection, Projection, Rename — The "WHERE / SELECT" Trio

### 3.1 Selection `σ`

```
σ_{age > 18}(STUDENT)
```
* Keeps rows where the predicate is true.
* Does not change the schema (attributes stay the same).
* Cardinality: `|σ_θ(R)| ≤ |R|`.

### 3.2 Projection `π`

```
π_{name, dept}(STUDENT)
```
* Keeps only the listed columns, **and** removes duplicate rows.
* Degree shrinks: `deg(π_{A1...An}(R)) = n`.
* Cardinality: `|π(R)| ≤ |R|` (duplicates may merge).

### 3.3 Rename `ρ`

```
ρ_{sid → student_id}(STUDENT)
```
* Used to disambiguate before joins (especially **self-joins**).

---

## 4. Joins — The Heart of Relational Algebra

### 4.1 Theta join (θ-join)
```
R ⋈_θ S  ≡  σ_θ(R × S)
```
Generic join with an arbitrary predicate. The most flexible — and most
expensive — form.

### 4.2 Equi-join
A θ-join where θ is one or more equalities, e.g.
`R ⋈_{R.A = S.A} S`. The two equal columns appear **twice** in the output.

### 4.3 Natural join `⋈`
* Equi-join on **every pair of attributes with the same name**.
* Duplicate columns are kept **once** in the output.
* Degree: `deg(R ⋈ S) = deg(R) + deg(S) − |common attributes|`.

#### Worked example
```
R(A, B):       S(B, C):
 a  1           1  x
 a  2           2  y
 b  1           3  z

R ⋈ S =
 A  B  C
 a  1  x
 a  2  y
 b  1  x
```

### 4.4 Outer joins

| Operator              | Notation       | Behaviour                                    |
|-----------------------|----------------|----------------------------------------------|
| Left outer join       | `R ⟕ S`        | Keep every R row; fill NULLs for missing S   |
| Right outer join      | `R ⟖ S`        | Keep every S row                             |
| Full outer join       | `R ⟗ S`        | Keep both sides                              |

These map directly to SQL `LEFT JOIN`, `RIGHT JOIN`, `FULL OUTER JOIN`.

### 4.5 Semi join and anti join

| Operator   | Notation | Meaning                                                |
|------------|----------|--------------------------------------------------------|
| Semi join  | `R ⋉ S`  | Rows of R that **have at least one match** in S        |
| Anti join  | `R ▷ S`  | Rows of R that **have no match** in S (the `NOT EXISTS`/`NOT IN` form) |

---

## 5. Division `R ÷ S`  ("for all")

Used for queries that contain the word **"every"** / **"all"**.

### Definition
Given `R(A, B)` and `S(B)`,
`R ÷ S = { a | ∀ b ∈ S, (a, b) ∈ R }`.

In English: the set of `A`-values that appear in R **with every**
`B`-value in S.

### Worked example — "Students who chose all CS courses"

```
ENROLL(sid, cid):           CS_COURSES(cid):
 1   c1                       c1
 1   c2                       c2
 1   c3
 2   c1
 3   c1
 3   c2

ENROLL ÷ CS_COURSES =
 sid
 1
```

Student 1 took both c1 and c2 → kept.
Student 2 missed c2; student 3 missed c1 → dropped.

### Identity to remember (exam classic)
```
R ÷ S  =  π_A(R)  −  π_A( (π_A(R) × S)  −  R )
```
Memorise the right-hand side; you can be asked to "express division
using basic operators only".

---

## 6. Putting It All Together — Big Worked Example

Schema:

```
STUDENT(sid PK, sname, dept)
COURSE (cid PK, cname, credit)
SC     (sid FK, cid FK, grade)
```

**Q.** "Find the names of students who took the course named 'DB'."

Step 1 — pick the DB course:
```
σ_{cname='DB'}(COURSE)
```

Step 2 — join with enrolments:
```
SC ⋈ σ_{cname='DB'}(COURSE)
```

Step 3 — join with students:
```
STUDENT ⋈ ( SC ⋈ σ_{cname='DB'}(COURSE) )
```

Step 4 — project names:
```
π_{sname}( STUDENT ⋈ SC ⋈ σ_{cname='DB'}(COURSE) )
```

Equivalent SQL:
```sql
SELECT DISTINCT s.sname
FROM   STUDENT s, SC, COURSE c
WHERE  s.sid = SC.sid
  AND  SC.cid = c.cid
  AND  c.cname = 'DB';
```

---

## 7. Algebraic Equivalences (used by the optimiser)

| Rule                                                        | Why it matters                      |
|-------------------------------------------------------------|-------------------------------------|
| `σ_{θ1∧θ2}(R) = σ_{θ1}(σ_{θ2}(R))`                          | Cascade of selections               |
| `σ_θ(R × S) = R ⋈_θ S`                                       | Replace product+filter with a join  |
| `σ_θ(R ⋈ S) = σ_θ(R) ⋈ S`  (if θ uses only R's attrs)         | **Push selection** before join → fewer rows |
| `π_L(R × S) = π_L(π_{L∩R}(R) × π_{L∩S}(S))`                   | **Push projection** before join     |
| `R ⋈ S = S ⋈ R`                                              | Joins are commutative               |
| `(R ⋈ S) ⋈ T = R ⋈ (S ⋈ T)`                                  | Joins are associative               |

> The query optimiser tries hundreds of these rewrites to find the
> cheapest plan. Hand-applying them is a popular exam question
> ("rewrite the expression to minimise intermediate-result size").

---

## 8. Exam-Style Questions

**Q1.** In relational algebra, the most expensive operator is usually:
A. selection  B. projection  C. natural join  D. Cartesian product
> Answer: D (its output size is |R|×|S|, before any filtering).

**Q2.** `π_A(R) − π_A(R − σ_{B=5}(R))` returns rows where the value of
B is:
> Always equal to 5 — this is the algebraic form of "ALL B = 5".

**Q3.** Given `R(A, B, C)` with 5 rows and `S(C, D)` with 4 rows,
the maximum cardinality of `R ⋈ S` (natural join on C) is:
> 5 × 4 = 20 (when every C-value of R equals every C-value of S).

**Q4.** Write `STUDENT ⋈ SC` using only **basic** operators.
> `π_{...}( σ_{STUDENT.sid = SC.sid}( STUDENT × SC ) )`.

**Q5.** Translate to SQL:
`π_{sname}( σ_{credit ≥ 3}(COURSE) ⋈ SC ⋈ STUDENT )`.
> ```sql
> SELECT DISTINCT s.sname
> FROM STUDENT s JOIN SC ON s.sid = SC.sid
>                JOIN COURSE c ON SC.cid = c.cid AND c.credit >= 3;
> ```

**Q6.** "Find students who took **every** course offered by the CS
department." Which operator do you need?
> Division (`÷`) — over `SC` and `(σ_{dept='CS'}(COURSE))`.

---

## 9. Cheat Sheet

```
Selection   σ_θ(R)            — WHERE
Projection  π_L(R)            — SELECT L
Rename      ρ_X(R)            — AS
Union       R ∪ S             — UNION
Diff        R − S             — EXCEPT
Intersect   R ∩ S             — INTERSECT
Product     R × S             — FROM R, S (no condition)
Join        R ⋈ S             — JOIN ON / NATURAL JOIN
Outer join  R ⟕ ⟖ ⟗ S          — LEFT/RIGHT/FULL JOIN
Semi/anti   R ⋉ S  / R ▷ S    — EXISTS / NOT EXISTS
Division    R ÷ S             — "for all" queries
```

---

## 10. Further Reading

* C. J. Date, *An Introduction to Database Systems*, ch. 7.
* Garcia-Molina, Ullman, Widom, *Database Systems: The Complete Book*,
  ch. 2 & 5.
