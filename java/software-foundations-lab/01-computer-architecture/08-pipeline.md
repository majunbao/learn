# 08 — Pipelining

> Syllabus reference: P84–P95
>
> **Pipelining** is the single most important performance technique in
> modern CPUs. Like an assembly line, it overlaps the execution of
> multiple instructions so that the CPU completes one instruction per
> cycle (in the ideal case). The exam tests pipeline timing, throughput
> calculation, hazard identification, and superscalar concepts.

---

## 1. The Assembly-Line Analogy

```
Without pipeline (sequential):
  I1: [F][D][E][W]
  I2:                [F][D][E][W]
  I3:                              [F][D][E][W]
  Time: 12 cycles for 3 instructions

With 4-stage pipeline:
  I1: [F][D][E][W]
  I2:    [F][D][E][W]
  I3:       [F][D][E][W]
  Time: 6 cycles for 3 instructions
```

Each stage works on a different instruction simultaneously, just like
stations on an assembly line.

---

## 2. Standard Pipeline Stages

| Stage | Name | Chinese | Action |
|-------|------|---------|--------|
| **F** | Fetch | 取指 | Read instruction from memory (PC → MAR → MDR → IR) |
| **D** | Decode | 译码 / 分析 | Decode opcode; read register operands |
| **E** | Execute | 执行 | ALU operation or address calculation |
| **W** | Write back | 写回 | Write result to register or memory |

Some ISAs split this into 5 stages (add a Memory access stage M between
E and W for LOAD/STORE). The exam uses either 4 or 5 stages.

### 5-stage RISC pipeline (MIPS-style)

```
F → D → E → M → W
```

| Stage | Action |
|-------|--------|
| IF (Fetch) | Fetch instruction from instruction cache |
| ID (Decode) | Decode; read registers |
| EX (Execute) | ALU op / branch resolution / address calc |
| MEM | Access data memory (LOAD/STORE only) |
| WB (Write-back) | Write result to register file |

---

## 3. Pipeline Performance Formulas

### 3.1 Throughput

```
Throughput = instructions / time
```

### 3.2 Execution time for n instructions on a k-stage pipeline

```
T_pipeline = k × Δt + (n − 1) × Δt
```

Where Δt = clock cycle time (determined by the **slowest** stage).

### 3.3 Speedup

```
Speedup = T_sequential / T_pipeline
        = n × k × Δt / (k × Δt + (n − 1) × Δt)
        = n × k / (k + n − 1)

As n → ∞: Speedup → k
```

> Theoretical maximum speedup = number of pipeline stages k.

### 3.4 Worked example

A 5-stage pipeline with Δt = 1 ns. How long for 100 instructions?

```
T = 5 × 1 + (100 − 1) × 1 = 104 ns
Throughput = 100 / 104 ≈ 0.96 instructions/ns
Speedup = 500 / 104 ≈ 4.81× (close to theoretical max of 5×)
```

---

## 4. Pipeline Hazards

Hazards prevent the next instruction from executing in its designated
cycle. Three types:

### 4.1 Structural hazard (结构冲突 / 资源冲突)

Two instructions need the **same hardware resource** in the same cycle.

| Cause | Example |
|-------|---------|
| Single memory port | IF and MEM stages both need memory access simultaneously |
| Single ALU | Two instructions need ALU in the same cycle |

**Solution:** Separate instruction cache and data cache (Harvard
architecture); duplicate functional units.

### 4.2 Data hazard (数据冲突)

An instruction depends on the **result of a prior instruction** that
has not yet completed.

| Type | Pattern | Example |
|------|---------|---------|
| **RAW** (Read After Write) — true dependence | I1 writes, I2 reads | `ADD R1, R2, R3` then `SUB R4, R1, R5` |
| **WAR** (Write After Read) — anti-dependence | I1 reads, I2 writes | Not a problem in in-order pipelines |
| **WAW** (Write After Write) — output dependence | Both write same register | Not a problem in in-order pipelines |

> RAW is the most common and important hazard. WAR and WAW only matter
> in out-of-order execution.

**Solutions for RAW:**

| Solution | How | Cost |
|----------|-----|------|
| **Stall (bubble)** | Insert NOP cycles until data is ready | Wastes cycles |
| **Forwarding / bypassing** | Route result directly from EX/MEM/WB to EX input | Hardware; eliminates most stalls |
| **Compiler scheduling** | Reorder instructions to separate dependent ops | Software; no hardware cost |

### 4.3 Control hazard (控制冲突)

A **branch instruction** changes the flow; the pipeline may have fetched
the wrong path.

**Solutions:**

| Solution | How | Trade-off |
|----------|-----|-----------|
| **Stall** | Wait until branch resolved | Simple but slow (2–3 cycle penalty) |
| **Predict not taken** | Assume branch not taken; flush if wrong | Good for loops (taken most of the time → bad) |
| **Predict taken** | Assume branch taken | Good for loops |
| **Delayed branch** | Fill the branch delay slot with a useful instruction | Requires compiler support |
| **Branch prediction (dynamic)** | 1-bit / 2-bit predictor, BTB | Most effective; used in modern CPUs |

### 4.4 Branch prediction accuracy

