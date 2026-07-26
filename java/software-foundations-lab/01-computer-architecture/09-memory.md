# 09 — Memory Systems

> Syllabus reference: P96–P105
>
> The **memory hierarchy** is the answer to a fundamental tension: we
> want storage that is fast, large, and cheap — but you can only pick
> two. By organising memory in layers with decreasing speed and
> increasing size, the system gives the illusion of a fast, large
> memory at low cost.

---

## 1. The Memory Hierarchy

```
┌───────────────────────────────────────────────┐
│  CPU Registers        ← fastest, smallest     │
├───────────────────────────────────────────────┤
│  Cache (L1 / L2 / L3)                        │
├───────────────────────────────────────────────┤
│  Main Memory (RAM)                            │
├───────────────────────────────────────────────┤
│  Secondary Storage (SSD / HDD) ← slowest, largest │
└───────────────────────────────────────────────┘

Speed:  decreasing ↓
Cost/bit: decreasing ↓
Capacity: increasing ↑
```

### Locality of reference — why the hierarchy works

| Type | Definition | Example |
|------|-----------|---------|
| **Temporal locality** | Recently accessed data will be accessed again soon | Loop variables |
| **Spatial locality** | Data near recently accessed data will be accessed soon | Array traversal |

> The hierarchy exploits locality: cache captures temporal locality;
> cache lines (blocks) capture spatial locality.

---

## 2. Memory Classification

### 2.1 By volatility

| Type | Chinese | Retains data without power? | Example |
|------|---------|---------------------------|---------|
| **Volatile** | 易失性 | No | SRAM, DRAM |
| **Non-volatile** | 非易失性 | Yes | ROM, Flash, HDD, SSD |

### 2.2 By read/write capability

| Type | Chinese | Read | Write | Use |
|------|---------|------|-------|-----|
| **RAM** | 随机存取存储器 | Yes | Yes | Main memory |
| **ROM** | 只读存储器 | Yes | No (or limited) | Firmware, BIOS |

---

## 3. RAM — Random Access Memory

### 3.1 SRAM (Static RAM)

| Feature | Detail |
|---------|--------|
| Storage element | 6-transistor flip-flop |
| Speed | Very fast (1–10 ns) |
| Cost | High |
| Power | Low (no refresh) |
| Use | CPU cache |

### 3.2 DRAM (Dynamic RAM)

| Feature | Detail |
|---------|--------|
| Storage element | 1 transistor + 1 capacitor |
| Speed | Slower (50–70 ns) |
| Cost | Low |
| Power | Needs periodic **refresh** (every ~8 ms) |
| Use | Main memory |

> Exam tip: SRAM = fast + expensive → cache. DRAM = slow + cheap → main
> memory. The "S" in SRAM stands for "static" (no refresh); the "D" in
> DRAM stands for "dynamic" (needs refresh).

### 3.3 DRAM refresh

- **Refresh overhead**: each row must be read and rewritten periodically.
- If a DRAM has 4096 rows and each refresh takes 100 ns, total refresh
  time per cycle = 4096 × 100 ns = 409.6 μs.
- **Refresh duty cycle** = refresh time / total cycle time.

### 3.4 DRAM variants

| Variant | Feature |
|---------|---------|
| **FPM DRAM** | Fast Page Mode — reuse the same row address |
| **EDO DRAM** | Extended Data Out — overlap data output with next address |
| **SDRAM** | Synchronous — clock-driven, burst transfer |
| **DDR SDRAM** | Double Data Rate — transfer on both clock edges |
| **DDR2/3/4/5** | Higher speeds, lower voltage, wider prefetch |

> DDR transfers data on both rising and falling edges of the clock →
> 2× the throughput of SDR at the same clock frequency.

---

## 4. ROM — Read-Only Memory

| Type | Chinese | Writable? | How |
|------|---------|----------|-----|
| **Mask ROM** | 掩膜ROM | No (factory-programmed) | — |
| **PROM** | 可编程ROM | Once | Electrically (burn fuses) |
| **EPROM** | 可擦除可编程ROM | Multiple times | UV light erase |
| **EEPROM** | 电可擦除可编程ROM | Multiple times | Electrically (byte-level) |
| **Flash** | 闪存 | Multiple times | Electrically (block-level) |

> Exam tip: Flash is a type of EEPROM that erases in blocks, not
> bytes. Used in USB drives, SSDs, and BIOS chips.

---

## 5. Memory Performance Metrics

| Metric | Formula | Unit |
|--------|---------|------|
| **Access time** | Time from request to data ready | ns |
| **Cycle time** | Minimum time between two successive accesses | ns |
| **Bandwidth** | Data transferred per unit time | MB/s or GB/s |

### Bandwidth calculation

```
Bandwidth = Bus width × Frequency

Example: 64-bit bus @ 800 MHz DDR
= 8 bytes × 800 MHz × 2 = 12,800 MB/s = 12.8 GB/s
```

---

## 6. Virtual Memory (虚拟存储器)

### 6.1 Why virtual memory?

