# 03 — Computer Architecture

> 16 chapters covering the complete computer-architecture section of the
> Chinese software engineer exam syllabus (P2–P186), rewritten in
> textbook-level depth. Each chapter is self-contained: theory →
> worked examples → exam-style Q&A → further reading.

## Roadmap

| #  | File                                              | Syllabus  | Topic |
|----|---------------------------------------------------|-----------|-------|
| 01 | [`01-cpu.md`](01-cpu.md)                         | P2–P19   | CPU structure, ALU, CU, registers, instruction cycle |
| 02 | [`02-units-and-bases.md`](02-units-and-bases.md) | P20–P35  | Basic units, binary/octal/hex conversions, bit-level operations |
| 03 | [`03-encoding.md`](03-encoding.md)               | P36–P45  | Sign-magnitude, one's complement, two's complement, excess/shifted code |
| 04 | [`04-floating-point.md`](04-floating-point.md)   | P46–P56  | IEEE 754, normalisation, arithmetic, precision |
| 05 | [`05-addressing.md`](05-addressing.md)           | P57–P63  | Instruction addressing modes: immediate, direct, indirect, indexed, etc. |
| 06 | [`06-error-codes.md`](06-error-codes.md)         | P64–P76  | Parity, Hamming code, CRC |
| 07 | [`07-cisc-risc.md`](07-cisc-risc.md)             | P77–P83  | CISC vs RISC philosophy, comparison |
| 08 | [`08-pipeline.md`](08-pipeline.md)               | P84–P95  | Pipeline stages, throughput, hazards, superscalar |
| 09 | [`09-memory.md`](09-memory.md)                   | P96–P105 | Memory hierarchy, ROM/RAM, cache-main mapping, virtual memory |
| 10 | [`10-cache.md`](10-cache.md)                     | P106–P118| Cache mapping (direct/fully/set-associative), replacement, write policies |
| 11 | [`11-interrupt.md`](11-interrupt.md)             | P119–P126| Interrupt types, processing flow, priority, multiple interrupts |
| 12 | [`12-io-control.md`](12-io-control.md)           | P127–P141| Programmed I/O, interrupt-driven, DMA, channel I/O |
| 13 | [`13-bus.md`](13-bus.md)                         | P142–P151| Bus classification, arbitration, width, bandwidth |
| 14 | [`14-security.md`](14-security.md)               | P152–P168| Security levels, threats, access control, firewall |
| 15 | [`15-encryption.md`](15-encryption.md)           | P169–P179| Symmetric, asymmetric, hash, digital signature, PKI |
| 16 | [`16-reliability.md`](16-reliability.md)         | P180–P186| Reliability metrics, series/parallel systems, RAS |

## Suggested Reading Order

The chapter numbering is the recommended order. A few alternative
study paths:

- **Data representation crammer**: 02 → 03 → 04 → 06.
- **CPU & instruction path**: 01 → 05 → 07 → 08.
- **Memory subsystem**: 09 → 10 → 11 → 12 → 13.
- **Security & reliability**: 14 → 15 → 16.

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