| Predictor | Accuracy | Mechanism |
|-----------|----------|-----------|
| Static (always not taken) | ~50–60% | No state |
| 1-bit BHT | ~85% | Remember last outcome |
| 2-bit saturating counter | ~90%+ | Need 2 consecutive misses to change prediction |

---

## 5. Superscalar Pipeline (超标量)

A superscalar CPU has **multiple execution units** and can issue **more
than one instruction per cycle**.

```
           ┌─→ ALU1 ──┐
Fetch → Decode ─→ ALU2 ──┤──→ Write-back
           ├─→ FPU  ──┤
           └─→ LSU  ──┘

Issue width: 2, 4, 6, or more instructions per cycle
```

| Feature | Scalar pipeline | Superscalar |
|---------|----------------|-------------|
| Instructions per cycle (IPC) | ≤ 1 | > 1 (theoretical) |
| Execution units | 1 each | Multiple |
| Issue rate | 1 per cycle | 2–6 per cycle |
| Complexity | Moderate | High (dependency checking, renaming) |

---

## 6. Pipeline Timing Diagrams — How to Draw Them

### Example: 5-stage pipeline, 3 instructions, no hazards

```
Cycle:  1   2   3   4   5   6   7
I1:     IF  ID  EX  MEM WB
I2:         IF  ID  EX  MEM WB
I3:             IF  ID  EX  MEM WB
```

### Example: RAW hazard with 1-cycle stall

```
I1: ADD R1, R2, R3    IF  ID  EX  MEM WB
I2: SUB R4, R1, R5        IF  ID  stall  EX  MEM WB
I3: AND R6, R7, R8            IF  stall  ID  EX  MEM WB
```

With forwarding, the stall is eliminated:

```
I1: ADD R1, R2, R3    IF  ID  EX  MEM WB
I2: SUB R4, R1, R5        IF  ID  EX  MEM WB  (R1 forwarded from EX→EX)
I3: AND R6, R7, R8            IF  ID  EX  MEM WB
```

---

## 7. Worked Examples

**Example 1:** A 4-stage pipeline has stage times 80ns, 70ns, 90ns,
80ns. What is the clock cycle time and throughput?

```
Cycle time = max(80, 70, 90, 80) = 90 ns
Throughput = 1 / 90 ns ≈ 11.1 MIPS (at 1 instruction/cycle steady state)
```

**Example 2:** 10 instructions on a 5-stage pipeline with 2 data
hazards, each causing 2-cycle stalls. Total time?

```
Without hazards: 5 + 9 = 14 cycles
With 2 stalls × 2 cycles = 4 extra cycles
Total = 14 + 4 = 18 cycles
```

**Example 3:** A branch is taken 80% of the time. Each misprediction
costs 3 cycles. What is the average branch penalty with "predict not
taken"?

```
Misprediction rate = 80% (branch is taken but we predicted not taken)
Average penalty = 0.8 × 3 = 2.4 cycles per branch
```

---

## 8. Exam-Style Questions

**Q1.** A 5-stage pipeline processes 200 instructions. The total
execution time is:
A. 200 cycles  B. 204 cycles  C. 1000 cycles  D. 205 cycles
> Answer: B (5 + 199 = 204 cycles, assuming no hazards).

**Q2.** Which hazard is caused by a branch instruction?
A. Structural  B. Data RAW  C. Control  D. Data WAR
> Answer: C.

**Q3.** Forwarding (bypassing) eliminates most ___ hazards.
A. structural  B. control  C. RAW data  D. all
> Answer: C.

**Q4.** The clock cycle time of a pipeline is determined by:
A. the fastest stage  B. the slowest stage  C. the average stage time  D. the number of stages
> Answer: B.

**Q5.** A superscalar processor with issue width 4 can theoretically
complete:
A. 1 instruction per cycle  B. 2  C. 4  D. 8
> Answer: C (4 instructions per cycle at most).

**Q6.** In a 5-stage pipeline, the speedup for a very large number of
instructions approaches:
A. 3  B. 4  C. 5  D. ∞
> Answer: C (speedup → k = 5 as n → ∞).

---

## 9. Further Reading

* Patterson & Hennessy, *Computer Organization and Design*, ch. 4.
* Hennessy & Patterson, *Computer Architecture: A Quantitative
  Approach*, ch. 3.
* Kogge, *The Architecture of Pipelined Computers*, 1981.

---

## 10. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Pipeline | 流水线 | 08 |
| Pipeline stage | 流水段 / 流水级 | 08 |
| Throughput | 吞吐率 | 08 |
| Speedup | 加速比 | 08 |
| Structural hazard | 结构冲突 | 08 |
| Data hazard | 数据冲突 | 08 |
| Control hazard | 控制冲突 | 08 |
| RAW | 写后读 (真相关) | 08 |
| WAR | 读后写 (反相关) | 08 |
| WAW | 写后写 (输出相关) | 08 |
| Forwarding / Bypassing | 转发 / 旁路 | 08 |
| Stall / Bubble | 暂停 / 气泡 | 08 |
| Branch prediction | 分支预测 | 08 |
| Delayed branch | 延迟分支 | 08 |
| Superscalar | 超标量 | 08 |
| Issue width | 发射宽度 | 08 |
