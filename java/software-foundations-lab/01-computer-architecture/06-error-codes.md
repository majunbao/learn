# 06 — Error Detection & Correction Codes

> Syllabus reference: P64–P76
>
> Data corruption is a fact of life in digital systems — cosmic rays,
> electrical noise, and media degradation all flip bits. **Error
> detection codes** tell you something went wrong; **error correction
> codes** let you fix it. The exam covers three: parity, Hamming code,
> and CRC.

---

## 1. Why Error Codes?

```
Sender ────[noisy channel]────► Receiver

Without error code: corrupted data accepted silently
With detection code: receiver can detect corruption → request retransmission
With correction code: receiver can fix corruption → no retransmission needed
```

### Key metrics

| Metric | Formula | Meaning |
|--------|---------|---------|
| **Code distance (Hamming distance)** | Number of bit positions where two codewords differ | Minimum distance d_min determines capability |
| **Detection capability** | d_min − 1 errors detectable | |
| **Correction capability** | ⌊(d_min − 1) / 2⌋ errors correctable | |

> Example: d_min = 3 → detect 2-bit errors, correct 1-bit errors.

---

## 2. Parity Check (奇偶校验)

### 2.1 Simple parity

Append one parity bit to make the total number of 1s **even** (even
parity) or **odd** (odd parity).

| Data | Even parity bit | Codeword |
|------|----------------|----------|
| 1011 001 | 0 (already 4 ones — even) | 1011 0010 |
| 1011 011 | 1 (5 ones → need 1 more) | 1011 0111 |

### 2.2 Properties

| Property | Value |
|----------|-------|
| d_min | 2 |
| Detects | 1-bit errors (any odd number of errors) |
| Misses | 2-bit errors (any even number of errors) |
| Corrects | None |

### 2.3 Two-dimensional parity (交叉奇偶校验)

Arrange data in a matrix; add a parity bit for each row and each column.

```
Data bits:     Row parity
1 0 1 1 0  →  1
0 1 1 0 1  →  1
1 1 0 0 1  →  0
↓ ↓ ↓ ↓ ↓
Col parity: 0 0 0 1 0
```

Can **detect and correct** a single-bit error (intersection of the
failing row and column). Can **detect** (but not correct) any 2-bit
error in different rows/columns.

---

## 3. Hamming Code (海明码)

### 3.1 Key idea

Place **check bits** at positions that are powers of 2 (1, 2, 4, 8, …).
Each check bit covers all data bits whose position number has that
power of 2 in its binary representation.

### 3.2 How many check bits?

Given m data bits and r check bits:

```
2ʳ ≥ m + r + 1
```

| Data bits (m) | Check bits (r) | Total (m+r) |
|---------------|---------------|-------------|
| 1 | 2 | 3 |
| 2–4 | 3 | 5–7 |
| 5–11 | 4 | 9–15 |
| 12–26 | 5 | 17–31 |
| 27–57 | 6 | 33–63 |

### 3.3 Encoding algorithm

```
1. Determine r from 2ʳ ≥ m + r + 1.
2. Place data bits in non-power-of-2 positions (3,5,6,7,9,10,11,…).
3. Place check bits in power-of-2 positions (1,2,4,8,…).
4. For each check bit P_i (at position 2^i):
   P_i = XOR of all bit positions whose (i+1)-th binary digit is 1.
5. Fill in the check bits.
```

### 3.4 Worked example: Encode 1011 using Hamming code

```
m = 4, need 2ʳ ≥ 4 + r + 1 → r = 3 (2³ = 8 ≥ 8)
Total = 7 bits

Positions:  1  2  3  4  5  6  7
Type:       P1 P2 D1 P4 D2 D3 D4
Data:              1      0  1  1

P1 (covers positions with bit 0 of position set: 1,3,5,7):
   P1 ⊕ D1 ⊕ D2 ⊕ D4 = 0 → P1 = 1⊕0⊕1 = 0

P2 (covers positions with bit 1 set: 2,3,6,7):
   P2 ⊕ D1 ⊕ D3 ⊕ D4 = 0 → P2 = 1⊕1⊕1 = 1

P4 (covers positions with bit 2 set: 4,5,6,7):
   P4 ⊕ D2 ⊕ D3 ⊕ D4 = 0 → P4 = 0⊕1⊕1 = 0

Codeword: 0 1 1 0 0 1 1
```

### 3.5 Error detection and correction

```
1. Recompute each check bit.
2. Form the syndrome: S = (P4_check P2_check P1_check) as a binary number.
3. If S = 0 → no error.
4. If S ≠ 0 → S is the position of the erroneous bit.
5. Flip that bit to correct.
```

### 3.6 Worked example: Detect and correct error

Received: `0 1 1 0 0 1 0` (bit 7 was flipped from 1 to 0)

```
P1 check: positions 1,3,5,7 → 0⊕1⊕0⊕0 = 1 → fail
P2 check: positions 2,3,6,7 → 1⊕1⊕1⊕0 = 1 → fail
P4 check: positions 4,5,6,7 → 0⊕0⊕1⊕0 = 1 → fail

Syndrome S = (P4 P2 P1) = 111₂ = 7
Error at position 7 → flip bit 7: 0→1

Corrected: 0 1 1 0 0 1 1 ✓
```

