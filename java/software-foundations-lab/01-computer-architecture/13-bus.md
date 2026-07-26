# 13 — Bus Systems

> Syllabus reference: P142–P151
>
> A **bus** is a shared communication pathway connecting CPU, memory,
> and I/O devices. Understanding bus classification, arbitration, width,
> and bandwidth is essential for the exam and for appreciating system
> performance trade-offs.

---

## 1. What Is a Bus?

```
┌─────┐     ┌────────┐     ┌──────────┐
│ CPU │─────│ Memory │─────│ I/O Devs │
└─────┘     └────────┘     └──────────┘
     ═════════════════════════════════
                   BUS
```

A bus is a set of **parallel wires** (lines) that carry:
- **Address** — which location/device to access
- **Data** — the actual information
- **Control** — read/write, interrupt, bus request/grant, clock

---

## 2. Bus Classification

### 2.1 By function / position

| Type | Chinese | Connects | Speed | Example |
|------|---------|----------|-------|---------|
| **Internal bus** (on-chip) | 内部总线 | Components within the CPU | Very fast | ALU ↔ registers |
| **System bus** (front-side) | 系统总线 | CPU ↔ memory ↔ chipset | Fast | Address/data/control |
| **Expansion bus** | 扩展总线 | System ↔ I/O controllers | Slower | PCI, PCIe, USB |

### 2.2 By signal type (system bus)

| Bus | Chinese | Width | Direction |
|-----|---------|-------|-----------|
| **Address bus** | 地址总线 | Determines addressable space | Unidirectional (CPU → memory) |
| **Data bus** | 数据总线 | Determines transfer size per cycle | Bidirectional |
| **Control bus** | 控制总线 | Read/Write, INT, ACK, CLK, etc. | Mixed |

> Exam tip: **address bus width** determines the maximum addressable
> memory. n-bit address bus → 2ⁿ addressable locations.

### 2.3 By data transfer mode

| Type | Chinese | How | Example |
|------|---------|-----|---------|
| **Parallel bus** | 并行总线 | Multiple bits simultaneously | PCI (32/64 bits) |
| **Serial bus** | 串行总线 | One bit at a time | USB, PCIe (lane), SATA |

> Modern trend: serial buses (PCIe, SATA) have replaced parallel buses
> (PCI, PATA) because high clock rates make parallel skew and crosstalk
> harder to manage.

---

## 3. Bus Arbitration (总线仲裁)

When multiple devices want the bus simultaneously, who gets it?

### 3.1 Centralised arbitration

| Scheme | Chinese | How | Pros | Cons |
|--------|---------|-----|------|------|
| **Daisy chain** | 链式查询 | Bus grant passes from device to device in a chain; first device that needs it takes it | Simple; few lines | Unfair (devices closer to arbiter get priority); slow propagation; single point of failure |
| **Counter-based** | 计数器定时查询 | Arbiter uses a counter to select device number | More fair than daisy chain | Needs device ID lines |
| **Independent request** | 独立请求方式 | Each device has its own Bus Request + Bus Grant line | Fast; flexible priority | Most lines; complex arbiter |

### 3.2 Distributed arbitration

| Scheme | How |
|--------|-----|
| **Self-selection** | Each device places its priority number on the bus; highest number wins |
| **Collision detection** | Devices transmit; if collision, back off and retry (CSMA/CD — Ethernet) |

> Exam tip: daisy chain is the simplest but least fair. Independent
> request is the fastest but most expensive.

---

## 4. Bus Width and Bandwidth

### 4.1 Address bus width → addressable memory

```
Addressable locations = 2^(address bus width)

Example: 32-bit address bus → 2³² = 4 GB (byte-addressable)
```

### 4.2 Data bus width → transfer per cycle

```
Data per cycle = data bus width / 8 bytes

Example: 64-bit data bus → 8 bytes per cycle
```

### 4.3 Bandwidth formula

```
Bandwidth = (bus width in bytes) × bus frequency

For DDR (double data rate):
Bandwidth = (bus width in bytes) × bus frequency × 2
```

### 4.4 Worked examples

**Example 1:** A 32-bit data bus running at 100 MHz. Bandwidth?

```
= 4 bytes × 100 × 10⁶ = 400 MB/s
```

