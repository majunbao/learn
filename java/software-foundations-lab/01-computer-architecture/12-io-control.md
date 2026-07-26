# 12 — I/O Control Methods

> Syllabus reference: P127–P141
>
> How does the CPU communicate with external devices? Four methods
> evolved over time, each reducing CPU involvement further: **programmed
> I/O**, **interrupt-driven I/O**, **DMA**, and **channel I/O**. The
> exam tests your ability to compare them and calculate CPU utilisation.

---

## 1. The Four Methods — Overview

```
CPU involvement:  HIGH ◄────────────────────────► LOW
                 Programmed → Interrupt → DMA → Channel
Speed:           SLOW ◄──────────────────────────► FAST
Complexity:      LOW ◄───────────────────────────► HIGH
```

| Method | Chinese | CPU role | Data path |
|--------|---------|----------|-----------|
| **Programmed I/O** | 程序查询方式 | Polls device; moves every byte | Device → CPU → Memory |
| **Interrupt-driven I/O** | 中断驱动方式 | Interrupt per byte/word | Device → CPU → Memory |
| **DMA** | 直接存储器存取 | Sets up transfer; CPU idle during block transfer | Device → Memory (direct) |
| **Channel I/O** | 通道方式 | Issues channel program; CPU completely free | Device → Memory (via channel) |

---

## 2. Programmed I/O (程序查询方式)

### 2.1 How it works

```
1. CPU writes command to device control register
2. CPU loops, reading device status register
3. When device is ready, CPU reads/writes data register
4. Repeat for each byte/word
```

### 2.2 Flow diagram

```
        ┌──────────────┐
        │ Issue command │
        └──────┬───────┘
               │
        ┌──────▼───────┐
   ┌──►│ Read status   │
   │   └──────┬───────┘
   │          │
   │   ┌──────▼───────┐    No
   │   │ Ready?       ├────────┐
   │   └──────┬───────┘        │
   │          │ Yes            │
   │   ┌──────▼───────┐        │
   │   │ Read/write   │        │
   │   │ data         │        │
   │   └──────┬───────┘        │
   │          │                │
   │   ┌──────▼───────┐        │
   │   │ Done?        ├─── No ─┘
   │   └──────┬───────┘
   │          │ Yes
   └──────────┘
```

### 2.3 Pros & Cons

| Pro | Con |
|-----|-----|
| Simple hardware | CPU wastes 100% of time polling |
| | CPU cannot do other work |
| | Slow response |

---

## 3. Interrupt-Driven I/O (中断驱动方式)

### 3.1 How it works

```
1. CPU issues I/O command
2. CPU goes on to do other work
3. Device interrupts CPU when ready
4. CPU transfers one byte/word in the interrupt handler
5. If more data needed, go to step 2
```

### 3.2 Pros & Cons

| Pro | Con |
|-----|-----|
| CPU is free between interrupts | Still one interrupt per byte/word → high overhead for large transfers |
| Better CPU utilisation | Context switch overhead |

---

## 4. DMA — Direct Memory Access (直接存储器存取)

### 4.1 How it works

```
1. CPU programs the DMA controller:
   - Source address (device)
   - Destination address (memory)
   - Transfer count (number of bytes/words)
   - Direction (read/write)
2. CPU continues other work
3. DMA controller transfers data directly between device and memory
4. DMA steals bus cycles from CPU (cycle stealing)
5. When transfer count reaches 0, DMA interrupts CPU (one interrupt per block)
```

### 4.2 DMA controller structure

```
┌─────────────────────────────────────┐
│           DMA Controller            │
│  ┌──────────┐  ┌─────────────────┐ │
│  │ Memory   │  │ Device          │ │
│  │ Address  │  │ Address/Control │ │
│  │ Register │  │ Register        │ │
│  ├──────────┤  ├─────────────────┤ │
│  │ Count    │  │ Control/Status  │ │
│  │ Register │  │ Register        │ │
│  └──────────┘  └─────────────────┘ │
└─────────────────────────────────────┘
```

### 4.3 Bus arbitration modes

| Mode | Chinese | How | CPU impact |
|------|---------|-----|-----------|
| **Cycle stealing** | 周期窃取 | DMA takes one bus cycle per transfer | CPU paused for 1 cycle; minimal impact |
| **Burst mode** | 突发模式 | DMA takes the bus for an entire block transfer | CPU paused for entire block; faster DMA |
| **Transparent mode** | 透明模式 | DMA uses bus only when CPU doesn't need it | No CPU impact; complex; slower DMA |

### 4.4 Pros & Cons

| Pro | Con |
|-----|-----|
| CPU involvement only at start and end | DMA controller hardware needed |
| One interrupt per block (not per byte) | Bus contention with CPU |
| Much higher throughput | Cannot handle complex I/O operations |

---

## 5. Channel I/O (通道方式)

### 5.1 How it works

A **channel** is a dedicated I/O processor that executes **channel
programs** (sequences of channel commands) independently of the CPU.

