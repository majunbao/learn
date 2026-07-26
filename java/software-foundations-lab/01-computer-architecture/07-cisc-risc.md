# 07 — CISC vs RISC

> Syllabus reference: P77–P83
>
> The **instruction set architecture (ISA)** is the contract between
> hardware and software. Two philosophical approaches emerged in the
> 1970s–80s: **CISC** (Complex Instruction Set Computer) and **RISC**
> (Reduced Instruction Set Computer). The exam tests your ability to
> compare them and understand why modern CPUs blend both.

---

## 1. CISC — Complex Instruction Set Computer

### 1.1 Philosophy

> "Hardware should do more per instruction — let the compiler's job be
> easier."

CISC designs pack complex operations into single instructions: string
operations, polynomial evaluation, loop control, etc.

### 1.2 Characteristics

| Feature | Detail |
|---------|--------|
| Instruction length | **Variable** (1–15 bytes in x86) |
| Instruction count | Many (hundreds) |
| Addressing modes | Many (10+) |
| Execution time | Varies widely (1 cycle to dozens) |
| Microprogrammed control | Common (complex decode → microcode ROM) |
| Register count | Few (x86: 8 GPRs in 32-bit mode) |
| Memory access | Memory-to-memory operations allowed |
| Emphasis | Minimise instruction count (code density) |

### 1.3 Representative: x86 / Intel

The x86 family is the quintessential CISC ISA. A single `REP MOVSB`
instruction can copy an entire string — the hardware handles the loop.

---

## 2. RISC — Reduced Instruction Set Computer

### 2.1 Philosophy

> "Simplify the hardware; let the compiler do the hard work. Simpler
> hardware runs faster."

RISC designs strip instructions down to simple, fixed-format operations
that execute in (ideally) one clock cycle.

### 2.2 Characteristics

| Feature | Detail |
|---------|--------|
| Instruction length | **Fixed** (typically 32 bits) |
| Instruction count | Few (dozens to ~100) |
| Addressing modes | Few (2–3: register, immediate, base+offset) |
| Execution time | ~1 cycle per instruction |
| Hardwired control | Common (simple decode → fast) |
| Register count | Many (32+ GPRs) |
| Memory access | **Load/Store only** — only LOAD and STORE touch memory; all arithmetic is register-to-register |
| Emphasis | Maximise instruction throughput (pipeline efficiency) |

### 2.3 Representative: ARM, MIPS, RISC-V

ARM dominates mobile/embedded; RISC-V is the open-source rising star.

---

## 3. Side-by-Side Comparison — Memorise This Table

| Feature | CISC | RISC |
|---------|------|------|
| Instruction count | Many | Few |
| Instruction length | Variable | Fixed |
| Addressing modes | Many | Few |
| Execution cycles | Variable (1–many) | ~1 |
| Control unit | Microprogrammed | Hardwired |
| Registers | Few | Many |
| Memory access | Any instruction | Load/Store only |
| Pipeline | Difficult (variable length) | Easy (fixed length) |
| Code density | High (fewer instructions) | Lower (more instructions) |
| Compiler complexity | Lower | Higher |
| Power consumption | Higher | Lower |
| Typical use | Desktop/server (x86) | Mobile/embedded (ARM) |
| Examples | x86, VAX | ARM, MIPS, RISC-V, PowerPC |

---

## 4. Why RISC Won (Sort Of)

### 4.1 The pipeline argument

RISC instructions are **uniform in size and execution time**, making
them ideal for pipelining (chapter 08). CISC's variable-length
instructions create pipeline bubbles and hazards.

### 4.2 The compiler argument

Compilers rarely use the complex CISC instructions. Studies showed that
~80% of x86 instructions used only 20% of the ISA. The complex
instructions were **wasting silicon** that could be used for caches,
more registers, or deeper pipelines.

### 4.3 The modern reality: CISC outside, RISC inside

Modern Intel/AMD CPUs are **CISC on the outside, RISC on the inside**:

```
x86 instruction (CISC)
       │
       ▼
  Decoder / Micro-op translator
       │
       ▼
  Micro-ops (RISC-like, fixed-length)
       │
       ▼
  Superscalar out-of-order pipeline (RISC-style)
```

