# 05 — Addressing Modes

> Syllabus reference: P57–P63
>
> An **addressing mode** determines how the CPU interprets the operand
> field of an instruction to locate the actual data. The exam tests your
> ability to identify each mode, calculate the effective address, and
> determine how many memory accesses are required.

---

## 1. What Is an Addressing Mode?

The **operand field** in an instruction does not always contain the data
itself — it may contain an address, a pointer, an offset, or a
combination. The addressing mode tells the CU **how to interpret** that
field.

```
Instruction:  OPCODE  |  operand field
                       │
                       ▼
              Addressing Mode logic
                       │
                       ▼
              Effective Address (EA) or Immediate Value
```

---

## 2. The Ten Addressing Modes

### 2.1 Immediate addressing (立即寻址)

```
Operand field = the data itself
```

| Item | Value |
|------|-------|
| EA | N/A (no memory access for operand) |
| Operand | Directly in the instruction |
| Speed | Fastest (no memory reference) |
| Range | Limited by operand field width |

> Example: `MOV AX, 5` — the value 5 is embedded in the instruction.

### 2.2 Direct addressing (直接寻址)

```
Operand field = address of the operand in memory
EA = operand field
```

| Item | Value |
|------|-------|
| EA | Operand field value |
| Memory accesses | 1 (to fetch the operand) |
| Range | Limited by address field width |

```
Instruction:  OPCODE | ADDR
                        │
                        ▼
              Memory[ADDR] → Operand
```

### 2.3 Indirect addressing (间接寻址)

```
Operand field = address of a memory location that contains the EA
EA = Memory[operand field]
```

| Item | Value |
|------|-------|
| EA | Memory[operand field] |
| Memory accesses | 2 (one for the pointer, one for the operand) |
| Advantage | Can address full memory space |

```
Instruction:  OPCODE | ADDR
                        │
                        ▼
              Memory[ADDR] → EA
                        │
                        ▼
              Memory[EA] → Operand
```

### 2.4 Register addressing (寄存器寻址)

```
Operand field = register number
Operand = Register[R]
```

| Item | Value |
|------|-------|
| EA | N/A (operand is in register) |
| Memory accesses | 0 |
| Speed | Very fast |

> Example: `MOV AX, BX` — both operands in registers.

### 2.5 Register indirect addressing (寄存器间接寻址)

```
Operand field = register number
EA = Register[R]
```

| Item | Value |
|------|-------|
| EA | Contents of the register |
| Memory accesses | 1 |

```
Instruction:  OPCODE | R
                        │
                        ▼
              Register[R] → EA
                        │
                        ▼
              Memory[EA] → Operand
```

### 2.6 Relative addressing (相对寻址)

```
EA = PC + offset (operand field is a signed displacement)
```

| Item | Value |
|------|-------|
| EA | PC + offset |
| Use | Branch/jump instructions, position-independent code |

> Exam tip: the PC has already been incremented to point to the **next**
> instruction when the offset is applied. So `EA = (PC + instruction
> length) + offset`.

### 2.7 Base addressing (基址寻址)

```
EA = Base register + offset (displacement)
```

| Item | Value |
|------|-------|
| EA | BR + offset |
| Use | Relocation, multi-segment programs |
| Key property | **Base register is managed by the OS**; user cannot modify it |

> Base addressing solves the **relocation problem**: when a program is
> loaded at a different address, only the base register changes; all
> offsets remain the same.

### 2.8 Indexed addressing (变址寻址)

```
EA = Index register + base address (operand field)
```

| Item | Value |
|------|-------|
| EA | IX + base_address |
| Use | Array traversal, loops |
| Key property | **Index register is modified by the user/program** |

> The difference from base addressing: in **base addressing** the
> register is fixed (OS-managed) and the offset varies; in **indexed
> addressing** the instruction provides a fixed base and the register
> varies.

### 2.9 Base + Indexed addressing (基址变址寻址)

```
EA = Base register + Index register + offset (optional)
```

| Item | Value |
|------|-------|
| EA | BR + IX + displacement |
| Use | Two-dimensional array access |

### 2.10 Stack addressing (堆栈寻址)

```
Operand is at the top of the stack (SP points to it)
```

