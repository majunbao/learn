# 10 — Cache Memory

> Syllabus reference: P106–P118
>
> **Cache** sits between the CPU and main memory, exploiting locality to
> deliver the illusion of memory that is nearly as fast as SRAM but as
> large as DRAM. The exam heavily tests the three mapping schemes,
> replacement policies, and hit-rate calculations.

---

## 1. Cache Basics

### 1.1 The principle

```
CPU → Cache → Main Memory

If data is in cache (HIT):  return it fast
If data is not in cache (MISS): fetch from main memory, store in cache, return it
```

### 1.2 Key metrics

| Metric | Formula |
|--------|---------|
| **Hit ratio (h)** | hits / total accesses |
| **Miss ratio** | 1 − h |
| **Average access time** | h × t_cache + (1 − h) × t_main |
| **Effective access time (with cache-to-main transfer)** | h × t_cache + (1 − h) × (t_cache + t_main) |

> Exam tip: be careful about the formula. Some questions count the
> cache access time even on a miss (the CPU checks cache first), while
> others don't. Read the question carefully.

### 1.3 Worked example

Cache access time = 10 ns, main memory access time = 200 ns, hit ratio
= 90%.

```
Average access time = 0.9 × 10 + 0.1 × (10 + 200) = 9 + 21 = 30 ns
```

---

## 2. Cache-Main Memory Mapping

The central question: **which cache line can hold a given memory block?**

### Terminology

| Term | Chinese | Meaning |
|------|---------|---------|
| Block / Line | 块 / 行 | Unit of transfer between cache and main memory |
| Tag | 标记 | Identifies which memory block occupies a cache line |
| Index | 索引 | Selects a cache line/set |
| Offset | 块内偏移 | Byte offset within a block |

---

## 3. Direct Mapping (直接映射)

### 3.1 Rule

> **Block j of main memory maps to cache line (j mod C)**, where C =
> number of cache lines.

Each memory block has **exactly one** cache line it can occupy.

### 3.2 Address structure

```
┌──────────┬──────────┬──────────┐
│   Tag    │  Index   │  Offset  │
│  (t bits)│  (i bits)│  (b bits)│
└──────────┴──────────┴──────────┘

Index bits = log₂(C)
Offset bits = log₂(block size)
Tag bits = address width − index bits − offset bits
```

### 3.3 Diagram

```
Main memory block j → cache line (j mod C)

Memory block 0  ─┐
Memory block C  ─┤→ Cache line 0
Memory block 2C ─┘
Memory block 1  ─┐
Memory block C+1─┤→ Cache line 1
Memory block 2C+1─┘
...
```

### 3.4 Pros & Cons

| Pro | Con |
|-----|-----|
| Simple, fast lookup | High conflict — two frequently-used blocks that map to the same line will thrash |
| No search needed (direct index) | Low flexibility |

---

## 4. Fully Associative Mapping (全相联映射)

### 4.1 Rule

> **Any memory block can go in any cache line.**

### 4.2 Address structure

```
┌──────────┬──────────┐
│   Tag    │  Offset  │
│  (t bits)│  (b bits)│
└──────────┴──────────┘

No index bits (every line must be searched by tag)
```

### 4.3 Pros & Cons

| Pro | Con |
|-----|-----|
| No conflict misses | Must search **all** lines → expensive (comparator per line) |
| Best hit rate | Complex hardware |

---

## 5. Set-Associative Mapping (组相联映射)

### 5.1 Rule

> Cache is divided into **S sets**; each set contains **k lines**
> (k-way set-associative). Block j maps to **set (j mod S)**; within
> the set, the block can go in any of the k lines.

### 5.2 Address structure

```
┌──────────┬──────────┬──────────┐
│   Tag    │  Set Index│  Offset  │
│  (t bits)│  (s bits)│  (b bits)│
└──────────┴──────────┴──────────┘

Set index bits = log₂(S)
Offset bits = log₂(block size)
Tag bits = address width − set index bits − offset bits
```

### 5.3 Relationship to the other two

| Mapping | Equivalent set-associative |
|---------|---------------------------|
| Direct mapping | 1-way set-associative (k = 1) |
| Fully associative | C-way set-associative (k = C, S = 1) |

### 5.4 Common associativities

| k | Name | Typical use |
|---|------|------------|
| 1 | Direct mapped | L1 instruction cache (some designs) |
| 2 | 2-way | L1 data cache |
| 4 | 4-way | L2 cache |
| 8 | 8-way | L3 cache |
| C | Fully associative | TLB |

---

## 6. Comparison of the Three Mappings

| Feature | Direct | Fully Associative | Set-Associative |
|---------|--------|-------------------|-----------------|
| Where can block go? | One line only | Any line | Any line in one set |
| Search cost | None (direct index) | Search all lines | Search k lines |
| Conflict misses | High | None | Moderate |
| Hardware complexity | Low | High | Medium |
| Hit rate | Lowest | Highest | Middle |
| Tag size | Smallest | Largest | Medium |

---

## 7. Replacement Policies

When a cache miss occurs and the target set is full, which line should
be evicted?

