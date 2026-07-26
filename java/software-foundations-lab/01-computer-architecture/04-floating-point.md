# 04 — Floating-Point Numbers

> Syllabus reference: P46–P56
>
> Floating-point representation lets us express a huge range of values
> — from atomic scales to astronomical — in a fixed number of bits.
> The **IEEE 754** standard is the universal format; mastering it is
> essential for the exam and for understanding numerical computing.

---

## 1. The General Floating-Point Format

A floating-point number has three parts:

```
N = (−1)^S × M × R^E

S = Sign      (0 or 1)
M = Mantissa  (significand / 尾数)
E = Exponent  (阶码)
R = Radix     (base, usually 2)
```

In memory layout:

```
┌─────┬──────────────┬───────────────────────────────┐
│  S  │   Exponent   │          Mantissa             │
│ 1bit│   E bits     │          M bits               │
└─────┴──────────────┴───────────────────────────────┘
 MSB                                                  LSB
```

---

## 2. IEEE 754 Standard

### 2.1 Two basic formats

| Format | Total bits | Sign | Exponent | Mantissa | Bias |
|--------|-----------|------|----------|----------|------|
| **Single (float32)** | 32 | 1 | 8 | 23 | 127 |
| **Double (float64)** | 64 | 1 | 11 | 52 | 1023 |

### 2.2 Normalised numbers

The mantissa has an **implicit leading 1** (hidden bit), so the
actual significand is `1.MMMMM...`.

**Value = (−1)^S × 1.M × 2^(E−bias)**

> The hidden bit gives one extra bit of precision for free — 23 stored
> mantissa bits actually represent 24 bits of precision.

### 2.3 Special values

| Exponent (E) | Mantissa (M) | Meaning |
|-------------|-------------|---------|
| 0 | 0 | **±0** (signed zero) |
| 0 | ≠ 0 | **Denormalised** (subnormal) number: (−1)^S × 0.M × 2^(1−bias) |
| 1…254 (single) | any | **Normalised** number |
| 255 (single) | 0 | **±Infinity** |
| 255 (single) | ≠ 0 | **NaN** (Not a Number) |

### 2.4 Denormalised numbers

When E = 0 and M ≠ 0, the implicit leading bit is **0** instead of 1,
and the exponent is `1 − bias` (not `0 − bias`). This provides a
gradual underflow from the smallest normalised number toward zero.

| Format | Smallest normalised | Smallest denormalised |
|--------|--------------------|-----------------------|
| Single | 2^(−126) ≈ 1.18×10⁻³⁸ | 2^(−149) ≈ 1.40×10⁻⁴⁵ |
| Double | 2^(−1022) ≈ 2.23×10⁻³⁰⁸ | 2^(−1074) ≈ 4.94×10⁻³²⁴ |

---

## 3. IEEE 754 Encoding — Step by Step

### Algorithm

```
1. Determine the sign bit S (0 for +, 1 for −).
2. Convert the absolute value to binary.
3. Normalise: write as 1.xxxxx × 2^e.
4. Compute E = e + bias.
5. Store S, E (as 8/11-bit unsigned), and the fractional part of
   the mantissa (drop the leading 1).
```

### Worked example: Encode −6.625 as IEEE 754 single

```
Step 1: S = 1 (negative)

Step 2: 6.625 → binary
  6 = 110
  0.625 = 0.101  (0.5 + 0.125)
  = 110.101

Step 3: Normalise
  110.101 = 1.10101 × 2²

Step 4: E = 2 + 127 = 129 = 1000 0001

Step 5: Mantissa (drop leading 1) = 10101 → padded to 23 bits:
  101 0100 0000 0000 0000 0000

Result:
  1  1000 0001  101 0100 0000 0000 0000 0000
  S  Exponent   Mantissa

Hex: 0xC0D40000
```

### Worked example: Decode IEEE 754 single `0x42E48000`

```
Binary: 0 10000101 11001001000000000000000

S = 0 (positive)
E = 1000 0101 = 133
e = 133 − 127 = 6
M = 1.1100100100... (add implicit 1)

Value = 1.11001001 × 2⁶
      = 1110010.01
      = 114.25
```

---

## 4. Floating-Point Normalisation (通用浮点数规格化)

The exam also covers **generic** (non-IEEE 754) floating-point formats.
The normalisation rules differ by encoding:

| Mantissa encoding | Normalisation rule | Mantissa range |
|-------------------|-------------------|---------------|
| **Sign-magnitude** | Highest bit of magnitude = 1 | 0.5 ≤ |M| < 1 (for base 2) |
| **Two's complement** | Sign bit ≠ highest magnitude bit | 0.5 ≤ |M| < 1 |
| **Shift code** | Highest bit of mantissa = 1 | — |

> For base R, normalisation means the first digit of the mantissa is
> non-zero, i.e. `1/R ≤ |M| < 1`.

### Normalisation by shifting

| Operation | Mantissa | Exponent |
|-----------|----------|----------|
| **Left shift** (normalise) | ×2 | −1 |
| **Right shift** (normalise) | ÷2 | +1 |

---

## 5. Floating-Point Arithmetic

### 5.1 Addition / Subtraction

```
1. Align exponents (shift the smaller mantissa right, increment its exponent)
2. Add/subtract mantissas
3. Normalise the result
4. Round
5. Check for overflow/underflow
```

### Worked example: Add 0.5 + 0.375 in IEEE 754 single

