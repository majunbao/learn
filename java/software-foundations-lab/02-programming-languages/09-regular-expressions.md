# 09 — Regular Expressions (正规式)

> Syllabus reference: P77–P82
>
> **Regular expressions** (正规式 / 正则表达式) are the formal foundation
> for lexical analysis. They describe the set of valid tokens in a
> language. The exam tests your ability to read, write, simplify, and
> convert regular expressions to finite automata.

---

## 1. Formal Definition

A **regular expression** over an alphabet Σ defines a **regular
language** (正规语言). The building blocks:

| Expression | Meaning | Chinese |
|-----------|---------|---------|
| `∅` | Empty set | 空集 |
| `ε` | Empty string | 空串 |
| `a` (a ∈ Σ) | Single character | 单字符 |
| `R1 | R2` (or `R1 + R2`) | Union (R1 or R2) | 并 / 或 |
| `R1 · R2` (or `R1R2`) | Concatenation | 连接 |
| `R*` | Kleene closure (zero or more) | 闭包 |
| `R+` | Positive closure (one or more) | 正闭包 |

### Precedence (high → low)

```
1. * + (closure)
2. · (concatenation, usually omitted)
3. | (union)
```

---

## 2. Operators in Detail

### 2.1 Union (|)

```
a | b  =  {a, b}
(a | b) | c  =  {a, b, c}
```

### 2.2 Concatenation (·)

```
ab  =  {ab}
(a|b)(c|d)  =  {ac, ad, bc, bd}
```

### 2.3 Kleene closure (*)

```
a*  =  {ε, a, aa, aaa, ...}
(a|b)*  =  all strings over {a, b}, including ε
```

### 2.4 Positive closure (+)

```
a+  =  {a, aa, aaa, ...}  =  aa*
R+  =  RR*
R*  =  ε | R+
```

---

## 3. Algebraic Identities (正规式等价变换)

These identities are essential for simplification and exam questions.

| Identity | Explanation |
|----------|-------------|
| `R \| R = R` | Idempotent (幂等) |
| `R \| ∅ = R` | Union with empty set |
| `R · ε = R` | Concatenation with empty string |
| `R · ∅ = ∅` | Concatenation with empty set |
| `ε* = ε` | Kleene closure of ε |
| `∅* = ε` | Kleene closure of empty set |
| `(R*)* = R*` | Double closure |
| `R+ = RR*` | Positive closure definition |
| `R* = ε \| R+` | Kleene and positive closure |
| `R \| ε = R \| ε` | Adding ε doesn't simplify unless needed |
| `(P \| Q)* = (P*Q*)*` | Star distributivity variant |
| `R(R* \| ε) = R+` | Useful simplification |

> Exam tip: `(a|b)* = (a*b*)* = (a*|b*)*` — all describe the same
> language (all strings over {a, b}).

---

## 4. Common Regular Expression Patterns

| Pattern | Language | Chinese description |
|---------|----------|-------------------|
| `(a|b)*` | All strings over {a, b} | a和b组成的所有字符串 |
| `a(a|b)*` | Strings starting with a | 以a开头的字符串 |
| `(a|b)*a` | Strings ending with a | 以a结尾的字符串 |
| `(a|b)*ab(a|b)*` | Strings containing "ab" | 包含ab的字符串 |
| `a*b*` | Any number of a's followed by any number of b's | 任意a后跟任意b |
| `(aa|bb)*` | Even-length strings of a's and b's (pairs) | a或b成对出现 |
| `(0|1)*00` | Binary strings ending with 00 | 以00结尾的二进制串 |
| `a*ba*ba*` | Strings with exactly two b's | 恰好含两个b的串 |

---

## 5. Regular Expression → NFA (Thompson's Construction)

Each sub-expression is converted to a small NFA, then combined:

### 5.1 Single character `a`

```
→ (s) ─a─→ (f)
```

### 5.2 Union `R1 | R2`

```
        ┌─ε─→ R1 ─ε─┐
→ (s) ──┤            ├──→ (f)
        └─ε─→ R2 ─ε─┘
```

### 5.3 Concatenation `R1R2`

```
→ R1 → R2 →
(merge R1's accept into R2's start)
```

### 5.4 Kleene closure `R*`

```
        ┌──ε──→ R ──ε──┐
        │       ↑  │    │
→ (s) ──ε───────┘  └──→ (f)
  │                          ↑
  └──────────ε───────────────┘
```

---

## 6. Worked Examples

**Example 1:** Simplify `(a|b)* | (a|b)*`

```
(a|b)* | (a|b)* = (a|b)*    (idempotent: R|R = R)
```

**Example 2:** What language does `a(b|c)*` describe?

```
Strings that start with 'a', followed by any combination of b's and c's.
Examples: a, ab, ac, abc, abbc, accb, ...
```

**Example 3:** Write a regular expression for "strings over {0,1} that
contain at least two 0s".

```
(0|1)*0(0|1)*0(0|1)*
```

**Example 4:** Write a regular expression for "strings over {a,b} where
every a is followed by at least one b".

```
(b*ab+)*b*   or   (b*abb*)*b*
```

**Example 5:** Simplify `∅* | ε`

```
∅* = ε, so ε | ε = ε
Answer: ε
```

---

## 7. Exam-Style Questions

**Q1.** The regular expression `(a|b)*` describes:
A. strings with only a's  B. all strings over {a,b}  C. the empty string only  D. strings starting with a
> Answer: B.

**Q2.** `a*` includes:
A. only a  B. ε and any number of a's  C. at least one a  D. no strings
> Answer: B.

**Q3.** `(a|b)*` is equivalent to:
A. `a*|b*`  B. `(a*b*)*`  C. `ab*`  D. `a+b+`
> Answer: B.

**Q4.** The regular expression for "strings ending with ab" over
{a,b} is:
A. `(a|b)ab`  B. `(a|b)*ab`  C. `ab(a|b)*`  D. `a*b*ab`
> Answer: B.

**Q5.** `∅*` equals:
A. ∅  B. ε  C. ∅*  D. undefined
> Answer: B.

**Q6.** `(R*)*` equals:
A. R  B. R*  C. R+  D. ε
> Answer: B.

---

## 8. Further Reading

* Aho et al. — *Compilers* (Dragon Book), §3.3.
* Hopcroft, Motwani, Ullman — *Introduction to Automata Theory*,
  ch. 2–3.

---

## 9. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Regular expression | 正规式 / 正则表达式 | 09 |
| Regular language | 正规语言 / 正则语言 | 09 |
| Alphabet | 字母表 | 09 |
| Union | 并 / 或 | 09 |
| Concatenation | 连接 | 09 |
| Kleene closure | 闭包 / 星闭包 | 09 |
| Positive closure | 正闭包 | 09 |
| Empty string (ε) | 空串 | 09 |
| Empty set (∅) | 空集 | 09 |
| Thompson's construction | Thompson构造法 | 09 |