| Policy | Chinese | How | Pros | Cons |
|--------|---------|-----|------|------|
| **RAND** | 随机替换 | Pick a random line | Simple | May evict a useful line |
| **FIFO** | 先进先出 | Evict the oldest line | Simple | May evict a frequently-used line |
| **LRU** | 最近最少使用 | Evict the line unused for the longest time | Good hit rate | Complex to track (needs counters) |
| **LFU** | 最不经常使用 | Evict the line with fewest accesses | Good for stable patterns | Doesn't adapt to changes |

> Exam tip: **LRU** is the most commonly tested and generally the best
> practical policy. For small associativity (2-way or 4-way), LRU can
> be implemented with a few bits per set.

### LRU implementation for 2-way set-associative

Only 1 bit per set: the bit indicates which way was accessed last.

### LRU implementation for 4-way set-associative

Needs ~2 bits per way or a small counter per set.

---

## 8. Write Policies

When the CPU writes to cache, when does main memory get updated?

| Policy | Chinese | On cache write hit | Consistency |
|--------|---------|-------------------|-------------|
| **Write-through** | 写直达 | Update cache AND main memory simultaneously | Always consistent; high write traffic |
| **Write-back** | 写回 | Update cache only; mark line as **dirty**; write to memory on eviction | Less traffic; stale data in memory temporarily |

| Policy | Chinese | On cache write miss | Detail |
|--------|---------|-------------------|--------|
| **Write-allocate** | 写分配 | Load block into cache, then write | Used with write-back |
| **No-write-allocate** | 非写分配 | Write directly to main memory; don't load into cache | Used with write-through |

> Common pairings: write-through + no-write-allocate; write-back +
> write-allocate.

---

## 9. Worked Examples

**Example 1:** A direct-mapped cache has 64 lines, block size = 16
bytes, 32-bit addresses. Calculate tag, index, and offset bits.

```
Offset = log₂(16) = 4 bits
Index = log₂(64) = 6 bits
Tag = 32 − 6 − 4 = 22 bits
```

**Example 2:** A 4-way set-associative cache has 256 lines total, block
size = 32 bytes, 32-bit addresses. Calculate tag, set index, offset.

```
Number of sets = 256 / 4 = 64
Offset = log₂(32) = 5 bits
Set index = log₂(64) = 6 bits
Tag = 32 − 6 − 5 = 21 bits
```

**Example 3:** A system has cache access time 20 ns, main memory access
time 200 ns. Hit ratio is 95%. What is the average access time?

```
T_avg = 0.95 × 20 + 0.05 × (20 + 200) = 19 + 11 = 30 ns
```

**Example 4:** Memory block 300 maps to which cache line in a
direct-mapped cache with 64 lines?

```
300 mod 64 = 300 − 4 × 64 = 300 − 256 = 44
→ Cache line 44
```

---

## 10. Exam-Style Questions

**Q1.** In a direct-mapped cache, two blocks that map to the same line
cause:
A. capacity miss  B. compulsory miss  C. conflict miss  D. coherence miss
> Answer: C (conflict miss).

**Q2.** A fully associative cache with 128 lines needs how many
comparators for tag matching?
A. 1  B. 7  C. 128  D. log₂(128)
> Answer: C (must compare the tag against all 128 lines in parallel).

**Q3.** A 2-way set-associative cache with 64 lines has how many sets?
A. 2  B. 32  C. 64  D. 128
> Answer: B (64 / 2 = 32 sets).

**Q4.** LRU replacement evicts the line that:
A. was loaded first  B. was accessed least recently  C. has the fewest accesses  D. is random
> Answer: B.

**Q5.** Write-back cache updates main memory:
A. on every write  B. only on eviction of a dirty line  C. never  D. only on read miss
> Answer: B.

**Q6.** A 32-bit address, 4 KB page, 64 KB cache, 64-byte block,
4-way set-associative. Tag bits = ?
> Sets = 64K / (64 × 4) = 256. Set index = 8 bits. Offset = 6 bits.
> Tag = 32 − 8 − 6 = 18 bits.

---

## 11. Further Reading

* Patterson & Hennessy, *Computer Organization and Design*, ch. 5.
* Hennessy & Patterson, *Computer Architecture: A Quantitative
  Approach*, ch. 2 (the "cache chapter" — the best in the book).

---

## 12. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Cache | 高速缓存 | 10 |
| Hit ratio | 命中率 | 10 |
| Miss ratio | 未命中率 | 10 |
| Direct mapping | 直接映射 | 10 |
| Fully associative mapping | 全相联映射 | 10 |
| Set-associative mapping | 组相联映射 | 10 |
| Tag | 标记 | 10 |
| Index | 索引 | 10 |
| Offset | 块内偏移 | 10 |
| Block / Line | 块 / 行 | 10 |
| Replacement policy | 替换策略 | 10 |
| LRU | 最近最少使用 | 10 |
| FIFO | 先进先出 | 10 |
| Write-through | 写直达 | 10 |
| Write-back | 写回 | 10 |
| Write-allocate | 写分配 | 10 |
| Dirty bit | 脏位 / 修改位 | 10 |
| Conflict miss | 冲突缺失 | 10 |
| Capacity miss | 容量缺失 | 10 |
| Compulsory miss | 强制缺失 | 10 |
