# 01 — Data Models

> Syllabus reference: P2–P4
>
> A **data model** is the formal language we use to describe data, the
> constraints on that data, and the operations we can perform on it.
> Every DBMS implements one (or more) data model; understanding them is
> the foundation for everything else in this module.

---

## 1. The Three Building Blocks of Any Data Model

| Component             | What it answers                                       |
|-----------------------|-------------------------------------------------------|
| **Data structure**    | What the data looks like (tables? trees? graphs?)     |
| **Data operations**   | What you can do to it (query, insert, update, delete) |
| **Integrity constraints** | What "valid" data means (PK, FK, CHECK, NOT NULL) |

If you can identify these three pieces for a given model, you understand
the model.

---

## 2. The Three Levels of Data Models

```
┌─────────────────────────────────────────────────┐
│ 1. Conceptual model     (close to the real world)│
│    e.g. ER diagram                              │
├─────────────────────────────────────────────────┤
│ 2. Logical model        (close to the DBMS)     │
│    e.g. relational, hierarchical, network,      │
│         object-oriented, document, key-value    │
├─────────────────────────────────────────────────┤
│ 3. Physical model       (close to the disk)     │
│    e.g. B+ tree files, heap files, LSM tree     │
└─────────────────────────────────────────────────┘
```

* **Conceptual model** — independent of any DBMS. Used during requirement
  analysis. The classic conceptual model is the **Entity-Relationship
  (ER) model** (Chen 1976).
* **Logical model** — depends on the chosen DBMS family. The dominant one
  for the last 40 years is the **relational model** (Codd 1970).
* **Physical model** — how the logical model is laid out on storage.
  Usually hidden by the DBMS.

> Exam tip: the question "ER diagram belongs to which level of model?" is
> a perennial favorite. Answer: **conceptual**.

### 2.1 ER Model — Entity Types

The exam distinguishes four kinds of entities and five kinds of
attributes. Memorise these; they appear in multiple-choice and in
diagram-reading questions.

**Entity types**

| Type | Notation (Chen) | Meaning | Example |
|------|-----------------|---------|---------|
| Strong entity | Rectangle | Exists independently; has its own PK | `STUDENT(sid, ...)` |
| Weak entity | Double rectangle | Existence depends on an owner entity; PK = owner's PK + partial key | `DEPENDENT(employee_id, name, ...)` |
| Associative entity | Rectangle around a diamond | Used when an M:N relationship itself has attributes | `ENROLLMENT(sid, cid, grade, semester)` |

**Attribute types**

| Type | Notation (Chen) | Meaning | Example |
|------|-----------------|---------|---------|
| Simple (atomic) | Ellipse | Cannot be split further | `age`, `gender` |
| Composite | Ellipse connected to sub-ellipses | Can be split into sub-parts | `address` → `(street, city, zip)` |
| Single-valued | Ellipse (single line) | One value per entity | `birth_date` |
| Multi-valued | Double ellipse | Zero or more values per entity | `phone_numbers` |
| Derived | Dashed ellipse | Computable from other attributes | `age` (from `birth_date`) |

**Relationship cardinality** (Chen notation)

| Label | Meaning |
|-------|---------|
| `1 : 1` | One-to-one |
| `1 : N` | One-to-many |
| `M : N` | Many-to-many |

> Exam trap: "Is `grade` an attribute of `STUDENT` or of the
> `ENROLLMENT` relationship?" — It belongs to the **relationship**
> (associative entity), because a grade only exists when a specific
> student takes a specific course.

---

## 3. The Four Classical Logical Models

### 3.1 Hierarchical model (层次模型)
* Data is organised as a **tree** (one parent, many children).
* Example: IBM IMS (1968).
* Pros: simple, fast for 1-to-N traversal.
* Cons: cannot naturally express M-to-N; updates are awkward.

### 3.2 Network model (网状模型)
* Generalised tree → **directed graph** (a record can have several parents).
* Example: CODASYL DBTG.
* Pros: expresses M-to-N directly.
* Cons: very complex pointer chasing for the programmer.

### 3.3 Relational model (关系模型)  ← **the one the exam cares about most**
* Data lives in **two-dimensional tables (relations)**.
* Every row is a **tuple**; every column is an **attribute**.
* Operations are defined by **relational algebra** (chapter 04).
* Integrity constraints come in three flavours:
  * **Entity integrity** — primary key cannot be NULL.
  * **Referential integrity** — a foreign key must either be NULL or match
    an existing primary-key value.
  * **User-defined integrity** — domain / CHECK constraints, e.g.
    `age BETWEEN 0 AND 150`.