```
1. CPU prepares a channel program in memory
2. CPU issues START I/O instruction to the channel
3. Channel executes the program autonomously
4. Channel interrupts CPU when done
```

### 5.2 Channel types

| Type | Chinese | Speed | Connected devices |
|------|---------|-------|-------------------|
| **Byte multiplexer channel** | 字节多路通道 | Low | Many slow devices (terminals, printers) |
| **Block multiplexer channel** | 数组多路通道 | Medium | Medium-speed devices (tapes) |
| **Selector channel** | 选择通道 | High | One fast device at a time (disks) |

### 5.3 Channel vs DMA

| Feature | DMA | Channel |
|---------|-----|---------|
| Intelligence | Simple data mover | I/O processor (executes programs) |
| Commands | Single transfer | Channel program (multiple commands) |
| CPU involvement | Set up transfer | Set up channel program |
| Flexibility | Low | High |
| Cost | Lower | Higher |
| Mainframe use | No | Yes (IBM mainframes) |

---

## 6. CPU Utilisation Calculations

### 6.1 Programmed I/O

```
CPU utilisation for I/O = 100% (CPU is always busy polling)
Effective CPU utilisation for other work = 0%
```

### 6.2 Interrupt-driven I/O

```
Interrupt overhead per byte = t_handler
Total I/O time = n × t_handler + n × t_device
CPU utilisation for other work = (total time − interrupt overhead) / total time
```

### 6.3 DMA

```
DMA setup time = t_setup (once per block)
Cycle stealing overhead = n × t_cycle (one cycle per byte/word)
CPU utilisation = 1 − (t_setup + n × t_cycle) / total_transfer_time
```

### 6.4 Worked example

A device transfers 1000 bytes. Device speed = 1 byte/μs. DMA cycle
steal time = 0.1 μs per byte. DMA setup time = 5 μs. What fraction of
CPU time is stolen?

```
Total transfer time = 1000 × 1 = 1000 μs
DMA overhead = 5 + 1000 × 0.1 = 105 μs
CPU time stolen = 105 / 1000 = 10.5%
```

---

## 7. Comparison Summary — Memorise This

| Feature | Programmed I/O | Interrupt I/O | DMA | Channel |
|---------|---------------|---------------|-----|---------|
| CPU involvement per byte | Full (poll) | Interrupt handler | None (cycle steal) | None |
| Interrupts per block | 0 | n (one per byte) | 1 | 1 |
| Data path | Dev→CPU→Mem | Dev→CPU→Mem | Dev→Mem | Dev→Mem |
| CPU utilisation | Worst | Moderate | Good | Best |
| Hardware cost | Lowest | Low | Medium | Highest |
| Suitable for | Simple systems | Low-speed devices | Block devices | Mainframes |

---

## 8. Exam-Style Questions

**Q1.** In programmed I/O, the CPU:
A. is interrupted when data is ready  B. continuously polls the device  C. uses DMA  D. is completely free
> Answer: B.

**Q2.** DMA transfers data between:
A. CPU and memory  B. device and CPU  C. device and memory  D. two devices
> Answer: C (device ↔ memory, bypassing the CPU).

**Q3.** In DMA cycle stealing, the CPU is paused for:
A. the entire block transfer  B. one bus cycle per byte/word  C. no time at all  D. one instruction
> Answer: B.

**Q4.** A channel is different from DMA because a channel:
A. is slower  B. can execute channel programs  C. uses more interrupts  D. cannot access memory
> Answer: B.

**Q5.** A device transfers 512 bytes at 2 MB/s using interrupt-driven
I/O. Each interrupt takes 20 μs. CPU overhead = ?
```
Transfer time = 512 / (2 × 10⁶) = 256 μs
Interrupts = 512 (one per byte)
Interrupt overhead = 512 × 20 = 10,240 μs
Total = 256 + 10,240 = 10,496 μs
CPU overhead = 10,240 / 10,496 ≈ 97.6%
```

**Q6.** Which I/O method has the lowest CPU utilisation for I/O?
A. Programmed I/O  B. Interrupt I/O  C. DMA  D. Channel I/O
> Answer: A (CPU is 100% occupied with polling).

---

## 9. Further Reading

* Stallings, *Computer Organization and Architecture*, ch. 7.
* Patterson & Hennessy, *Computer Organization and Design*, ch. 5 & 6.

---

## 10. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Programmed I/O | 程序查询方式 | 12 |
| Interrupt-driven I/O | 中断驱动方式 | 12 |
| DMA | 直接存储器存取 | 12 |
| Channel I/O | 通道方式 | 12 |
| Cycle stealing | 周期窃取 | 12 |
| Burst mode | 突发模式 | 12 |
| DMA controller | DMA控制器 | 12 |
| Channel program | 通道程序 | 12 |
| Selector channel | 选择通道 | 12 |
| Byte multiplexer channel | 字节多路通道 | 12 |
| Block multiplexer channel | 数组多路通道 | 12 |