- Each process thinks it has a **contiguous, private** address space.
- Physical memory is shared and fragmented.
- The OS maps virtual addresses to physical addresses using a **page
  table**.

### 6.2 Paging

| Term | Chinese | Size |
|------|---------|------|
| **Page** | 页 (virtual) | Fixed-size block of virtual memory (4 KB typical) |
| **Frame / Page frame** | 页框 / 页帧 (physical) | Same size as a page |
| **Page table** | 页表 | Maps page number → frame number |

### 6.3 Address translation

```
Virtual address:  [Page number | Offset]
                         │
                    Page table
                         │
                         ▼
Physical address: [Frame number | Offset]
```

The **offset** bits are the same in both virtual and physical addresses.

### 6.4 TLB — Translation Lookaside Buffer

The page table is in main memory → every memory access would require
**two** memory accesses (one for the page table, one for the data).

The **TLB** is a cache for page table entries:

```
Virtual address → TLB lookup
  Hit:  get frame number directly (1 cycle)
  Miss: walk page table in memory, then cache in TLB
```

### 6.5 Page fault

When the accessed page is **not in physical memory** (on disk):

```
1. CPU generates a page fault exception
2. OS saves the process state
3. OS loads the page from disk into a free frame
4. OS updates the page table
5. OS resumes the process (re-executes the instruction)
```

> Page fault is very expensive (disk access ~ ms vs memory access ~ ns).

---

## 7. Memory-Main Memory Mapping (主存编址)

### 7.1 Addressable units

| Addressing | Addressable unit | Address bits for M bytes |
|-----------|-----------------|-------------------------|
| Byte-addressable | 1 byte | log₂(M) |
| Word-addressable | 1 word (4 bytes) | log₂(M/4) |

### 7.2 Worked example

A 32-bit system with 256 MB of byte-addressable memory:

```
Address space: 2³² = 4 GB (virtual)
Physical memory: 256 MB = 2²⁸ bytes
Physical address width: 28 bits
```

---

## 8. Worked Examples

**Example 1:** A DRAM chip has 12 address lines and 8 data lines. What
is its capacity?

```
Addressable locations = 2¹² = 4096
Data width = 8 bits = 1 byte
Capacity = 4096 × 1 byte = 4 KB
```

**Example 2:** A system uses 4 KB pages. Virtual address is 32 bits.
How many pages and how many offset bits?

```
Page size = 4 KB = 2¹² → offset = 12 bits
Page number bits = 32 − 12 = 20 bits
Number of pages = 2²⁰ = 1,048,576
```

**Example 3:** A memory has 16-bit address bus, byte-addressable. How
many 16-bit words can it store?

```
Addressable bytes = 2¹⁶ = 65,536
Words (2 bytes each) = 65,536 / 2 = 32,768
```

---

## 9. Exam-Style Questions

**Q1.** Which memory type is used for CPU cache?
A. DRAM  B. SRAM  C. ROM  D. Flash
> Answer: B (SRAM — fast, no refresh needed).

**Q2.** DRAM needs periodic refresh because:
A. it is too slow  B. capacitors leak charge  C. it uses flip-flops  D. it is volatile
> Answer: B.

**Q3.** A 64-bit data bus running at 400 MHz DDR has bandwidth:
A. 3.2 GB/s  B. 6.4 GB/s  C. 1.6 GB/s  D. 12.8 GB/s
> Answer: A (8 bytes × 400 MHz × 2 = 6,400 MB/s = 6.4 GB/s). Wait —
> 8 × 400 × 2 = 6,400 MB/s = 6.4 GB/s. Answer: B.

**Q4.** In a paging system with 4 KB pages and 32-bit virtual
addresses, the offset field is:
A. 10 bits  B. 12 bits  C. 20 bits  D. 22 bits
> Answer: B (log₂(4096) = 12).

**Q5.** TLB is a cache for:
A. data  B. instructions  C. page table entries  D. disk blocks
> Answer: C.

**Q6.** Which ROM type can be erased with UV light?
A. PROM  B. EPROM  C. EEPROM  D. Flash
> Answer: B.

---

## 10. Further Reading

* Patterson & Hennessy, *Computer Organization and Design*, ch. 5.
* Stallings, *Computer Organization and Architecture*, ch. 4–5.

---

## 11. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Memory hierarchy | 存储器层次结构 | 09 |
| SRAM | 静态随机存取存储器 | 09 |
| DRAM | 动态随机存取存储器 | 09 |
| Refresh | 刷新 | 09 |
| ROM | 只读存储器 | 09 |
| PROM | 可编程ROM | 09 |
| EPROM | 可擦除可编程ROM | 09 |
| EEPROM | 电可擦除可编程ROM | 09 |
| Flash | 闪存 | 09 |
| Virtual memory | 虚拟存储器 | 09 |
| Page | 页 | 09 |
| Frame / Page frame | 页框 / 页帧 | 09 |
| Page table | 页表 | 09 |
| TLB | 快表 / 旁路转换缓冲 | 09 |
| Page fault | 缺页 | 09 |
| Bandwidth | 带宽 | 09 |
| DDR | 双倍数据速率 | 09 |