**Example 2:** A 64-bit data bus running at 800 MHz DDR. Bandwidth?

```
= 8 bytes × 800 × 10⁶ × 2 = 12,800 MB/s = 12.8 GB/s
```

**Example 3:** A system has a 24-bit address bus, byte-addressable.
Maximum memory?

```
2²⁴ = 16,777,216 bytes = 16 MB
```

---

## 5. Bus Timing

### 5.1 Synchronous bus

- Uses a **common clock** signal.
- All operations happen at clock edges.
- Simple but requires all devices to operate at the same speed.
- **Wait states** inserted for slow devices.

### 5.2 Asynchronous bus

- Uses **handshake** signals (request/acknowledge) instead of a clock.
- No common clock needed; devices can operate at different speeds.
- Three-phase handshake:

```
Master:  REQ ────────────────────────
Slave:         ───── ACK ────────────
Master:              ───── REQ off ──
Slave:                     ── ACK off
```

| Type | Pros | Cons |
|------|------|------|
| Synchronous | Simple; fast | All devices must be same speed; inflexible |
| Asynchronous | Flexible; works with mixed-speed devices | More complex; higher latency per transfer |

---

## 6. Common Bus Standards

| Bus | Type | Width | Speed | Use |
|-----|------|-------|-------|-----|
| **PCI** | Parallel | 32/64 bit | 33/66 MHz | Legacy expansion |
| **PCIe** | Serial (lanes) | ×1/×4/×8/×16 | 2.5–16 GT/s per lane | Modern expansion |
| **USB** | Serial | 1 bit | 1.5–20 Gbps | Peripheral |
| **SATA** | Serial | 1 bit | 1.5–6 Gbps | Storage |
| **I²C** | Serial | 1 bit | 100 kHz–3.4 MHz | Embedded / sensor |
| **SPI** | Serial | 1 bit | Up to ~100 MHz | Embedded / flash |

> PCIe ×16 means 16 serial lanes operating in parallel. Each lane is
> full-duplex.

---

## 7. Exam-Style Questions

**Q1.** A 20-bit address bus can address how many bytes?
A. 1 MB  B. 2 MB  C. 512 KB  D. 16 MB
> Answer: A (2²⁰ = 1,048,576 = 1 MB).

**Q2.** In daisy-chain arbitration, which device has the highest
priority?
A. The one farthest from the arbiter  B. The one closest to the arbiter  C. The one with the highest ID  D. It varies
> Answer: B.

**Q3.** A 64-bit data bus at 200 MHz has bandwidth:
A. 200 MB/s  B. 400 MB/s  C. 800 MB/s  D. 1600 MB/s
> Answer: D (8 bytes × 200 × 10⁶ = 1,600 MB/s).

**Q4.** An asynchronous bus uses ___ for coordination.
A. a clock  B. handshake signals  C. wait states  D. DMA
> Answer: B.

**Q5.** Modern systems prefer serial buses (PCIe) over parallel (PCI)
because:
A. serial is slower  B. serial avoids skew and crosstalk at high speeds  C. serial uses more wires  D. parallel is cheaper
> Answer: B.

**Q6.** Independent request arbitration requires:
A. 2 lines per device  B. 1 line per device  C. log₂(n) lines  D. 0 lines
> Answer: A (Bus Request + Bus Grant per device).

---

## 8. Further Reading

* Stallings, *Computer Organization and Architecture*, ch. 3.
* Hennessy & Patterson, *Computer Architecture: A Quantitative
  Approach*, Appendix D.

---

## 9. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Bus | 总线 | 13 |
| System bus | 系统总线 | 13 |
| Address bus | 地址总线 | 13 |
| Data bus | 数据总线 | 13 |
| Control bus | 控制总线 | 13 |
| Bus arbitration | 总线仲裁 | 13 |
| Daisy chain | 链式查询 | 13 |
| Independent request | 独立请求 | 13 |
| Synchronous bus | 同步总线 | 13 |
| Asynchronous bus | 异步总线 | 13 |
| Handshake | 握手 | 13 |
| Bandwidth | 带宽 | 13 |
| Bus width | 总线宽度 | 13 |
| PCIe | PCI Express | 13 |