### 3.4 Object-oriented model (面向对象模型)
* Objects, methods, inheritance.
* Mostly used in CAD / CAM / multimedia DBs.

### 3.5 Modern non-relational variants (NoSQL)
Not in the classic textbook chapter but worth knowing:

| Family       | Example       | Sweet spot                                  |
|--------------|---------------|---------------------------------------------|
| Key-value    | Redis         | Caches, session stores                      |
| Document     | MongoDB       | Schema-flexible JSON-shaped data            |
| Column-family| Cassandra     | Wide rows, time-series                      |
| Graph        | Neo4j         | Highly connected data (social, knowledge)   |

### 3.6 Side-by-Side Comparison of the Four Classical Models

| Feature | Hierarchical | Network | Relational | Object-Oriented |
|---------|-------------|---------|------------|-----------------|
| Data structure | Tree | Directed graph | Table (relation) | Object (class) |
| M:N support | No (must split) | Yes (via sets) | Yes (via join table) | Yes (via references) |
| Query language | Procedural (DL/1) | Procedural (CODASYL DML) | Declarative (SQL) | OQL / native methods |
| Data independence | Low | Low | High | Medium |
| Typical system | IBM IMS | IDMS | MySQL, Oracle, PostgreSQL | ObjectStore, db4o |
| Exam relevance | ★★☆☆☆ | ★★☆☆☆ | ★★★★★ | ★☆☆☆☆ |

> Exam tip: "Which model uses a tree structure?" → Hierarchical.
> "Which model introduced the concept of a set (系)?" → Network.
> "Which model has the highest data independence?" → Relational.

---

## 4. Database System Components

A **database system** (数据库系统, DBS) is more than just the data.
The exam distinguishes four components:

```
┌──────────────────────────────────────────────┐
│                  USERS / DBA                  │
│         (define schema, write queries)        │
├──────────────────────────────────────────────┤
│              APPLICATION PROGRAMS             │
│    (Java / Python / web app using JDBC/ORM)   │
├──────────────────────────────────────────────┤
│                    DBMS                       │
│  (MySQL, Oracle, PostgreSQL — the software)   │
├──────────────────────────────────────────────┤
│                  DATABASE                     │
│       (the actual data files on disk)         │
└──────────────────────────────────────────────┘
```

| Component | Chinese | Role |
|-----------|---------|------|
| Database (DB) | 数据库 | The stored data itself — tables, indexes, logs |
| DBMS | 数据库管理系统 | The software that manages access, concurrency, recovery |
| Application programs | 应用程序 | Code that issues SQL via a driver (JDBC, ODBC) |
| Database Administrator (DBA) | 数据库管理员 | Human who designs schema, tunes performance, manages backups |

> Exam trap: "A database system consists of ___." The answer is all
> four: DB + DBMS + applications + DBA. The DBMS alone is not the
> whole system.

---

## 5. The Relational Model — Vocabulary You Must Memorise

| Term                | Synonym(s)             | Meaning                                                                |
|---------------------|------------------------|------------------------------------------------------------------------|
| Relation 关系       | Table                  | A set of tuples sharing the same schema                                |
| Tuple 元组          | Row, record            | One element of the relation                                            |
| Attribute 属性      | Column, field          | A named component of a tuple                                           |
| Domain 域           | Type                   | The set of permitted values for an attribute                           |
| Degree 度 / 元数    | Arity                  | Number of attributes                                                   |
| Cardinality 基数    | —                      | Number of tuples                                                       |
| Schema 模式         | Heading                | The set of attribute names + their domains                             |
| Instance 实例       | State                  | The set of tuples in a relation at a given moment                      |
| Candidate key 候选键| —                      | A minimal set of attributes that uniquely identifies a tuple           |
| Primary key 主键    | PK                     | The chosen candidate key                                               |
| Alternate key 候选/备用键 | —                | Candidate keys that were NOT chosen as primary                         |
| Foreign key 外键    | FK                     | Attribute(s) whose value must appear as a PK in another relation       |
| Super key 超键      | —                      | Any set of attributes that uniquely identifies a tuple (not minimal)   |

> Exam trap: **super key ⊇ candidate key ⊇ primary key**.
> "Candidate key must be minimal" is the property that distinguishes it
> from a super key.

---

## 6. Worked Example

Given relation `STUDENT(sid, name, dept, advisor, advisor_office)`:

