# 11 — Interrupts

> Syllabus reference: P119–P126
>
> An **interrupt** is a signal that causes the CPU to suspend its
> current work, save state, and execute a special handler before
> resuming. Interrupts are the foundation of multitasking, I/O, and
> exception handling. The exam tests interrupt types, processing flow,
> priority, and multiple-interrupt scenarios.

---

## 1. What Is an Interrupt?

```
Normal execution:  I1 → I2 → I3 → I4 → ...
                              │
                    Interrupt occurs
                              │
                              ▼
                    Save state (PC, PSW)
                              │
                              ▼
                    Execute interrupt handler
                              │
                              ▼
                    Restore state
                              │
                              ▼
Normal execution resumes:  I3 → I4 → ...
```

---

## 2. Interrupt Classification

### 2.1 By source

| Type | Chinese | Source | Example |
|------|---------|--------|---------|
| **Hardware interrupt** (external) | 外中断 / 硬件中断 | External device | Keyboard, timer, disk I/O completion |
| **Software interrupt** (internal) | 内中断 / 异常 / 陷入 | CPU itself | Division by zero, page fault, syscall (TRAP) |

### 2.2 By expected behaviour

| Type | Chinese | Meaning | After handling |
|------|---------|---------|---------------|
| **Fault** | 故障 | Recoverable error | Restart the **same** instruction |
| **Trap** | 陷入 / 陷阱 | Intentional (system call) | Continue with the **next** instruction |
| **Abort** | 终止 | Unrecoverable error | Terminate the process |

> Exam tip: **Fault** = restart current instruction (e.g. page fault
> after loading the page). **Trap** = continue to next instruction
> (e.g. `INT 0x80` system call). **Abort** = kill the process (e.g.
> hardware failure).

### 2.3 By maskability

| Type | Chinese | Can be disabled? | Use |
|------|---------|-----------------|-----|
| **Maskable interrupt** | 可屏蔽中断 | Yes (via interrupt enable flag) | Most device interrupts |
| **Non-maskable interrupt (NMI)** | 不可屏蔽中断 | No | Power failure, memory parity error |

---

## 3. Interrupt Processing Flow

```
1. Device raises interrupt signal
2. CPU completes current instruction
3. CPU checks interrupt enable flag (IF)
   If IF = 0 and interrupt is maskable → ignore
   If IF = 1 (or NMI) → proceed
4. CPU saves state:
   - Push PC and PSW onto stack (or to special registers)
5. CPU disables further interrupts (clear IF)
6. CPU obtains the interrupt handler address (vector)
7. CPU jumps to the handler
8. Handler executes (save additional registers, process, restore)
9. Handler executes IRET / RTI (return from interrupt)
10. CPU restores PC and PSW from stack
11. Original program resumes
```

### Simplified flow diagram

```
┌───────────────────┐
│ Execute instruction│
└────────┬──────────┘
         │
         ▼
┌───────────────────┐     No
│ Interrupt pending? ├──────────► Continue execution
└────────┬──────────┘
         │ Yes
         ▼
┌───────────────────┐
│ Save PC + PSW     │
│ Disable interrupts│
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Get vector address│
│ Jump to handler   │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Execute handler   │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ IRET: restore     │
│ PC + PSW          │
└────────┬──────────┘
         │
         ▼
    Resume program
```

---

## 4. Interrupt Vectoring

### 4.1 Vectored interrupt

Each interrupt source has a unique **interrupt vector number**. The CPU
uses this number as an index into the **interrupt vector table (IVT)**
to find the handler address.

```
Vector number n → IVT[n] → handler address
```

| Approach | How the handler address is obtained |
|----------|-------------------------------------|
| **Vectored** | Device supplies vector number; CPU looks up IVT |
| **Non-vectored** | All interrupts go to a single handler that polls devices |

> Modern systems use vectored interrupts. Non-vectored is simpler but
> slower.

### 4.2 Interrupt vector table (IVT)

| System | IVT location | Entry size |
|--------|-------------|-----------|
| x86 (real mode) | Address 0 | 4 bytes (CS:IP) |
| x86 (protected mode) | IDTR points to IDT | 8 bytes (gate descriptor) |
| ARM | Vector table at 0x00000000 or 0xFFFF0000 | 4 bytes (branch instruction) |

---

## 5. Multiple Interrupts — Priority

When multiple interrupts arrive simultaneously (or a new interrupt
arrives while handling another), the CPU must decide which to handle
first.

### 5.1 Two strategies

| Strategy | Chinese | How |
|----------|---------|-----|
| **Sequential (single-level)** | 单重中断 / 顺序处理 | Disable interrupts while handling; queue new ones until handler finishes |
| **Nested (multi-level)** | 多重中断 / 嵌套处理 | Allow higher-priority interrupts to preempt the current handler |