```
0.5  = 1.0 × 2⁻¹    E = 126
0.375 = 1.1 × 2⁻²    E = 125

Align: shift 0.375's mantissa right by 1
  0.375 aligned = 0.11 × 2⁻¹

Add mantissas:
  1.000 0000...
+ 0.110 0000...
────────────────
  1.110 0000...

Result = 1.11 × 2⁻¹ = 0.875 ✓
```

### 5.2 Multiplication

```
1. Sign = S1 ⊕ S2
2. Exponent = E1 + E2 − bias
3. Mantissa = M1 × M2
4. Normalise and round
```

### 5.3 Division

```
1. Sign = S1 ⊕ S2
2. Exponent = E1 − E2 + bias
3. Mantissa = M1 / M2
4. Normalise and round
```

---

## 6. Precision and Rounding

### 6.1 Significant digits

| Format | Mantissa bits | Decimal digits of precision |
|--------|-------------|---------------------------|
| Single | 24 (23 + 1 hidden) | ~7 |
| Double | 53 (52 + 1 hidden) | ~15–16 |

### 6.2 Rounding modes (IEEE 754)

| Mode | Description |
|------|-------------|
| Round to nearest, ties to even | Default; minimises bias |
| Round toward +∞ | Always round up |
| Round toward −∞ | Always round down |
| Round toward 0 | Truncate |

---

## 7. Floating-Point Range Summary

| Format | Max normalised | Min normalised | Max denormalised | Min denormalised |
|--------|---------------|---------------|-----------------|-----------------|
| Single | ±3.4×10³⁸ | ±1.18×10⁻³⁸ | ±1.18×10⁻³⁸ | ±1.4×10⁻⁴⁵ |
| Double | ±1.8×10³⁰⁸ | ±2.23×10⁻³⁰⁸ | ±2.23×10⁻³⁰⁸ | ±4.94×10⁻³²⁴ |

---

## 8. Worked Examples

**Example 1:** What is the largest finite IEEE 754 single-precision
number?

```
S = 0, E = 254 (not 255 — that's infinity), M = all 1s
Value = 1.111...1 (23 ones) × 2^(254−127)
      = (2 − 2⁻²³) × 2¹²⁷
      ≈ 3.4028 × 10³⁸
```

**Example 2:** Encode −0.75 as IEEE 754 single.

```
0.75 = 0.11₂ = 1.1 × 2⁻¹
S = 1
E = −1 + 127 = 126 = 0111 1110
M = 1000 0000 0000 0000 0000 000 (drop leading 1, keep .1)

Result: 1 01111110 10000000000000000000000
Hex: 0xBF400000
```

**Example 3:** A non-IEEE floating-point format uses 1 sign bit, 5-bit
excess-16 exponent, and 10-bit sign-magnitude mantissa. Encode −5.5.

```
5.5 = 101.1₂ = 0.1011 × 2³  (normalised, first magnitude bit = 1)
S = 1
E = 3 + 16 = 19 = 10011
M = 1011000000 (10 bits, sign-magnitude, leading bit of fraction = 1)

Result: 1 10011 1011000000
```

---

## 9. Exam-Style Questions

**Q1.** In IEEE 754 single precision, the exponent bias is:
A. 126  B. 127  C. 128  D. 255
> Answer: B.

**Q2.** The binary pattern `0 11111111 00000000000000000000000` represents:
A. largest finite number  B. +0  C. +Infinity  D. NaN
> Answer: C (exponent all 1s, mantissa all 0s = Infinity).

**Q3.** How many decimal digits of precision does IEEE 754 double
provide?
A. 7  B. 11  C. 15–16  D. 32
> Answer: C.

**Q4.** A denormalised number has an exponent field of all zeros. The
implicit leading bit of the mantissa is:
A. 0  B. 1  C. the sign bit  D. undefined
> Answer: A (denormalised numbers use 0.M instead of 1.M).

**Q5.** When adding two floating-point numbers, the first step is:
A. add mantissas  B. align exponents  C. normalise  D. round
> Answer: B.

**Q6.** In a generic floating-point format with base-2 sign-magnitude
mantissa, normalisation requires:
A. the sign bit = 1  B. the highest magnitude bit = 1  C. the exponent = 0  D. the mantissa = 0
> Answer: B.

---

## 10. Further Reading

* IEEE 754-2008, *IEEE Standard for Floating-Point Arithmetic*.
* Goldberg, "What Every Computer Scientist Should Know About
  Floating-Point Arithmetic", *ACM Computing Surveys*, 1991.
* Patterson & Hennessy, *Computer Organization and Design*, ch. 3.

---

## 11. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Floating-point | 浮点数 | 04 |
| Significand / Mantissa | 尾数 | 04 |
| Exponent | 阶码 / 指数 | 04 |
| Bias | 偏移量 / 阶码偏移 | 04 |
| Normalisation | 规格化 | 04 |
| Denormalised number | 非规格化数 | 04 |
| Hidden bit | 隐藏位 | 04 |
| IEEE 754 | IEEE 754 标准 | 04 |
| Single precision | 单精度 | 04 |
| Double precision | 双精度 | 04 |
| Overflow | 上溢 | 04 |
| Underflow | 下溢 | 04 |
| Rounding | 舍入 | 04 |
| NaN | 非数 | 04 |
| Infinity | 无穷大 | 04 |
