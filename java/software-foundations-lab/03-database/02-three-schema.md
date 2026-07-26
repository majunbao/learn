# 02 — The Three-Schema Architecture

> Syllabus reference: P5–P7
>
> Proposed by ANSI/SPARC in 1975, the **three-schema architecture** is
> the conceptual backbone of every modern DBMS. It defines three
> independent layers so that changes in one layer don't ripple into the
> others — the property called **data independence**.

---

## 1. The Three Schemas

```
                   ┌───────────────────────┐
       User A ───► │  External schema      │     "What this user sees"
                   │  (external view 1)    │
                   └───────────┬───────────┘
                               │  ← External / conceptual mapping
                   ┌───────────▼───────────┐
                   │  Conceptual schema    │     "What the DB actually contains"
                   │  (logical view)       │
                   └───────────┬───────────┘
                               │  ← Conceptual / internal mapping
                   ┌───────────▼───────────┐
                   │  Internal schema      │     "How it is stored on disk"
                   │  (physical view)      │
                   └───────────────────────┘
```

### 1.1 External schema (外模式 / 子模式 / user view)

* Describes the data **as a particular user or application sees it**.
* Implemented in SQL as **VIEWs**.
* One conceptual schema → many external schemas.
* Purpose: hide irrelevant attributes, enforce per-user security.

### 1.2 Conceptual schema (概念模式 / 模式 / logical schema)

* The **single, complete** description of the database.
* Defines all relations, attributes, types, constraints, relationships.
* Implemented in SQL as **CREATE TABLE / CREATE CONSTRAINT** etc.
* There is **exactly one** conceptual schema per database.

### 1.3 Internal schema (内模式 / 存储模式 / physical schema)

* Describes the **physical layout** — file organisation, indexes,
  partitioning, compression, block size.
* There is **exactly one** internal schema per database.
* You normally don't write it directly; the DBMS manages it (storage
  engines, tablespaces, etc.).

---

## 2. Why three layers?  →  **Data independence**

The whole point of the architecture is to **decouple** the three layers
so that a change in one does not force changes in the others.
This is achieved through **two mappings** (see chapter 03):

| Mapping                       | Provides                               |
|-------------------------------|----------------------------------------|
| External ⇄ Conceptual         | **Logical data independence**          |
| Conceptual ⇄ Internal         | **Physical data independence**         |

---

## 3. Memorise the Counts!

| Schema     | How many per DB? |
|------------|------------------|
| External   | Many (one per user view) |
| Conceptual | Exactly **1**            |
| Internal   | Exactly **1**            |

Exam questions love to test this. "A database has only one ___ schema."
Answer: conceptual (or internal). External schemas are many.

---

## 4. Mapping to Real SQL Objects

| Three-schema term | Real-world SQL artifact                       |
|-------------------|-----------------------------------------------|
| External schema   | `CREATE VIEW`                                 |
| Conceptual schema | `CREATE TABLE`, `CREATE CONSTRAINT`, `CREATE TRIGGER` |
| Internal schema   | tablespaces, storage engine (`InnoDB`), block size, file layout |

Indexes (`CREATE INDEX`) live primarily at the **internal** level — they
change storage/access, not the logical meaning of the data.

---

## 5. Worked Example

Consider a payroll database:

* **External schemas**
  * `HR_VIEW` — sees `(emp_id, name, dept, hire_date)` (no salary).
  * `MANAGER_VIEW` — sees `(emp_id, name, salary, bonus)`.
* **Conceptual schema** —
  `EMPLOYEE(emp_id PK, name, dept, hire_date, salary, bonus, ssn)`.
* **Internal schema** — InnoDB table, B+ tree primary index on `emp_id`,
  secondary index on `(dept, hire_date)`, 16 KB pages.

A web developer queries `HR_VIEW`; they never know the salary column
exists. That's the external layer doing its job.

If the DBA adds a new column `nickname` to `EMPLOYEE`, the two views
remain valid — that's **logical data independence**.

If the DBA migrates the table from MyISAM to InnoDB, the two views and
the `EMPLOYEE` table remain valid — that's **physical data
independence**.

---

## 6. Exam-Style Questions

**Q1.** A database has how many conceptual schemas?
A. 0  B. 1  C. many  D. depends on the DBMS
> Answer: B.

**Q2.** Which schema describes how data is physically stored?
A. external  B. conceptual  C. internal  D. user
> Answer: C (internal).

**Q3.** Adding a new index does **not** affect the application program.
Which kind of data independence is this?
A. logical  B. physical  C. external  D. user
> Answer: B (physical).

**Q4.** A SQL `VIEW` corresponds to which level of schema?
A. external  B. conceptual  C. internal  D. all of the above
> Answer: A (external).

---

## 7. Further Reading

* ANSI/X3/SPARC Study Group, *Interim Report* (1975).
* Silberschatz et al., *Database System Concepts*, §1.4 "View of Data".
