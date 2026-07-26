# 02 — Basic Units & Base Conversion

> Syllabus reference: P20–P35
>
> Before diving into data representation, you need a rock-solid grasp
> of **units of information** and **base conversion**. These are the
> building blocks for everything from memory addressing to floating-point
> encoding.

---

## 1. Units of Information

| Unit | Symbol | Size | Chinese |
|------|--------|------|---------|
| Bit | b | 0 or 1 | 位 |
| Byte | B | 8 bits | 字节 |
| Word | — | Machine-dependent (16/32/64 bits) | 字 |
| Kilobyte | KB | 2¹⁰ = 1024 B | 千字节 |
| Megabyte | MB | 2²⁰ B | 兆字节 |
| Gigabyte | GB | 2³⁰ B | 吉字节 |
| Terabyte | TB | 2⁴⁰ B | 太字节 |

> Exam trap: **K = 2¹⁰ = 1024**, not 1000. In the exam, always use
> powers of 2 unless the question explicitly says "decimal" (e.g.
> hard-disk manufacturers use 10³ = 1000).

### Bit vs Byte convention

| Context | Convention | Example |
|---------|-----------|---------|
| Storage (memory, disk) | KB, MB, GB — **binary** (2¹⁰, 2²⁰, 2³⁰) | 4 GB RAM = 2³² B |
| Network bandwidth | kbps, Mbps — **decimal** (10³, 10⁶) | 100 Mbps = 100 × 10⁶ bps |
| Hard disk capacity | GB, TB — **decimal** (10⁹, 10¹²) | 500 GB disk ≈ 465 GiB |

---

## 2. Number Systems

| Base | Name | Digits | Prefix |
|------|------|--------|--------|
| 2 | Binary | 0, 1 | `0b` or subscript ₂ |
| 8 | Octal | 0–7 | `0o` or subscript ₈ |
| 10 | Decimal | 0–9 | (no prefix) |
| 16 | Hexadecimal | 0–9, A–F | `0x` or subscript ₁₆ |

### Quick conversion table (0–15)

| Dec | Bin | Oct | Hex | Dec | Bin | Oct | Hex |
|-----|-----|-----|-----|-----|-----|-----|-----|
| 0 | 0000 | 0 | 0 | 8 | 1000 | 10 | 8 |
| 1 | 0001 | 1 | 1 | 9 | 1001 | 11 | 9 |
| 2 | 0010 | 2 | 2 | 10 | 1010 | 12 | A |
| 3 | 0011 | 3 | 3 | 11 | 1011 | 13 | B |
| 4 | 0100 | 4 | 4 | 12 | 1100 | 14 | C |
| 5 | 0101 | 5 | 5 | 13 | 1101 | 15 | D |
| 6 | 0110 | 6 | 6 | 14 | 1110 | 16 | E |
| 7 | 0111 | 7 | 7 | 15 | 1111 | 17 | F |

---

## 3. Conversion Algorithms

### 3.1 Any base → Decimal (按权展开法)

Multiply each digit by its positional weight and sum.

**Example:** `1A3₁₆ → decimal`

```
1 × 16² + A × 16¹ + 3 × 16⁰
= 1 × 256 + 10 × 16 + 3 × 1
= 256 + 160 + 3
= 419
```

**Example:** `1011.01₂ → decimal`

```
1×2³ + 0×2² + 1×2¹ + 1×2⁰ + 0×2⁻¹ + 1×2⁻²
= 8 + 0 + 2 + 1 + 0 + 0.25
= 11.25
```

### 3.2 Decimal → Any base (除基取余法 for integer, 乘基取整法 for fraction)

**Integer part:** repeatedly divide by the target base; collect remainders
in **reverse** order.

**Example:** `419 → hexadecimal`

```
419 ÷ 16 = 26 remainder 3
 26 ÷ 16 =  1 remainder A
  1 ÷ 16 =  0 remainder 1

Read remainders bottom-up: 1A3
```

**Fraction part:** repeatedly multiply by the target base; collect
integer parts in **forward** order.

**Example:** `0.6875 → binary`

```
0.6875 × 2 = 1.375  → 1
0.375  × 2 = 0.75   → 0
0.75   × 2 = 1.5    → 1
0.5    × 2 = 1.0    → 1

Read integer parts top-down: 0.1011
```

### 3.3 Binary ↔ Octal (group by 3 bits)

**Binary → Octal:** group bits from the radix point outward in groups
of 3; pad with 0s; convert each group.

```
110 101 011 . 101 100
 6   5   3    5   4
= 653.54₈
```

**Octal → Binary:** expand each octal digit to 3 bits.

