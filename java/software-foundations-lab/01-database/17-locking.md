# 17 — Locking and Concurrency Control

> Syllabus reference: P135–P137
>
> Locks are the mechanism the DBMS uses to *implement* the isolation
> letter of ACID. The exam loves three topics: lock modes, two-phase
> locking, and deadlocks.

---

## 1. Lock Modes — Shared vs. Exclusive

| Lock | Symbol | Granted with                     | Conflicts with                  |
|------|--------|----------------------------------|---------------------------------|
| **Shared / read** | S | Other S locks                       | X                               |
| **Exclusive / write** | X | Nothing                          | S, X                            |

Compatibility matrix (✔ = compatible, ✘ = blocks):

|        | S  | X  |
|--------|----|----|
| **S**  | ✔  | ✘  |
| **X**  | ✘  | ✘  |

Acquire with explicit SQL:

```sql
-- shared read lock (MySQL)
SELECT ... FOR SHARE;
-- exclusive write lock
SELECT ... FOR UPDATE;
```

Most DML acquires its own locks automatically.

---

## 2. Lock Granularity & Intention Locks

Locks can be placed at different levels:

| Granularity   | Pros                          | Cons                           |
|---------------|-------------------------------|--------------------------------|
| Row           | Maximum concurrency           | Many locks, lots of bookkeeping |
| Page          | Compromise                    | Hotspots if rows in same page  |
| Table         | Cheap                         | Kills concurrency              |
| Database      | Used for DDL                  | Very rare                      |

To let a transaction lock a row inside a table while another wants to
lock the whole table, DBMSs use **intention locks** (multi-granularity
locking):

| Lock | Meaning                                         |
|------|-------------------------------------------------|
| IS   | Intend to acquire S on a finer-grained item     |
| IX   | Intend to acquire X on a finer-grained item     |
| SIX  | S on the entire item plus IX on finer pieces    |

Compatibility (acquirer rows, holder columns):

|     | IS | IX | S  | SIX | X  |
|-----|----|----|----|-----|----|
| IS  | ✔  | ✔  | ✔  | ✔   | ✘  |
| IX  | ✔  | ✔  | ✘  | ✘   | ✘  |
| S   | ✔  | ✘  | ✔  | ✘   | ✘  |
| SIX | ✔  | ✘  | ✘  | ✘   | ✘  |
| X   | ✘  | ✘  | ✘  | ✘   | ✘  |

---

## 3. Two-Phase Locking (2PL)

> **A transaction must acquire all its locks before releasing any.**

This single rule guarantees **conflict-serialisability**.

### Phases
1. **Growing phase** — acquire locks; never release.
2. **Shrinking phase** — release locks; never acquire.

Once the transaction releases its first lock, it cannot acquire any
more.

### Strict 2PL (S2PL)
* X locks are held until COMMIT/ROLLBACK.
* Prevents **cascading rollback** (no other txn ever reads dirty data).

### Rigorous 2PL (R2PL)
* **All** locks (S and X) held until commit.
* Easier to reason about; the most common in real systems.

### Limitations
2PL guarantees serialisability but **not deadlock freedom**. See §5.

---

## 4. Predicate / Gap Locks (Solving Phantoms)

A predicate lock protects a *range of keys* even if some of those rows
don't exist yet — necessary to prevent phantom reads.

InnoDB calls them **next-key locks**: a row lock + a gap lock on the
gap before it. The combination prevents another txn from inserting a
new row in the protected range.

---

## 5. Deadlocks

A deadlock occurs when transactions form a cycle in the wait-for
graph:

```
T1 wants X on row A (held by T2)
T2 wants X on row B (held by T1)
```

### Detection
The DBMS periodically builds the **wait-for graph** and checks for
cycles. If found, it picks a **victim** transaction (usually the one
that has done the least work or the youngest) and aborts it.

### Prevention strategies

| Strategy                | Behaviour                                       |
|-------------------------|-------------------------------------------------|
| **Wait-Die**            | If `Ti` is older than `Tj` (smaller timestamp), `Ti` waits; otherwise `Ti` aborts. |
| **Wound-Wait**          | If `Ti` is older than `Tj`, `Ti` wounds (aborts) `Tj`; otherwise `Ti` waits. |
| **Timeout**             | Abort any txn that waits longer than `t` seconds. |
| **Always lock in same order** | Application-level discipline (cheap, effective). |

### Avoiding deadlocks in application code
1. Always lock objects in the **same global order**.
2. Keep transactions **short**.
3. Use the lowest sufficient isolation level.
4. Retry on deadlock; this is normal and expected, not exceptional.

---

## 6. MVCC — A Lock-Free Alternative for Readers

Most modern DBs (InnoDB, PostgreSQL, Oracle) use **Multi-Version
Concurrency Control**:

* Each write creates a new version of the row.
* Reads see a **snapshot** consistent with their start timestamp.
* Readers never block writers, and writers never block readers.
* Writers still need locks against each other.

This drastically reduces contention without weakening isolation.

---

## 7. Worked Example — Constructing a Wait-For Graph

Schedule:
* `T1` locks A (X), then requests B (X) — waiting.
* `T2` locks B (X), then requests A (X) — waiting.

Wait-for graph: `T1 → T2 → T1` → cycle → **deadlock**.
Victim chosen → e.g. T2 aborts → T1 proceeds → application retries T2.

---

## 8. Exam-Style Questions

**Q1.** State the two-phase locking rule.
> A transaction must acquire **all** its locks before releasing any.

**Q2.** Which lock modes are compatible?
A. X and X  B. X and S  C. S and S  D. X and IS
> Answer: **C** (S and S share).

**Q3.** Two-phase locking guarantees serialisability but **not**:
A. consistency  B. deadlock freedom  C. durability  D. atomicity
> Answer: B.

**Q4.** What does an intention lock at table level represent?
> A declaration that the transaction intends to acquire row-level
> locks within that table — used by the DBMS to detect conflicts with
> requests for table-level locks.

**Q5.** Which strategy aborts a transaction immediately if it tries to
wait for a younger one?
A. Wait-Die  B. Wound-Wait  C. Timeout  D. Strict 2PL
> Answer: **A. Wait-Die** (older waits, younger dies).

---

## 9. Further Reading

* Bernstein, Hadzilacos, Goodman, *Concurrency Control and Recovery in
  Database Systems*.
* InnoDB internals: locking and isolation chapters of the MySQL Reference Manual.
