# 16 — Backup and Recovery

> Syllabus reference: P131–P134
>
> Disks fail, processes crash, datacentres burn. A DBA's job is to
> guarantee that **no committed data is ever lost**, and that the
> database can resume operation within a tolerable time after any
> failure.

---

## 1. Classifying Failures

| Failure type             | Example                              | Recovery technique              |
|--------------------------|--------------------------------------|---------------------------------|
| Transaction failure      | Constraint violation, explicit ROLLBACK | Undo (rollback) using the log |
| System failure (soft)    | Power cut, OS crash                  | Crash recovery: REDO + UNDO     |
| Media failure (hard)     | Disk loss, file corruption           | Restore from backup + REDO log  |
| Disaster / data centre   | Fire, flood                          | Off-site backups, replication   |

---

## 2. Backup Strategies

### 2.1 Full backup
Complete copy of the entire database. Simple but slow and large.

### 2.2 Incremental backup
Copies only the data changed since the **last incremental** backup.
Smallest size; restore requires the full backup + every increment in order.

### 2.3 Differential backup
Copies all data changed since the **last full** backup.
Larger than incremental, but restore needs only the full + the latest
differential.

### Common cadence

```
Sun         Mon  Tue  Wed  Thu  Fri  Sat
Full        Inc  Inc  Inc  Inc  Inc  Inc
```

or

```
1st of month        rest of the month
Full                Differential daily
```

### Logical vs. physical backups

| Type        | Example tool       | Pros                              | Cons                          |
|-------------|--------------------|-----------------------------------|-------------------------------|
| Logical     | `mysqldump`, `pg_dump` | Portable across versions, easy to inspect | Slow on large DBs, no PITR    |
| Physical    | `xtrabackup`, `pg_basebackup` | Fast, supports PITR with WAL | Tied to engine version, opaque |

### Point-in-time recovery (PITR)
Most modern systems combine periodic physical backups + a continuous
**WAL archive**, letting you restore to any timestamp.

---

## 3. The Write-Ahead Log (WAL)

The single most important invariant in DB recovery:

> **Before any modified data page is written to disk, the corresponding
> log record must already be on disk.**

This is the **WAL rule**. Each log record contains:

* Transaction id
* Operation (insert / update / delete)
* Before-image (for UNDO)
* After-image (for REDO)

Log file names: MySQL `redo log` (InnoDB) + `binlog`, PostgreSQL `WAL`,
Oracle `redo log` + `archive log`.

---

## 4. Recovery Algorithms

### 4.1 Undo / Redo / Undo-Redo
Three classical algorithms. Modern DBMSs use the **undo-redo** flavour
(ARIES) because it allows the buffer manager to flush dirty pages
whenever convenient.

### 4.2 ARIES — the de facto standard
A three-pass algorithm executed at startup after a crash:

1. **Analysis** — scan the WAL forward from the last checkpoint to
   rebuild the transaction table (active txns) and the dirty-page
   table.
2. **REDO** — re-apply every change since the earliest dirty page,
   bringing the database to the exact state at the time of the crash.
3. **UNDO** — roll back every transaction that was active at crash
   time.

### 4.3 Checkpoints
Periodically the DBMS writes a **CHECKPOINT** record that captures the
list of active transactions and dirty pages. Recovery starts scanning
from the latest checkpoint, drastically shortening startup time.

---

## 5. Recovery Objectives

| Metric | Meaning                                                  |
|--------|----------------------------------------------------------|
| **RPO** (Recovery Point Objective) | Maximum tolerable data loss measured in time |
| **RTO** (Recovery Time Objective)  | Maximum tolerable downtime                  |

| RPO target  | Required tooling                              |
|-------------|-----------------------------------------------|
| Hours       | Daily full backup                             |
| Minutes     | WAL archiving + frequent incremental backups  |
| Seconds     | Synchronous replication / DR site             |
| Zero        | Synchronous replication with quorum commit    |

---

## 6. Worked Example — A Crash Recovery Story

State at crash:
* Last checkpoint at LSN 1000.
* Active transactions: T1 (started LSN 900), T2 (started LSN 1100).
* T1 issued `UPDATE A SET v=1` (LSN 1050) and `COMMIT` (LSN 1080).
* T2 issued `UPDATE B SET v=2` (LSN 1150) — not committed.
* Buffer pool flushed A's page at LSN 1100; B's page not yet flushed.
* Crash at LSN 1200.

Recovery:
1. **Analysis** — scan from LSN 1000. Find:
   * T1 ended (commit at 1080).
   * T2 still active at crash.
   * Dirty pages: page B at LSN 1150.
2. **REDO** — re-apply log records that come after the dirty page's
   `recLSN`. Page A was already flushed; the REDO for LSN 1050 is a
   no-op (compare page LSN ≥ record LSN). Page B is re-updated from
   LSN 1150.
3. **UNDO** — T2 is still active → undo its updates using the
   before-images. Page B reverts.

Database is now consistent: T1's commit survives, T2 has been
completely rolled back.

---

## 7. Replication — A Quick Note

Replication is **not a backup**; it is a high-availability tool. A
malicious / accidental DELETE will replicate too. Always pair
replication with proper time-shifted backups.

| Mode                  | Behaviour                                            |
|-----------------------|------------------------------------------------------|
| **Async**             | Master commits; slaves catch up later. Possible data loss on master failure. |
| **Semi-sync**         | Master waits until at least one slave acknowledges.  |
| **Sync (quorum)**     | Master waits until majority acknowledges (Raft/Paxos). |

---

## 8. Exam-Style Questions

**Q1.** Which backup type produces the smallest daily file?
A. full  B. incremental  C. differential  D. logical
> Answer: B.

**Q2.** Restoring from full + differential requires how many backup
files?
> **Two** — the latest full and the latest differential.

**Q3.** State the WAL rule.
> Log records describing a change must reach stable storage **before**
> the corresponding data page is written.

**Q4.** Which recovery algorithm uses a three-pass analysis-redo-undo
sequence with checkpoints?
> **ARIES.**

**Q5.** RPO = 0 implies what infrastructure?
> Synchronous replication with quorum commit (or equivalent durable,
> multi-site write).

---

## 9. Further Reading

* Mohan et al., "ARIES: A Transaction Recovery Method Supporting
  Fine-Granularity Locking and Partial Rollbacks Using Write-Ahead
  Logging", *ACM TODS*, 1992.
* PostgreSQL docs: WAL & Continuous Archiving.
* Percona blog: backup/restore best practices.
