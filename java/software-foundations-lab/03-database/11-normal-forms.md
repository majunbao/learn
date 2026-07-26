# 11 — Normal Forms

> Syllabus reference: P82–P99
>
> A **normal form** is a quality criterion for a relational schema.
> Higher forms eliminate more anomalies. The progression
> **1NF → 2NF → 3NF → BCNF → 4NF → 5NF** is the most-tested topic in
> the database part of the exam.

---

## 1. Why Normalise?

Un-normalised schemas suffer from three classic **update anomalies**:

| Anomaly        | Symptom                                                          |
|----------------|------------------------------------------------------------------|
| Insertion      | Cannot insert a fact because some unrelated info is missing      |
| Deletion       | Deleting one row throws away unrelated information               |
| Update         | A single change must be repeated in many rows; risk of inconsistency |

Plus **redundancy** (same fact stored many times) → wasted storage.

---

## 2. First Normal Form (1NF) — Atomicity

> A relation is in **1NF** iff every attribute value is **atomic**
> (no repeating groups, no multi-valued cells, no nested tables).

### Violation
```
order_id | items
1001     | "Java x2 @50; Code x1 @80"
```

### Fix
Split the `items` string into separate rows:
```
order_id | book | qty | price
1001     | Java | 2   | 50
1001     | Code | 1   | 80
```

> 1NF is the baseline — any "real" relational table is automatically 1NF.

---

## 3. Second Normal Form (2NF) — No Partial Dependency

> A relation is in **2NF** iff it is in 1NF and **every non-prime
> attribute is fully functionally dependent on every candidate key**
> (no partial FD on a candidate key).

A **non-prime attribute** is one that does not belong to any candidate key.

### Worked example

`SC(sid, cid, grade, sname, dept)`, candidate key `(sid, cid)`,
FDs: `(sid,cid) → grade`, `sid → sname`, `sid → dept`.

* `sname` depends on `sid` alone (a subset of the key) → **partial FD**
  → violates 2NF.

### Decomposition
* `STUDENT(sid PK, sname, dept)`
* `SC(sid PK FK, cid PK, grade)`

Now every non-prime attribute fully depends on its (whole) key.

> **2NF problem appears only when the candidate key is composite.**
> Single-attribute keys cannot have partial FDs.

---

## 4. Third Normal Form (3NF) — No Transitive Dependency on a Key

> A relation is in **3NF** iff it is in 2NF and **no non-prime attribute
> transitively depends on a candidate key**.

### Worked example

`STUDENT(sid, sname, dept, dept_head)`, key `sid`,
FDs: `sid → dept`, `dept → dept_head`.

* `sid → dept → dept_head` is a transitive FD. `dept_head` is non-prime
  and transitively depends on the key → **violates 3NF**.

### Decomposition
* `STUDENT(sid PK, sname, dept)`
* `DEPARTMENT(dept PK, dept_head)`

### Alternative 3NF Statement (equivalent)
A schema R is in 3NF iff for every non-trivial FD `X → A`:

* `X` is a super key, **or**
* `A` is a prime attribute (part of some candidate key).

---

## 5. Boyce-Codd Normal Form (BCNF) — The Strict 3NF

> A relation is in **BCNF** iff for every non-trivial FD `X → Y`,
> **X is a super key**.

BCNF removes the second escape hatch of 3NF (the "or A is prime" part).

### Example violating BCNF but satisfying 3NF

`R(sid, course, instructor)` with FDs:

* `(sid, course) → instructor`
* `instructor → course`

Candidate keys: `(sid, course)` and `(sid, instructor)`. All three
attributes are prime. The FD `instructor → course` has `instructor` as
its LHS, which is **not** a super key. → **violates BCNF**.
3NF accepts it because `course` is a prime attribute, but the redundancy
(every (sid, instructor) pair re-stores `course`) is real.

### BCNF decomposition
* `R1(sid, instructor)`
* `R2(instructor, course)`

> BCNF decomposition is **always lossless** but may **not preserve all
> FDs** (see chapter 13).

---

## 6. Fourth Normal Form (4NF) — No Non-Trivial Multi-Valued Dependency