### 5.2 Priority rules

- Higher-priority interrupts can preempt lower-priority handlers.
- Same-priority or lower-priority interrupts must wait.

### 5.3 Typical priority order (high to low)

```
1. Machine check / NMI        (highest)
2. Page fault / virtualization
3. Clock / timer
4. Disk I/O
5. Network
6. Keyboard / mouse           (lowest)
```

### 5.4 Timing diagrams

**Single-level (sequential):**

```
Main: ────[I1]──────────────────────────────────[I2]────
              │                              │
Int A:        └────[Handler A]──────────────┘
                    │
Int B:              └──(queued)──[Handler B]──┘
```

**Multi-level (nested):**

```
Main: ────[I1]──────────────────────────────────[I2]────
              │                              │
Int A:        └────[Handler A]─────┘         │
                    │              │
Int B:              └──[Handler B]─┘         │
                         │
Int C:                   └[Handler C]┘
```

---

## 6. Interrupt vs Polling

| Feature | Interrupt | Polling |
|---------|-----------|---------|
| CPU involvement | Passive (CPU is notified) | Active (CPU repeatedly checks) |
| Efficiency | High (CPU does other work) | Low (wastes cycles) |
| Response time | Fast (immediate on signal) | Variable (depends on poll interval) |
| Hardware complexity | Higher (interrupt controller) | Lower |
| Best for | Infrequent, unpredictable events | Frequent, predictable events |

---

## 7. Worked Examples

**Example 1:** A system handles interrupts in the order: NMI > Timer >
Disk > Keyboard. Timer interrupt arrives while handling Disk interrupt.
What happens?

```
Timer has higher priority than Disk → Timer preempts Disk handler.
After Timer handler finishes, Disk handler resumes.
```

**Example 2:** In a single-level interrupt system, a keyboard interrupt
arrives while handling a timer interrupt. What happens?

```
Single-level: interrupts are disabled during handler.
Keyboard interrupt is queued until timer handler finishes (IRET).
Then keyboard interrupt is processed.
```

**Example 3:** An interrupt handler takes 50 μs. A device generates
interrupts at 10 kHz. Can the system keep up?

```
Interrupt rate = 10,000/s → one every 100 μs
Handler time = 50 μs < 100 μs → Yes, the system can keep up.
CPU utilisation for interrupts = 50/100 = 50%
```

---

## 8. Exam-Style Questions

**Q1.** A page fault is classified as:
A. external interrupt  B. trap  C. fault  D. abort
> Answer: C (fault — the instruction is restarted after the page is
> loaded).

**Q2.** During interrupt handling, the CPU automatically saves:
A. all registers  B. PC and PSW  C. only PC  D. only the accumulator
> Answer: B (PC and PSW are saved automatically; other registers are
> saved by the handler software).

**Q3.** A non-maskable interrupt (NMI):
A. can be disabled by clearing IF  B. cannot be disabled  C. is always lowest priority  D. is generated by software
> Answer: B.

**Q4.** In nested interrupt handling, a higher-priority interrupt can:
A. never preempt  B. always preempt  C. preempt a lower-priority handler  D. only preempt after IRET
> Answer: C.

**Q5.** The interrupt vector table stores:
A. interrupt data  B. device status  C. handler addresses  D. interrupt priorities
> Answer: C.

**Q6.** After a TRAP (system call), execution resumes at:
A. the same instruction  B. the next instruction  C. the handler  D. the beginning of the program
> Answer: B (trap continues with the next instruction).

---

## 9. Further Reading

* Patterson & Hennessy, *Computer Organization and Design*, ch. 5.
* Stallings, *Computer Organization and Architecture*, ch. 1 & 8.

---

## 10. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Interrupt | 中断 | 11 |
| Hardware interrupt | 外中断 / 硬件中断 | 11 |
| Software interrupt | 内中断 / 异常 | 11 |
| Fault | 故障 | 11 |
| Trap | 陷入 / 陷阱 | 11 |
| Abort | 终止 | 11 |
| Maskable interrupt | 可屏蔽中断 | 11 |
| Non-maskable interrupt (NMI) | 不可屏蔽中断 | 11 |
| Interrupt vector | 中断向量 | 11 |
| Interrupt vector table (IVT) | 中断向量表 | 11 |
| Interrupt handler | 中断服务程序 | 11 |
| Nested interrupt | 多重中断 / 嵌套中断 | 11 |
| IRET / RTI | 中断返回 | 11 |
| Interrupt enable flag (IF) | 中断允许标志 | 11 |