### 3.4 Binary ↔ Hexadecimal (group by 4 bits)

Same idea, but groups of 4.

```
1101 0101 1011 . 1011
 D    5    B     B
= D5B.B₁₆
```

> Exam shortcut: binary ↔ octal and binary ↔ hex conversions are
> trivial grouping operations. When asked to convert between octal and
> hex, always go through binary as an intermediate — it's faster and
> less error-prone.

---

## 4. Binary Arithmetic

### 4.1 Addition

```
  1011
+ 1101
------
 11000
```

Rules: 0+0=0, 0+1=1, 1+0=1, 1+1=10 (0 carry 1).

### 4.2 Subtraction

Use two's complement (see chapter 03) or borrow method.

### 4.3 Multiplication

Shift-and-add, just like decimal long multiplication.

### 4.4 Division

Shift-and-subtract (long division in base 2).

---

## 5. Bit-Level Operations

| Operation | Symbol | Example (8-bit) |
|-----------|--------|-----------------|
| AND | `&` | `1100 1010 & 1010 0110 = 1000 0010` |
| OR | `\|` | `1100 1010 \| 1010 0110 = 1110 1110` |
| XOR | `^` | `1100 1010 ^ 1010 0110 = 0110 1100` |
| NOT | `~` | `~1100 1010 = 0011 0101` |
| Left shift | `<<` | `0000 1010 << 2 = 0010 1000` (×4) |
| Logical right shift | `>>` (fill 0) | `1010 0000 >> 3 = 0001 0100` |
| Arithmetic right shift | `>>>` (fill sign) | `1010 0000 >>> 3 = 1111 0100` |

> Exam tip: left shift by n = multiply by 2ⁿ. Right shift by n =
> divide by 2ⁿ (floor). Arithmetic right shift preserves the sign bit.

---

## 6. Worked Examples

**Example 1:** Convert `0x1F4` to binary and octal.

```
0x1F4 → binary:  0001 1111 0100
       → octal:  000 111 110 100 = 0774₈
```

**Example 2:** Convert `0.3` (decimal) to binary (6 fractional bits).

```
0.3 × 2 = 0.6 → 0
0.6 × 2 = 1.2 → 1
0.2 × 2 = 0.4 → 0
0.4 × 2 = 0.8 → 0
0.8 × 2 = 1.6 → 1
0.6 × 2 = 1.2 → 1  (repeats!)

0.3₁₀ ≈ 0.010011₂ (truncated to 6 bits)
```

> Key insight: 0.3 cannot be represented exactly in binary. This is
> why floating-point has precision issues (chapter 04).

**Example 3:** How many KB is 2²⁰ bytes?

```
2²⁰ / 2¹⁰ = 2¹⁰ = 1024 KB = 1 MB
```

---

## 7. Exam-Style Questions

**Q1.** 1 GB equals:
A. 1000 MB  B. 1024 MB  C. 1000² KB  D. 2³⁰ bits
> Answer: B (1 GB = 2³⁰ B = 2²⁰ KB = 2¹⁰ MB = 1024 MB).

**Q2.** Convert `0x3A` to octal.
> 0x3A = 0011 1010₂ = 000 111 010 = 072₈.

**Q3.** `1010 1100 >> 2` (arithmetic right shift, 8-bit):
> 1110 1011 (sign bit 1 is propagated).

**Q4.** A 32-bit address space can address how many bytes of memory?
> 2³² = 4,294,967,296 B = 4 GB.

**Q5.** Which of the following decimal numbers can be represented
**exactly** in binary?
A. 0.1  B. 0.2  C. 0.5  D. 0.3
> Answer: C (0.5 = 2⁻¹). The others have infinite binary expansions.

**Q6.** `0xFF & 0x0F` equals:
> 0x0F (masks the high nibble).

---

## 8. Further Reading

* Patterson & Hennessy, *Computer Organization and Design*, ch. 2.
* Stallings, *Computer Organization and Architecture*, ch. 9.

---

## 9. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Bit | 位 | 02 |
| Byte | 字节 | 02 |
| Word | 字 | 02 |
| Binary | 二进制 | 02 |
| Octal | 八进制 | 02 |
| Decimal | 十进制 | 02 |
| Hexadecimal | 十六进制 | 02 |
| Base conversion | 进制转换 | 02 |
| Positional weight | 位权 | 02 |
| Left shift | 左移 | 02 |
| Right shift | 右移 | 02 |
| Arithmetic shift | 算术移位 | 02 |
| Logical shift | 逻辑移位 | 02 |
| AND | 与 | 02 |
| OR | 或 | 02 |
| XOR | 异或 | 02 |
| NOT | 非 | 02 |