### 3.7 Properties

| Property | Value |
|----------|-------|
| d_min | 3 |
| Detects | 2-bit errors |
| Corrects | 1-bit errors |
| Overhead | r check bits for m data bits |

---

## 4. CRC — Cyclic Redundancy Check (循环冗余校验)

### 4.1 Key idea

Treat the data as a polynomial in GF(2), divide by a **generator
polynomial G(x)**, and append the remainder as the check value.

### 4.2 Terminology

| Term | Meaning |
|------|---------|
| **Data polynomial** M(x) | The original data bits |
| **Generator polynomial** G(x) | Agreed-upon divisor; degree = r |
| **Codeword** T(x) | M(x) · xʳ + R(x) (data shifted left by r + remainder) |
| **Remainder** R(x) | Result of polynomial division |

### 4.3 Encoding algorithm

```
1. Let r = degree of G(x).
2. Append r zero bits to M(x) → M(x) · xʳ.
3. Divide M(x) · xʳ by G(x) using XOR-based polynomial division.
4. The remainder R(x) has at most r bits.
5. Codeword = M(x) · xʳ + R(x) (replace the r zeros with R(x)).
```

### 4.4 Worked example

Data: `1100 011` (7 bits), G(x) = x³ + x + 1 → `1011` (4 bits, r = 3)

```
Append 3 zeros: 1100 011 000

XOR division:
1100011000 ÷ 1011

 1100011000
 1011
 ----
  1110
  1011
  ----
   1011
   1011
   ----
    0000
    0000
    ----
     0000
     0000
     ----
      0000

Remainder R(x) = 100

Codeword: 1100 011 100
```

### 4.5 Verification

Divide the received codeword by G(x). If the remainder is **0**, the
data is intact.

### 4.6 Common generator polynomials

| Name | G(x) | Use |
|------|------|-----|
| CRC-8 | x⁸ + x² + x + 1 | ATM |
| CRC-16 | x¹⁶ + x¹⁵ + x² + 1 | Modbus |
| CRC-32 | x³² + x²⁶ + x²³ + x²² + x¹⁶ + x¹² + x¹¹ + x¹⁰ + x⁸ + x⁷ + x⁵ + x⁴ + x² + x + 1 | Ethernet, ZIP |

### 4.7 Properties

| Property | Value |
|----------|-------|
| Detects | All single-bit errors, all double-bit errors (if G(x) has 3+ terms), all odd-number errors (if G(x) has x+1 as factor), all burst errors ≤ r bits |
| Corrects | None (detection only) |

---

## 5. Comparison of the Three Codes

| Feature | Parity | Hamming | CRC |
|---------|--------|---------|-----|
| Overhead | 1 bit | log₂(m+r+1) bits | r bits (depends on G(x)) |
| d_min | 2 | 3 | Depends on G(x) |
| Detect | 1-bit errors | 2-bit errors | Burst ≤ r, many patterns |
| Correct | None | 1-bit errors | None |
| Complexity | Trivial | Moderate | Moderate (XOR division) |
| Use case | Memory, UART | ECC RAM | Network, storage |

---

## 6. Exam-Style Questions

**Q1.** A code has d_min = 5. How many errors can it detect and correct?
> Detect: 4. Correct: 2. (d_min − 1 detectable; ⌊(d_min−1)/2⌋ correctable.)

**Q2.** How many check bits are needed for 8 data bits using Hamming code?
> 2ʳ ≥ 8 + r + 1. Try r = 4: 16 ≥ 13 ✓. Answer: 4.

**Q3.** In Hamming code, if the syndrome is `0101`, which bit is in error?
> Position 5 (syndrome gives the error position in binary).

**Q4.** CRC can detect all burst errors of length ≤ r because:
A. the remainder is always 0  B. the generator polynomial has r+1 bits  C. any burst ≤ r cannot make the remainder 0  D. CRC uses XOR
> Answer: C.

**Q5.** Even parity of `1101 011` is:
> Count 1s: 5 (odd). Even parity bit = 1 (to make total even). Codeword
> = `1101 0111`.

**Q6.** Two-dimensional parity can correct a single-bit error because:
A. d_min = 4  B. the intersection of the failing row and column pinpoints the bit  C. it uses Hamming distance  D. it has two parity bits
> Answer: B.

---

## 7. Further Reading

* Hamming, "Error Detecting and Error Correcting Codes", *Bell System
  Technical Journal*, 1950.
* Peterson & Brown, "Cyclic Codes for Error Detection", *Proceedings
  of the IRE*, 1961.
* Stallings, *Computer Organization and Architecture*, ch. 5.

---

## 8. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Parity check | 奇偶校验 | 06 |
| Even parity | 偶校验 | 06 |
| Odd parity | 奇校验 | 06 |
| Hamming code | 海明码 | 06 |
| Check bit | 校验位 | 06 |
| Syndrome | 伴随式 / 校验子 | 06 |
| CRC | 循环冗余校验 | 06 |
| Generator polynomial | 生成多项式 | 06 |
| Codeword | 码字 | 06 |
| Hamming distance | 海明距离 | 06 |
| Minimum distance | 最小距离 | 06 |
| Burst error | 突发错误 | 06 |