* Tuple = one row, e.g. `(1001, 'Alice', 'CS', 'Bob', 'Room 305')`.
* Domain of `sid` = INT in `[10000000, 99999999]`.
* Degree = 5.
* If `sid` is unique, then `{sid}` is a candidate key, and so are
  `{sid, name}` (super key but not minimal — so NOT a candidate key).
* If every student has exactly one advisor and every advisor has one
  office, then `advisor → advisor_office` is a *functional dependency*
  (chapter 11) that you should remove via normalisation (chapter 12).

---

## 7. Exam-Style Questions

**Q1.** Which of the following is **not** part of a data model?
A. data structure  B. data operations  C. data backup  D. integrity constraints
> Answer: C. Backup belongs to DB administration, not the data model itself.

**Q2.** ER model belongs to which of the following?
A. conceptual model  B. logical model  C. physical model  D. external model
> Answer: A.

**Q3.** In a relational DB, "every non-NULL value of a foreign key must
equal some primary-key value in the referenced relation" is which kind
of integrity?
A. entity  B. referential  C. user-defined  D. domain
> Answer: B (referential integrity).

**Q4.** Given `R(A, B, C, D)` with candidate keys `{A}` and `{B, C}`,
how many super keys does R have?
> A super key is any attribute set that contains a candidate key.
> Total attributes = 4. Count sets containing `{A}`: fix A, the
> remaining 3 attributes can each be in or out → 2³ = 8.
> Count sets containing `{B, C}`: fix B and C, the remaining 2
> attributes can each be in or out → 2² = 4.
> Subtract the overlap (sets containing both `{A}` and `{B, C}`):
> fix A, B, C, the remaining 1 attribute can be in or out → 2.
> Total = 8 + 4 − 2 = **10 super keys**.

**Q5.** A database system (DBS) consists of:
A. DBMS only  B. DB + DBMS  C. DB + DBMS + applications  D. DB + DBMS + applications + DBA
> Answer: D.

**Q6.** A student's `phone_numbers` (they may have 0, 1, or several)
is which type of attribute in an ER diagram?
A. simple  B. composite  C. derived  D. multi-valued
> Answer: D (multi-valued, drawn as a double ellipse).

**Q7.** Which data model organises data as a tree?
A. relational  B. network  C. hierarchical  D. object-oriented
> Answer: C.

---

## 8. Further Reading

* E. F. Codd, "A Relational Model of Data for Large Shared Data Banks",
  *Communications of the ACM*, 1970.
* P. P. Chen, "The Entity-Relationship Model — Toward a Unified View of
  Data", *ACM TODS*, 1976.
* Silberschatz, Korth, Sudarshan — *Database System Concepts*, ch. 2.

---

## 9. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Data model | 数据模型 | 01 |
| Conceptual model | 概念模型 | 01 |
| Logical model | 逻辑模型 | 01 |
| Physical model | 物理模型 | 01 |
| Hierarchical model | 层次模型 | 01 |
| Network model | 网状模型 | 01 |
| Relational model | 关系模型 | 01 |
| Object-oriented model | 面向对象模型 | 01 |
| Entity | 实体 | 01 |
| Strong entity | 强实体 | 01 |
| Weak entity | 弱实体 | 01 |
| Attribute | 属性 | 01 |
| Simple / atomic attribute | 简单属性 | 01 |
| Composite attribute | 复合属性 | 01 |
| Single-valued attribute | 单值属性 | 01 |
| Multi-valued attribute | 多值属性 | 01 |
| Derived attribute | 派生属性 | 01 |
| Relationship | 联系 | 01 |
| Cardinality | 基数 | 01 |
| Database (DB) | 数据库 | 01 |
| DBMS | 数据库管理系统 | 01 |
| Database system (DBS) | 数据库系统 | 01 |
| DBA | 数据库管理员 | 01 |
| Relation | 关系 | 01 |
| Tuple | 元组 | 01 |
| Domain | 域 | 01 |
| Degree | 度 / 元数 | 01 |
| Schema | 模式 | 01 |
| Instance | 实例 | 01 |
| Candidate key | 候选键 / 候选码 | 01 |
| Primary key (PK) | 主键 / 主码 | 01 |
| Foreign key (FK) | 外键 / 外码 | 01 |
| Super key | 超键 / 超码 | 01 |
| Entity integrity | 实体完整性 | 01 |
| Referential integrity | 参照完整性 | 01 |
| User-defined integrity | 用户定义完整性 | 01 |
