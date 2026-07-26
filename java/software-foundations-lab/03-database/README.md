# 01 — Database Systems

> 18 chapters covering the complete database section of the Chinese
> software engineer exam syllabus (P2–P143), rewritten in
> textbook-level depth. Each chapter is self-contained: theory →
> worked examples → exam-style Q&A → further reading.

## Roadmap

| #  | File                              | Syllabus | Topic |
|----|-----------------------------------|----------|-------|
| 01 | [`01-data-models.md`](01-data-models.md) | P2–P4 | Data models (conceptual / logical / physical), the relational model, key vocabulary |
| 02 | [`02-three-schema.md`](02-three-schema.md) | P5–P7 | ANSI/SPARC three-schema architecture |
| 03 | [`03-two-level-mapping.md`](03-two-level-mapping.md) | P8–P10 | Two-level mappings, logical & physical data independence |
| 04 | [`04-relational-algebra.md`](04-relational-algebra.md) | P11–P29 | Relational algebra: 8 operators, joins, division, equivalences |
| 05 | [`05-algebra-to-sql.md`](05-algebra-to-sql.md) | P30–P37 | Translating between relational algebra and SQL |
| 06 | [`06-sql-language.md`](06-sql-language.md) | P38–P56 | DDL, DML, queries, joins, sub-queries, NULL semantics |
| 07 | [`07-sql-control.md`](07-sql-control.md) | P57–P60 | Stored procedures, functions, triggers, cursors |
| 08 | [`08-views.md`](08-views.md) | P61–P63 | Views, updatability, WITH CHECK OPTION, materialised views |
| 09 | [`09-indexes.md`](09-indexes.md) | P64–P66 | B+ tree / hash / bitmap, leftmost-prefix rule, EXPLAIN |
| 10 | [`10-functional-dependency.md`](10-functional-dependency.md) | P67–P81 | FDs, Armstrong's axioms, attribute closure, finding all keys |
| 11 | [`11-normal-forms.md`](11-normal-forms.md) | P82–P99 | 1NF → 2NF → 3NF → BCNF → 4NF → 5NF |
| 12 | [`12-decomposition.md`](12-decomposition.md) | P100–P103 | BCNF decomposition and 3NF synthesis algorithms |
| 13 | [`13-lossless-fd-preserving.md`](13-lossless-fd-preserving.md) | P104–P107 | Lossless-join test, chase, dependency preservation |
| 14 | [`14-database-design.md`](14-database-design.md) | P108–P127 | The 4-phase design lifecycle: requirements → conceptual → logical → physical |
| 15 | [`15-transaction.md`](15-transaction.md) | P128–P130 | ACID, isolation levels, concurrency anomalies, schedule theory |
| 16 | [`16-backup-recovery.md`](16-backup-recovery.md) | P131–P134 | Backup types, WAL, ARIES, RPO / RTO |
| 17 | [`17-locking.md`](17-locking.md) | P135–P137 | Lock modes, 2PL, deadlocks, MVCC |
| 18 | [`18-distributed-db.md`](18-distributed-db.md) | P138–P143 | Sharding, replication, 2PC, CAP, BASE |

## Suggested Reading Order

The chapter numbering is the recommended order. A few alternative
study paths:

- **Pure theory crammer**: 01 → 02 → 03 → 04 → 10 → 11 → 12 → 13.
- **SQL hands-on first**: 06 → 07 → 08 → 09, then come back for theory.
- **Concurrency & operations**: 15 → 17 → 16 → 18.

## Pairing With the Hands-On MySQL

Theory in this module + practice in `tools/docker-compose.yml`:

```bash
docker compose -f ../tools/docker-compose.yml up -d
mysql -h127.0.0.1 -ulab -plab lab
```

Then try out the algebra/SQL translations from chapter 05 directly on
the running database.

## How Each Chapter Is Structured

```
1. Concept / definition
2. Diagrams or tables
3. Worked examples
4. Algorithms / formulas
5. Exam-style Q&A with answers
6. Further reading (books / papers / online docs)
```

## Why This Folder Has No `pom.xml`

It contains only Markdown. Maven would only get in the way. The folder
is **not** registered in the parent `pom.xml`'s `<modules>` list.
