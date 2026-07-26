# 18 — Distributed Databases

> Syllabus reference: P138–P143
>
> A **distributed database** stores data on several physical nodes (in
> the same data centre or across the world). The user should perceive
> it as a single logical database. Achieving that illusion requires
> three new ideas on top of everything you already know: data
> partitioning, replication, and distributed transactions.

---

## 1. What Makes a Database "Distributed"?

A distributed DB has:

1. **Multiple data sites** that are physically separate.
2. A **network** connecting them.
3. A **distributed query processor** that can route, fragment, and
   recombine queries.

Compare:

| System type      | One node? | One DBMS? | Notes                                  |
|------------------|-----------|-----------|----------------------------------------|
| Centralised      | yes       | yes       | Classic single-server DB               |
| Parallel         | many      | yes       | Same software, same site, shared disk  |
| Distributed      | many      | yes       | Same software, multiple sites          |
| Federated        | many      | many      | Different DBMSs joined under a wrapper |

---

## 2. Goals → "Transparencies"

A well-designed distributed DB hides the distribution from the user.
The exam loves these terms.

| Transparency                | Hides what                                                   |
|-----------------------------|--------------------------------------------------------------|
| **Location**                | Which site stores the data                                   |
| **Fragmentation**           | That a table is split into pieces                            |
| **Replication**             | That multiple copies exist                                   |
| **Failure**                 | That some sites are down                                     |
| **Concurrency**             | That other users are running queries on the same data        |

Aim for **all five**; in practice, full failure transparency is hard.

---

## 3. Fragmentation (Partitioning)

Cutting a table into smaller pieces stored on different nodes.

### 3.1 Horizontal fragmentation (sharding)
Split **rows** by a predicate.

```
USERS shard 1: WHERE country = 'CN'
USERS shard 2: WHERE country = 'US'
USERS shard 3: WHERE country IN ('JP','KR')
```

Variants: range, hash, list, composite. Hash sharding spreads load
evenly; range sharding supports range scans.

### 3.2 Vertical fragmentation
Split **columns**. Typical for hot/cold separation:

```
USERS_HOT  (id PK, email, password_hash)
USERS_COLD (id PK, bio, preferences, profile_image)
```

Both fragments must share the primary key.

### 3.3 Mixed fragmentation
Vertical first, then horizontal (or vice versa) — common in real
warehouses.

### Correctness conditions

Every fragmentation must satisfy:

1. **Completeness** — every data item appears in at least one fragment.
2. **Reconstruction** — the original table can be rebuilt by joining
   (vertical) or unioning (horizontal) the fragments.
3. **Disjointness** (for horizontal only) — no row in two fragments
   (unless replicated explicitly).

---

## 4. Replication

Storing multiple copies of the same fragment to increase availability
and read throughput.

| Mode               | Pros                                  | Cons                                       |
|--------------------|---------------------------------------|--------------------------------------------|
| **Synchronous**    | No data loss; readers always fresh    | Higher write latency; commit blocks on slow replicas |
| **Asynchronous**   | Fast writes                           | Possible replica lag, possible data loss on master failure |
| **Quorum**         | Tunable balance via N, W, R           | Complex algorithms (Raft, Paxos)           |

Quorum rule: **W + R > N** guarantees a reader sees the latest write.

---

## 5. Distributed Transactions — Two-Phase Commit (2PC)

When a single transaction modifies data on multiple nodes, atomicity
across nodes is enforced with the **two-phase commit** protocol.

```
           Coordinator                Participants
              │
              │   ① PREPARE ────────►   prepare to commit; force log
              │                        ◄────  vote: YES / NO
              │
              │   ── if any NO → ABORT, send ROLLBACK to all ──
              │
              │   ② COMMIT  ────────►   write commit log
              │                        ◄────  ACK
```

### Properties
* **Blocking** — if the coordinator crashes after PREPARE but before
  COMMIT, participants are stuck waiting (the **coordinator failure**
  problem).
* **Three-Phase Commit (3PC)** adds an extra PRE-COMMIT round to
  reduce blocking, at the cost of more messages. Rarely used in
  practice.

### Modern alternatives
* **Paxos / Raft** for replicated state machines.
* **Optimistic** approaches like Calvin and FaunaDB's deterministic
  ordering.

---

## 6. CAP Theorem (Brewer 2000)

> In any networked shared-data system you can have at most two of:
> **Consistency**, **Availability**, **Partition tolerance**.

* In a real distributed system the network can partition → you must
  tolerate **P**.
* That leaves a choice between **C** and **A** during partitions.

| Camp         | Examples                                       |
|--------------|------------------------------------------------|
| **CP**       | HBase, MongoDB (with majority writes), ZooKeeper, etcd |
| **AP**       | Cassandra (eventual), DynamoDB, Riak           |

CAP is a **simplification** — see PACELC for the latency/consistency
trade-off when the network is healthy.

---

## 7. Query Processing in a Distributed DB

A query optimiser now considers:

* **Where the data lives** — minimise data movement.
* **Network cost** — usually the dominant term in a distributed plan.
* **Semi-join optimisation** — ship only the join key first, then
  fetch the rest, instead of shipping whole tables.
* **Parallelism** — fan a query out to all shards, merge the partial
  results centrally.

---

## 8. BASE — The Eventual-Consistency Counterpart of ACID

Many AP systems explicitly relax ACID in favour of:

| Letter | Property                       |
|--------|--------------------------------|
| **B**  | **Basically available**        |
| **S**  | **Soft state**                 |
| **E**  | **Eventual consistency**       |

Use BASE when business value of being "always on" outweighs the value
of "always consistent".

---

## 9. Sample Topology — Real-World Example

A three-region OLTP setup:

```
Region: Beijing
  - shard-A (range 0–33%): primary + 2 sync replicas
Region: Shanghai
  - shard-B (range 34–66%): primary + 2 sync replicas
Region: Guangzhou
  - shard-C (range 67–100%): primary + 2 sync replicas

Cross-region async replication for disaster recovery.
Application proxy routes by user_id hash.
```

* Within a region: CP (Raft consensus, strong consistency).
* Cross-region: AP (asynchronous, eventual consistency).

---

## 10. Exam-Style Questions

**Q1.** Which of the following is NOT one of the five "transparencies"
of a distributed DB?
A. location  B. fragmentation  C. transaction  D. replication
> Answer: **C.** (The five are location, fragmentation, replication,
> failure, concurrency. "Transaction transparency" is sometimes used
> loosely to mean atomic distributed transactions but it's not part of
> the classic five.)

**Q2.** The two-phase commit protocol can block when:
> The **coordinator crashes** between sending PREPARE and sending
> COMMIT — participants must wait for it to recover before they can
> safely commit or abort.

**Q3.** A horizontal fragmentation must satisfy three properties:
> Completeness, reconstruction, disjointness.

**Q4.** A NoSQL document store advertises "AP". During a network
partition the system will:
A. refuse all writes  B. refuse all reads  C. accept reads & writes,
risking temporary inconsistency  D. become read-only
> Answer: **C.**

**Q5.** Quorum rule for guaranteeing read-after-write consistency:
> `W + R > N`, where N = total replicas, W = write quorum, R = read
> quorum.

---

## 11. Further Reading

* Özsu & Valduriez, *Principles of Distributed Database Systems*.
* Brewer, "Towards Robust Distributed Systems", PODC keynote, 2000.
* Lamport, "The Part-Time Parliament" (Paxos), 1998.
* Ongaro & Ousterhout, "In Search of an Understandable Consensus
  Algorithm" (Raft), 2014.