The CPU translates x86 CISC instructions into internal **micro-ops**
(μops) that look like RISC: simple, fixed-format, register-to-register.
The pipeline then executes these μops using RISC techniques.

> Exam tip: "Modern x86 CPUs use RISC internally" is a true statement
> that appears frequently.

---

## 5. RISC Design Principles (the 5 rules)

These are the classic RISC design principles from Patterson & Hennessy:

| # | Principle | Explanation |
|---|-----------|-------------|
| 1 | **One instruction per cycle** | Simple enough to complete in one clock |
| 2 | **Register-to-register operations** | Only LOAD/STORE access memory |
| 3 | **Hardwired control** | Faster than microprogrammed |
| 4 | **Fixed instruction format** | Simplifies decode and pipeline |
| 5 | **More registers** | Reduces memory access frequency |

---

## 6. Worked Example

**Q.** Compare the code to add two arrays of 100 integers on CISC vs RISC.

**CISC (x86-like):**

```asm
MOV ECX, 100        ; counter
MOV ESI, 0          ; index
LOOP: MOV EAX, [A+ESI*4]
      ADD EAX, [B+ESI*4]
      MOV [C+ESI*4], EAX
      INC ESI
      LOOP LOOP     ; dec ECX, jump if not zero
```

**RISC (MIPS-like):**

```asm
      ADDI $t0, $zero, 100   ; counter
      ADDI $t1, $zero, 0     ; index
LOOP: LW   $t2, A($t1)       ; load A[i]
      LW   $t3, B($t1)       ; load B[i]
      ADD  $t4, $t2, $t3     ; add
      SW   $t4, C($t1)       ; store C[i]
      ADDI $t1, $t1, 4       ; index += 4
      ADDI $t0, $t0, -1      ; counter--
      BNE  $t0, $zero, LOOP  ; loop if counter ≠ 0
```

CISC uses fewer instructions (6 vs 9) but each takes more cycles.
RISC uses more instructions but each takes ~1 cycle, and the pipeline
keeps throughput high.

---

## 7. Exam-Style Questions

**Q1.** Which is a characteristic of RISC?
A. Variable instruction length  B. Microprogrammed control  C. Load/Store architecture  D. Many addressing modes
> Answer: C.

**Q2.** Modern Intel CPUs are best described as:
A. Pure CISC  B. Pure RISC  C. CISC externally, RISC internally  D. RISC externally, CISC internally
> Answer: C.

**Q3.** RISC uses hardwired control because:
A. it is cheaper  B. instructions are simple and regular  C. microcode is not available  D. it supports more instructions
> Answer: B.

**Q4.** Which of the following is NOT a RISC design principle?
A. One instruction per cycle  B. Register-to-register operations  C. Variable instruction format  D. More registers
> Answer: C.

**Q5.** CISC has ___ instructions but each takes ___ cycles compared to
RISC.
A. fewer, fewer  B. fewer, more  C. more, fewer  D. more, more
> Answer: B (fewer instructions, but each takes more cycles).

**Q6.** The "80/20 rule" in ISA design means:
> 80% of execution time is spent in 20% of the instructions. This
> observation motivated RISC: optimise the frequently-used simple
> instructions and drop the rarely-used complex ones.

---

## 8. Further Reading

* Patterson & Ditzel, "The Case for the Reduced Instruction Set
  Computer", *ACM SIGARCH*, 1980.
* Patterson & Hennessy, *Computer Organization and Design*, ch. 1 & 2.
* Hennessy & Patterson, *Computer Architecture: A Quantitative
  Approach*, Appendix K.

---

## 9. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| CISC | 复杂指令集计算机 | 07 |
| RISC | 精简指令集计算机 | 07 |
| ISA | 指令集体系结构 | 07 |
| Instruction set | 指令集 | 07 |
| Load/Store architecture | 加载/存储体系结构 | 07 |
| Micro-op (μop) | 微操作 | 07 |
| Hardwired control | 硬布线控制 | 07 |
| Microprogrammed control | 微程序控制 | 07 |
| Code density | 代码密度 | 07 |