A **multi-valued dependency (MVD)** `X →→ Y` exists when, for any value
of `X`, the set of `Y` values is determined independently of any other
columns.

> A relation is in **4NF** iff it is in BCNF and every non-trivial MVD
> `X →→ Y` has X as a super key.

### Example
`STUDENT_COURSE_HOBBY(sid, course, hobby)` where a student's courses
and hobbies are independent.

* `sid →→ course` and `sid →→ hobby` (non-trivial MVDs, sid not a super key).
* Redundancy: each (course, hobby) pair is repeated.

### Decomposition
* `SC(sid, course)`
* `SH(sid, hobby)`

---

## 7. Fifth Normal Form (5NF / PJ/NF)

Concerns **join dependencies** that are not implied by candidate keys.
Rarely tested directly; the exam mention is "5NF eliminates redundancy
caused by join dependencies".

---

## 8. The Big Picture

```
1NF  ─── add atomicity
  │
  ▼
2NF  ─── remove partial FDs    (only matters with composite key)
  │
  ▼
3NF  ─── remove transitive FDs (non-prime → non-prime)
  │
  ▼
BCNF ─── every FD's LHS is a super key
  │
  ▼
4NF  ─── remove non-trivial MVDs
  │
  ▼
5NF  ─── remove non-trivial join dependencies
```

Every higher form implies all the lower forms.

---

## 9. Cheat-Sheet for the Exam

| Form | Removes                        | Quick check                                       |
|------|--------------------------------|---------------------------------------------------|
| 1NF  | Multi-valued cells             | Are values atomic?                                |
| 2NF  | Partial FDs on candidate key   | Composite key? Any subset already determines a non-prime attr? |
| 3NF  | Transitive FDs                 | Non-prime → non-prime path?                       |
| BCNF | All non-super-key LHS          | Is every FD's LHS a super key?                    |
| 4NF  | Non-trivial MVDs               | Two independent multi-valued sets?                |

---

## 10. Worked End-to-End Example

`R(sid, sname, dept, dept_head, cid, grade)`

Given FDs:
* `sid → sname, dept`
* `dept → dept_head`
* `(sid, cid) → grade`

**Candidate key:** `(sid, cid)`.

Check normalisation:

1. **2NF?** `sid → sname` is a partial FD on key `(sid, cid)`. **Fails**.
2. Decompose to remove partial FDs:
   * `STUDENT(sid PK, sname, dept, dept_head)`
   * `SC(sid PK FK, cid PK, grade)`
3. **Now check STUDENT for 3NF**: `sid → dept → dept_head` is transitive. **Fails**.
4. Further decompose:
   * `STUDENT(sid PK, sname, dept FK)`
   * `DEPARTMENT(dept PK, dept_head)`
   * `SC(sid PK FK, cid PK, grade)`

All three resulting relations are now in BCNF (and therefore 3NF, 2NF, 1NF).

---

## 11. Exam-Style Questions

**Q1.** A relation in 3NF is guaranteed to have no:
A. partial FD  B. transitive FD on the key  C. MVD  D. join dependency
> Answer: **both A and B** (3NF implies 2NF, which removes partial FDs).
> Best single answer: B (the new property 3NF adds).

**Q2.** Which form requires that every non-trivial FD's LHS be a super key?
> BCNF.

**Q3.** Schema `R(A, B, C)` with `B → C`. Candidate key = `(A, B)`.
Which normal form is it in?
> 1NF (B is part of the key but `B → C` is a partial FD → fails 2NF).

**Q4.** Schema `R(A, B, C)`, key `A`, FDs `A → B`, `B → C`.
Which normal form does it satisfy at most?
> 2NF (single-attribute key → no partial FDs). It fails 3NF because of
> transitive FD `A → B → C`.

**Q5.** Why can BCNF decomposition lose FDs but 3NF synthesis cannot?
> Because the 3NF synthesis algorithm explicitly creates one relation
> per FD in the canonical cover, preserving every FD. BCNF requires
> stronger conditions that sometimes force a split which spreads an
> FD across two relations.

---

## 12. Further Reading

* Codd, "Further Normalization of the Data Base Relational Model", 1971.
* Silberschatz et al., *Database System Concepts*, ch. 8.
* Date, *Database Design and Relational Theory*.