| Item | Value |
|------|-------|
| EA | SP (implicit) |
| Operations | PUSH (SP−2 → SP, write), POP (read, SP+2 → SP) |

---

## 3. Comparison Table — Memorise This

| Mode | EA | Memory accesses | Speed | Typical use |
|------|----|-----------------|-------|-------------|
| Immediate | N/A | 0 | ★★★★★ | Constants |
| Register | N/A | 0 | ★★★★★ | Fast variables |
| Direct | A | 1 | ★★★★ | Simple variables |
| Register indirect | R | 1 | ★★★ | Pointers |
| Indirect | M[A] | 2 | ★★ | Pointers to pointers |
| Relative | PC+d | 1 | ★★★ | Branches |
| Base | BR+d | 1 | ★★★ | Relocation |
| Indexed | IX+A | 1 | ★★★ | Arrays |
| Base+Indexed | BR+IX+d | 1 | ★★ | 2D arrays |
| Stack | SP | 1 | ★★★ | Expression eval |

---

## 4. Base vs Indexed — The Exam Trap

| Feature | Base addressing | Indexed addressing |
|---------|----------------|-------------------|
| What varies? | Offset (displacement) | Index register |
| What is fixed? | Base register (OS) | Base address (in instruction) |
| Who changes the register? | OS only | User program |
| Purpose | Relocation | Array iteration |

> Mnemonic: **Base = Big (OS-managed), Indexed = Incrementing (user loop)**.

---

## 5. Worked Examples

**Example 1:** A computer uses 16-bit instructions with a 4-bit opcode
and a 12-bit address field. Memory is word-addressed. For direct
addressing, what is the maximum addressable memory?

```
Address field = 12 bits → 2¹² = 4096 words
```

**Example 2:** PC = 2000 (decimal). A relative branch instruction at
address 2000 has offset = +6. The instruction length is 1 word. Where
does the branch go?

```
After fetch, PC = 2001 (next instruction)
EA = 2001 + 6 = 2007
```

**Example 3:** Base register = 4000, index register = 20, displacement
= 8. What is the EA for base+indexed addressing?

```
EA = 4000 + 20 + 8 = 4028
```

---

## 6. Exam-Style Questions

**Q1.** Which addressing mode requires **no** memory access to obtain
the operand?
A. Direct  B. Register indirect  C. Immediate  D. Relative
> Answer: C (immediate — the operand is in the instruction itself).
> Note: Register addressing also requires 0 memory accesses, but the
> operand is in a register, not in the instruction.

**Q2.** In indirect addressing, the number of memory accesses to fetch
the operand is:
A. 0  B. 1  C. 2  D. 3
> Answer: C (one to read the pointer, one to read the operand).

**Q3.** Which addressing mode is best for writing position-independent
code?
A. Direct  B. Base  C. Indexed  D. Register
> Answer: B (base addressing — the OS sets the base register at load
> time; all offsets are relative).

**Q4.** In indexed addressing, who modifies the index register?
A. OS  B. Compiler  C. User program  D. Hardware automatically
> Answer: C.

**Q5.** PC = 100, offset = −5, instruction length = 2 bytes. EA = ?
> After fetch, PC = 102. EA = 102 + (−5) = 97.

**Q6.** Which addressing mode is most suitable for traversing an array?
A. Immediate  B. Direct  C. Indexed  D. Indirect
> Answer: C (increment the index register each iteration).

---

## 7. Further Reading

* Patterson & Hennessy, *Computer Organization and Design*, ch. 2.
* Stallings, *Computer Organization and Architecture*, ch. 13.

---

## 8. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Addressing mode | 寻址方式 | 05 |
| Immediate addressing | 立即寻址 | 05 |
| Direct addressing | 直接寻址 | 05 |
| Indirect addressing | 间接寻址 | 05 |
| Register addressing | 寄存器寻址 | 05 |
| Register indirect addressing | 寄存器间接寻址 | 05 |
| Relative addressing | 相对寻址 | 05 |
| Base addressing | 基址寻址 | 05 |
| Indexed addressing | 变址寻址 | 05 |
| Base + Indexed addressing | 基址变址寻址 | 05 |
| Stack addressing | 堆栈寻址 | 05 |
| Effective address (EA) | 有效地址 | 05 |
| Displacement / Offset | 偏移量 / 位移量 | 05 |
