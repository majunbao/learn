# 15 — Transactions

> Syllabus reference: P128–P130
>
> A **transaction** is the unit of work the DBMS treats as atomic.
> Either everything in the unit happens, or nothing does. The four
> **ACID** guarantees are the contract every relational DB promises;
> understanding them is mandatory for the exam and for survival in
> production.

---

## 1. The Transaction Lifecycle

```
        ┌─── COMMIT ───► committed → durable
START   │
TRAN ───┤
        │
        └─── ROLLBACK ──► aborted → all changes undone
```

A transaction can also implicitly abort on error (constraint violation,
deadlock, crash). The DBMS guarantees the same recovery either way.

### Standard SQL syntax

```sql
START TRANSACTION;
   UPDATE account SET balance = balance - 100 WHERE id = 1;
   UPDATE account SET balance = balance + 100 WHERE id = 2;
COMMIT;        -- or ROLLBACK
```

Most clients run in **autocommit** mode (every statement is its own
transaction). Disable it (`SET autocommit = 0`) to write multi-statement
transactions.

### Savepoints (partial rollback)

```sql
SAVEPOINT s1;
   UPDATE ...;
ROLLBACK TO SAVEPOINT s1;     -- undo only the part after s1
   UPDATE ...;
COMMIT;                       -- final commit still atomic
```

---

## 2. ACID — The Four Guarantees

| Letter | Property      | Plain-English meaning                                              |
|--------|---------------|---------------------------------------------------------------------|
| **A**  | Atomicity     | All operations succeed or all are undone — no half-done txn       |
| **C**  | Consistency   | Each txn moves the DB from one valid state to another             |
| **I**  | Isolation     | Concurrent txns appear to run alone (subject to isolation level)  |
| **D**  | Durability    | Once `COMMIT` returns, the change survives crashes                |

### How the DBMS implements each

| Property | Mechanism                                  |
|----------|--------------------------------------------|
| A        | Undo log / rollback segment                |
| C        | Constraints + application logic            |
| I        | Locking and/or MVCC (chapter 17)           |
| D        | Write-ahead log (WAL) flushed to disk      |

---

## 3. Concurrency Anomalies

If multiple transactions run with insufficient isolation, four classic
anomalies can appear:

| Anomaly                | What happens                                                       |
|------------------------|--------------------------------------------------------------------|
| **Dirty read**         | Txn A reads data written but not yet committed by Txn B            |
| **Non-repeatable read**| Txn A reads the same row twice and gets different values because Txn B updated it in between |
| **Phantom read**       | Txn A re-runs the same range query and sees new rows that Txn B inserted |
| **Lost update**        | Two txns read the same value, both compute a new value, both write back — one update is lost |

---

## 4. SQL Isolation Levels

Defined by ANSI/ISO SQL. From weakest to strongest:

| Level                | Dirty | Non-repeatable | Phantom |
|----------------------|-------|----------------|---------|
| **READ UNCOMMITTED** | ✘     | ✘              | ✘       |
| **READ COMMITTED**   | ✔     | ✘              | ✘       |
| **REPEATABLE READ**  | ✔     | ✔              | ✘       |
| **SERIALIZABLE**     | ✔     | ✔              | ✔       |

(✔ = prevented, ✘ = still possible.)

Default in popular DBMSs:

| DBMS         | Default level    |
|--------------|------------------|
| MySQL InnoDB | REPEATABLE READ (with gap locks → also prevents phantoms) |
| PostgreSQL   | READ COMMITTED   |
| Oracle       | READ COMMITTED   |
| SQL Server   | READ COMMITTED   |

Change it per session:

```sql
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
```

---

## 5. Worked Example — Lost Update

Two cashiers process the same gift card with balance 100:

```
Time   Txn A                       Txn B
t1     SELECT balance → 100
t2                                  SELECT balance → 100
t3     balance := 100 − 30 = 70
t4                                  balance := 100 − 40 = 60
t5     UPDATE ... SET balance=70
t6                                  UPDATE ... SET balance=60   ← lost A's change
```

Final balance is 60 instead of 30. Solutions:

1. **Pessimistic lock**: `SELECT balance FROM card WHERE id=… FOR UPDATE`
   inside an explicit transaction.
2. **Optimistic version**: add a `version` column, write
   `UPDATE ... SET balance=?, version=version+1 WHERE id=? AND version=?`
   and retry on conflict.
3. **Atomic delta**: `UPDATE card SET balance = balance - ? WHERE id = ?`
   — one statement that the DBMS serialises internally.

---

## 6. Schedule Theory (the math behind isolation)

* A **schedule** is an interleaving of operations from several transactions.
* A schedule is **serial** if no operations interleave across txns.
* A schedule is **serialisable** if its effects equal *some* serial
  schedule.
* Two main equivalences:
  * **Conflict-serialisable** — checked via the precedence graph
    (a.k.a. dependency graph). No cycle → conflict-serialisable.
  * **View-serialisable** — strictly weaker (allows more schedules)
    but NP-hard to check; rarely used in practice.

### Precedence graph algorithm
1. Node per transaction.
2. Edge `Ti → Tj` if Ti executes an operation that **conflicts** with a
   later operation by Tj on the same data item. Two operations
   conflict iff at least one is a write.
3. If the graph is a **DAG (acyclic)**, the schedule is
   conflict-serialisable.

---

## 7. Exam-Style Questions

**Q1.** Which property of ACID guarantees that a committed change
survives a crash?
> **Durability.**

**Q2.** A txn reads a row, performs a network call, then re-reads the
same row and gets a different value. Which anomaly is this?
> **Non-repeatable read.**

**Q3.** Which isolation level prevents phantom reads but may still
allow non-repeatable reads?
> *None of the standard ANSI levels — REPEATABLE READ prevents
> non-repeatable reads but may allow phantoms, and SERIALIZABLE
> prevents both. Trick question.*

**Q4.** What does autocommit imply?
> Every SQL statement is wrapped in its own transaction and committed
> immediately.

**Q5.** Two transactions T1, T2 execute the schedule
`R1(A), W2(A), W1(A), R2(B)`. Build the precedence graph.
> Edges: `T1 → T2` (R1(A) before W2(A) — conflict), `T2 → T1` (W2(A)
> before W1(A) — conflict). Cycle → **not conflict-serialisable**.

---

## 8. Further Reading

* Bernstein, Hadzilacos, Goodman, *Concurrency Control and Recovery in
  Database Systems* (free PDF online).
* Silberschatz et al., *Database System Concepts*, ch. 14–17.
