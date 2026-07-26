# 03 — Sign-Magnitude, One's Complement, Two's Complement & Shift Code

> Syllabus reference: P36–P45
>
> How do we represent **signed integers** in binary? This is one of the
> most heavily tested areas on the exam. Four encoding schemes exist;
> two's complement dominates modern hardware, but you must know all four
> and be able to convert between them fluently.

---

## 1. The Four Encoding Schemes (8-bit examples)

| Scheme | Chinese | Positive range | Negative range | Zero representation |
|--------|---------|---------------|----------------|---------------------|
| **Sign-magnitude** | 原码 | 0 ~ 127 | −0 ~ −127 | +0 and −0 (two zeros) |
| **One's complement** | 反码 | 0 ~ 127 | −0 ~ −127 | +0 and −0 (two zeros) |
| **Two's complement** | 补码 | 0 ~ 127 | −128 ~ −1 | Single 0 |
| **Excess / Shift code** | 移码 | −128 ~ +127 | (same) | 1000 0000 = 0 |

> For an **n-bit** system:
> - Sign-magnitude range: **−(2ⁿ⁻¹−1) ~ +(2ⁿ⁻¹−1)**
> - Two's complement range: **−2ⁿ⁻¹ ~ +(2ⁿ⁻¹−1)**
> - Two's complement has one more negative number than positive.

---

## 2. Sign-Magnitude (原码)

The MSB is the **sign bit** (0 = positive, 1 = negative); remaining
bits are the magnitude.

### Rules

| Value | Representation |
|-------|---------------|
| +5 | `0 000 0101` |
| −5 | `1 000 0101` |
| +0 | `0 000 0000` |
| −0 | `1 000 0000` |

### Pros & Cons

| Pro | Con |
|-----|-----|
| Simple, intuitive | Two representations of zero |
| Easy to read magnitude | Addition/subtraction requires sign checking |
| | Cannot represent −128 in 8 bits |

---

## 3. One's Complement (反码)

### Rules

| Value type | How to get one's complement |
|-----------|---------------------------|
| **Positive** | Same as sign-magnitude |
| **Negative** | Sign bit = 1; magnitude bits = **bitwise NOT** of the absolute value |

### Examples (8-bit)

| Value | Sign-magnitude | One's complement |
|-------|---------------|-----------------|
| +5 | `0000 0101` | `0000 0101` |
| −5 | `1000 0101` | `1111 1010` |
| +0 | `0000 0000` | `0000 0000` |
| −0 | `1000 0000` | `1111 1111` |

### One's complement addition

Add the two numbers. If there is a **carry out** of the MSB, add it
back to the LSB (**end-around carry**).

```
  +5:  0000 0101
+ −3:  1111 1100
────────────────
       0000 0001  + carry 1 → 0000 0010 = +2 ✓
```

---

## 4. Two's Complement (补码) — **the most important one**

### Rules

| Value type | How to get two's complement |
|-----------|---------------------------|
| **Positive** | Same as sign-magnitude |
| **Negative** | One's complement + 1 (i.e., invert all bits, then add 1) |

Alternative shortcut: **scan from right to left; keep all bits up to and
including the first 1; invert all remaining bits.**

### Examples (8-bit)

| Value | Sign-magnitude | One's complement | Two's complement |
|-------|---------------|-----------------|-----------------|
| +5 | `0000 0101` | `0000 0101` | `0000 0101` |
| −5 | `1000 0101` | `1111 1010` | `1111 1011` |
| +0 | `0000 0000` | `0000 0000` | `0000 0000` |
| −0 | `1000 0000` | `1111 1111` | `0000 0000` (same as +0!) |
| −128 | (not representable) | (not representable) | `1000 0000` |

> Key insight: two's complement eliminates the double-zero problem and
> can represent one extra negative number (−2ⁿ⁻¹).

### Two's complement addition

Just add; discard any carry out of the MSB. No end-around carry needed!

```
  +5:  0000 0101
+ −3:  1111 1101
────────────────
       0000 0010  = +2 ✓  (carry out discarded)
```

### Two's complement subtraction

`A − B = A + (−B)`. Compute `−B` as two's complement of B, then add.

### Negation shortcut

To negate a two's complement number: **invert all bits, then add 1**.

```
+5 = 0000 0101
Invert: 1111 1010
Add 1:  1111 1011 = −5 ✓
```

### Sign extension

To extend from n bits to m bits (m > n): **replicate the sign bit**.

```
8-bit −5:  1111 1011
16-bit −5: 1111 1111 1111 1011
```

---

## 5. Excess / Shift Code (移码)

### Definition

For an n-bit excess code with bias = 2ⁿ⁻¹:

> **[X]_shift = X + 2ⁿ⁻¹**  (treat as unsigned)

### Examples (8-bit, bias = 128)

| Value | Shift code |
|-------|-----------|
| −128 | `0000 0000` (−128 + 128 = 0) |
| −1 | `0111 1111` (−1 + 128 = 127) |
| 0 | `1000 0000` (0 + 128 = 128) |
| +1 | `1000 0001` |
| +127 | `1111 1111` |

