# 14 — Database Design

> Syllabus reference: P108–P127
>
> The **database design lifecycle** is a four-phase engineering process
> that turns a vague business request into a normalised, indexed,
> deployable schema. Every textbook and every exam question uses the
> same four-phase model.

---

## 1. The Four Phases

```
   Requirement
   analysis        →   Conceptual    →   Logical      →   Physical
   (P108–P112)         design            design           design
                       (P113–P119)       (P120–P124)      (P125–P127)
```

| Phase                | Output                                          |
|----------------------|-------------------------------------------------|
| Requirement analysis | Data dictionary, data-flow diagrams, business rules |
| Conceptual design    | ER diagram (DBMS-independent)                   |
| Logical design       | Relational schema in 3NF/BCNF (DBMS-family-specific) |
| Physical design      | Indexes, partitions, storage layout (DBMS-specific) |

A fifth phase, **implementation & maintenance**, covers schema
deployment, ongoing tuning and rollback plans.

---

## 2. Requirement Analysis (P108–P112)

Goal: understand **what data** must be stored and **what queries** must
be supported.

### Deliverables

1. **Data dictionary** — every data item with name, type, domain,
   constraints, source, who uses it.
2. **Data-flow diagram (DFD)** — how data moves between processes,
   stores and external entities.
3. **Business rules** — constraints that cannot be inferred from the
   data structure alone (e.g. "salary must be raised by no more than
   10 % per year").
4. **Volume estimates** — rows per table, growth rate, peak QPS.

### Exam tip
The "user" in this phase is the **business stakeholder**. Database
specialists translate, never assume.

---

## 3. Conceptual Design (P113–P119)

Goal: produce a **DBMS-independent** model of the data — almost always
an **ER diagram** (Chen 1976) or an **EER** (extended ER) diagram.

### ER notation cheat-sheet

| Shape                | Meaning                                     |
|----------------------|---------------------------------------------|
| Rectangle            | Entity                                      |
| Diamond              | Relationship                                |
| Ellipse              | Attribute                                   |
| Double-line ellipse  | Multi-valued attribute                      |
| Dashed ellipse       | Derived attribute (e.g. `age` from DOB)     |
| Underline            | Primary key                                 |
| Double rectangle     | Weak entity (depends on owner)              |
| Double diamond       | Identifying relationship for weak entity    |
| Triangle             | ISA (specialisation/generalisation)         |

### Cardinality notation

| Notation        | Meaning                                |
|-----------------|----------------------------------------|
| `1 : 1`         | One-to-one                             |
| `1 : N`         | One-to-many                            |
| `M : N`         | Many-to-many                           |
| `(min, max)`    | Participation (e.g. `(0, N)`, `(1, 1)`)|

### Integrating multiple ER diagrams

Real projects produce **local ER diagrams** per business area, then
merge them. Conflicts to resolve:

* **Naming conflicts** — two diagrams call the same concept different
  things (synonyms) or different concepts the same thing (homonyms).
* **Structural conflicts** — one diagram models X as an entity, another
  as an attribute.
* **Constraint conflicts** — different domains, different cardinalities.

Resolution rules (memorise!):

1. Unify naming.
2. Prefer modelling concepts that have their own attributes as
   **entities**.
3. Take the **stricter** constraint when in doubt.

---

## 4. Logical Design (P120–P124)

Goal: convert the ER diagram into a **relational schema** (or whatever
the chosen DBMS family supports) and then **normalise** it.

### ER → Relational mapping rules

| ER construct                            | Relational outcome                            |
|-----------------------------------------|-----------------------------------------------|
| Strong entity                           | New relation; key = entity's PK               |
| Weak entity                             | New relation; key = owner's PK + partial key  |
| 1 : 1 relationship                      | Add FK to either side (often optional side)   |
| 1 : N relationship                      | Add FK to the **many** side                   |
| M : N relationship                      | **New relation** with both FKs as composite PK|
| Multi-valued attribute                  | Separate relation with FK back                |
| ISA (specialisation)                    | Three options: single table inheritance, class table, joined table |
| Composite attribute                     | Flatten into sub-attributes                   |

### Then normalise
Apply the normalisation chapters (10–13) until every relation is in
**3NF** (or BCNF where possible without losing dependency preservation).

### Add user-friendly objects
* Views for security / convenience.
* Granular `GRANT` / `REVOKE` privileges.

---

## 5. Physical Design (P125–P127)

Goal: tune the **on-disk layout** of the logical schema for the
expected workload.

### Decisions to make

| Topic                  | Typical decisions                                    |
|------------------------|------------------------------------------------------|
| Indexing               | Which columns to index? B+ tree, hash, bitmap?       |
| Clustered key          | Use auto-increment? Use natural key?                 |
| Partitioning           | Range? Hash? List? Composite?                        |
| Storage engine         | InnoDB vs. MyISAM (MySQL); heap vs. table-cluster (Oracle) |
| File layout            | Tablespaces, separate fast disks for indexes / logs  |
| Buffer-pool sizing     | Match working-set size                               |
| Backup / archive plan  | Full / incremental cadence (see chapter 16)          |

### Workload classification
* **OLTP** (Online Transaction Processing) — short reads/writes, many
  concurrent users → favour B+ tree indexes, careful normalisation,
  small transactions.
* **OLAP** (Online Analytical Processing) — long aggregates over
  history → favour column stores, materialised views, denormalisation.

Most real systems are a mix (HTAP) and require careful trade-offs.

---

## 6. Iteration & Reverse Engineering

The four phases are not strictly sequential — physical bottlenecks
often force a logical-schema change, which may force an ER revision.
Treat the lifecycle as a **spiral**, not a waterfall.

For legacy systems, the reverse path is also valid:
**physical → logical → conceptual** ("reverse engineering"), used when
moving an existing database to a new platform.

---

## 7. Worked Mini-Project — Bookstore

### Phase 1 — Requirements
* Customers buy books online.
* Each book has one or more authors, exactly one category.
* Orders contain ≥ 1 line items; each line records the price paid.
* Payments may be retried; only the latest SUCCESS counts as paid.

### Phase 2 — Conceptual (simplified)

Entities: `User`, `Address`, `Book`, `Author`, `Category`, `Order`,
`OrderItem`, `Payment`.

Relationships (cardinalities):
* `User 1—N Address`
* `User 1—N Order`
* `Order 1—N OrderItem`
* `OrderItem N—1 Book`
* `Book M—N Author`
* `Category 1—N Book`
* `Order 1—N Payment`

### Phase 3 — Logical
See `module-10-bookstore-app/src/main/resources/schema.sql`-style DDL:
9 relations, all in BCNF, except `OrderItem.unit_price` which is a
**deliberate denormalisation** for historical correctness.

### Phase 4 — Physical
* Cluster `user`, `order`, `book` on auto-increment PK.
* Secondary index on `book(category_id)`, `order(user_id, placed_at)`.
* Partition the `order_item` table by `order_id` range when row count
  passes ~100 M.

---

## 8. Exam-Style Questions

**Q1.** Which phase produces the ER diagram?
> Conceptual design.

**Q2.** Which phase introduces indexes?
> Physical design.

**Q3.** When converting an `M : N` relationship to a relational schema,
the result is:
A. add FK to one side
B. add FK to the other side
C. add a new relation with both FKs as composite PK
D. nothing, M:N is forbidden
> Answer: C.

**Q4.** When merging two local ER diagrams and one models `customer`
as an entity while the other models it as an attribute of `order`,
this is a:
A. naming conflict  B. structural conflict  C. value conflict  D. type conflict
> Answer: B (structural conflict).

**Q5.** A weak entity must always be modelled with:
> A **double rectangle** + a **double diamond** identifying relationship.
> Its PK is the owner's PK plus its own partial key.

---

## 9. Further Reading

* Batini, Ceri, Navathe, *Conceptual Database Design: An
  Entity-Relationship Approach*.
* Silberschatz et al., *Database System Concepts*, ch. 7.
