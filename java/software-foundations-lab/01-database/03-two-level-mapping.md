# 03 — The Two-Level Mappings & Data Independence

> Syllabus reference: P8–P10
>
> Building on chapter 02, the two mappings are the *mechanism* that
> delivers the *property* of data independence.

---

## 1. The Two Mappings

```
External schema 1   External schema 2   ...   External schema N
        │                  │                          │
        └──────────────────┼──────────────────────────┘
                           │  ① External / Conceptual mapping
                           ▼
                  Conceptual schema  (one)
                           │
                           │  ② Conceptual / Internal mapping
                           ▼
                  Internal schema  (one)
                           │
                           ▼
                       Physical storage
```

### Mapping ① — External ⇄ Conceptual

* Tells the DBMS **how each external view is derived from the
  conceptual schema**.
* In SQL terms: the `SELECT` statement inside `CREATE VIEW`.
* If the conceptual schema changes (e.g. add a column, split a table),
  the DBA only needs to rewrite this mapping; **applications using the
  view stay unchanged**.
* This is exactly **logical data independence**.

### Mapping ② — Conceptual ⇄ Internal

* Tells the DBMS **how the conceptual relations are physically stored**.
* In SQL terms: choice of storage engine, indexes, tablespaces,
  partitioning, compression.
* If the storage changes (new index, switch engine, repartition),
  applications using `SELECT ... FROM table` stay unchanged.
* This is exactly **physical data independence**.

---

## 2. Two Kinds of Data Independence

| Independence            | Insulates against                      | Mapping that does the work |
|-------------------------|----------------------------------------|----------------------------|
| **Logical**             | Changes to the **conceptual schema**   | External ⇄ Conceptual      |
| **Physical**            | Changes to the **internal schema**     | Conceptual ⇄ Internal      |

> Mnemonic: "Logical change → fix the **L**eft mapping (the upper one
> closer to the user)". "Physical change → fix the **P**hysical
> mapping (the lower one closer to disk)".

Logical independence is **harder to achieve** than physical
independence because it requires the DBMS to translate updates back
through view-definitions, which can be ambiguous (the famous
"updatable view" problem).

---

## 3. Concrete Scenarios

| Scenario                                                       | Which independence saves you? |
|----------------------------------------------------------------|-------------------------------|
| The DBA adds a new column to `EMPLOYEE`                        | Logical                       |
| The DBA splits `EMPLOYEE` into `EMP_PUBLIC` + `EMP_PRIVATE`    | Logical                       |
| The DBA creates a new B+ tree index on `EMPLOYEE(dept)`        | Physical                      |
| The DBA moves the table from `disk0` to a faster SSD           | Physical                      |
| The DBA changes block size from 8 KB to 16 KB                  | Physical                      |
| A user view drops a column the application never used          | Logical                       |
| The conceptual schema renames `salary` to `wage`               | Logical (rewrite the view!)   |

---

## 4. Why This Matters in Practice

Without these two mappings:

* Adding a column would break every program that did `SELECT *`.
* Adding an index would force every program to be re-compiled.
* Every application would need to know the exact physical layout —
  rendering the DB completely uneconomic to evolve.

Mature ORMs (Hibernate, MyBatis) deliberately encourage
**logical-level access** (`SELECT name FROM emp` rather than
`SELECT * FROM emp`) precisely so logical independence keeps working.

---

## 5. Exam-Style Questions

**Q1.** When the storage method of a base table is changed (e.g. switching
from heap file to clustered B+ tree), application programs do not have
to change. This is:
A. logical data independence
B. physical data independence
C. data sharing
D. data integrity
> Answer: B.

**Q2.** When the conceptual schema changes but external views remain
valid through view definitions, we say the system provides:
A. logical data independence
B. physical data independence
C. distribution transparency
D. concurrency control
> Answer: A.

**Q3.** Which mapping ensures logical data independence?
A. external/conceptual  B. conceptual/internal  C. external/internal  D. none
> Answer: A.

**Q4.** Which of the following will **NOT** affect application code
under physical data independence?
①Adding an index  ②Changing storage device  ③Adding a new column
④Switching storage engine
> ①②④ — physical independence covers them.
> ③ is a *logical* change, requiring the **external/conceptual** mapping
> to be rewritten (or no change if the view doesn't expose that column).

---

## 6. Further Reading

* Silberschatz et al., *Database System Concepts*, §1.4.
* Date, *An Introduction to Database Systems*, ch. 2 (data independence).