### Properties

| Property | Detail |
|----------|--------|
| **Unsigned order = signed order** | Larger unsigned value = larger signed value |
| **Zero = 1000...0** | The bias value |
| **Relationship to two's complement** | `[X]_shift = [X]_2's complement with sign bit inverted` |

> Exam tip: shift code is used for the **exponent** field of IEEE 754
> floating-point numbers. The fact that unsigned comparison works for
> signed values makes hardware comparison of exponents trivial.

---

## 6. Conversion Summary Table

Given an 8-bit value, how to convert between representations:

| From → To | Positive | Negative |
|-----------|----------|----------|
| Sign-mag → One's comp | Same | Invert magnitude bits |
| Sign-mag → Two's comp | Same | Invert magnitude bits, then +1 |
| Two's comp → One's comp | Same | −1 (if negative) |
| One's comp → Two's comp | Same | +1 (if negative) |
| Two's comp → Shift code | Invert sign bit | Invert sign bit |
| Shift code → Two's comp | Invert sign bit | Invert sign bit |

> Universal shortcut: **shift code = two's complement with sign bit
> flipped.** Memorise this one line.

---

## 7. Overflow Detection in Two's Complement

| Scenario | Overflow? | Rule |
|----------|-----------|------|
| Positive + Positive = Negative | Yes | Two positives cannot yield a negative |
| Negative + Negative = Positive | Yes | Two negatives cannot yield a positive |
| Positive + Negative | Never | Result always fits |

**Hardware rule:** Overflow occurs when the carry **into** the MSB
differs from the carry **out of** the MSB.

```
OF = Carry_in_MSB ⊕ Carry_out_MSB
```

### Worked example

```
  0111 1111  (+127)
+ 0000 0001  (+1)
────────────
  1000 0000  (−128)  ← overflow!

Carry into MSB: 1 (from bit 6)
Carry out of MSB: 0
1 ⊕ 0 = 1 → OF = 1 ✓
```

---

## 8. Worked Examples

**Example 1:** Given `[X]_原 = 1,1010100`, find one's complement,
two's complement, and shift code.

```
[X]_原 = 1,1010100  (negative, magnitude = 1010100)

One's comp:  1,0101011  (invert magnitude bits)
Two's comp:  1,0101100  (one's comp + 1)
Shift code:  0,0101100  (invert sign bit of two's comp)
```

**Example 2:** Given `[X]_补 = 1110 0110`, find the decimal value.

```
Sign bit = 1 → negative
Two's comp → decimal:
  Invert: 0001 1001
  Add 1:  0001 1010 = 26
  Value = −26
```

**Example 3:** Compute `−80 + 70` in 8-bit two's complement.

```
−80: 80 = 0101 0000 → invert = 1010 1111 → +1 = 1011 0000
+70: 0100 0110

  1011 0000
+ 0100 0110
────────────
  1111 0110

Sign bit = 1 → negative.
Invert: 0000 1001, +1: 0000 1010 = 10
Result = −10 ✓
```

---

## 9. Exam-Style Questions

**Q1.** In 8-bit two's complement, the range is:
A. −127 ~ +127  B. −128 ~ +127  C. −128 ~ +128  D. −127 ~ +128
> Answer: B.

**Q2.** The two's complement of `−0` is:
A. 1000 0000  B. 1111 1111  C. 0000 0000  D. does not exist
> Answer: C (two's complement has only one zero).

**Q3.** Given `[X]_补 = 1000 0000`, what is X?
> −128. This is the unique value in two's complement with no sign-
> magnitude equivalent.

**Q4.** `[X]_移 = [X]_补` with the ___ bit inverted.
A. MSB  B. LSB  C. all  D. parity
> Answer: A (sign bit / MSB).

**Q5.** In 8-bit two's complement, `64 + 64` causes overflow because:
A. carry out = 1  B. two positives yield a negative result  C. the sum exceeds 255  D. sign bit is 0
> Answer: B (0100 0000 + 0100 0000 = 1000 0000 = −128).

**Q6.** How many distinct values can 8-bit sign-magnitude represent?
> 255 (−127 ~ −0, +0 ~ +127; two zeros count as one value? No — they
> are distinct bit patterns, so 256 patterns, but only 255 distinct
> integers because +0 = −0).

---

## 10. Further Reading

* Patterson & Hennessy, *Computer Organization and Design*, ch. 3.
* Stallings, *Computer Organization and Architecture*, ch. 9.

---

## 11. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Sign-magnitude | 原码 | 03 |
| One's complement | 反码 | 03 |
| Two's complement | 补码 | 03 |
| Excess code / Shift code | 移码 | 03 |
| Sign bit | 符号位 | 03 |
| Magnitude | 尾数 / 绝对值 | 03 |
| End-around carry | 循环进位 | 03 |
| Overflow | 溢出 | 03 |
| Sign extension | 符号扩展 | 03 |
| Negation | 求补 | 03 |
