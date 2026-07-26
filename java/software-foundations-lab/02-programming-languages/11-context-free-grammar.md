# 11 — Context-Free Grammars (上下文无关文法)

> Syllabus reference: P104–P113
>
> Context-free grammars (CFG) are the formal foundation for **syntax
> analysis**. While regular expressions describe tokens (lexical
> structure), CFGs describe the **nested, recursive structure** of
> programs. The exam tests derivations, parse trees, ambiguity, and
> basic transformations.

---

## 1. Formal Definition

A CFG is a 4-tuple **G = (V, T, P, S)**:

| Component | Chinese | Meaning |
|-----------|---------|---------|
| V | 非终结符集 | Non-terminal symbols (variables) |
| T | 终结符集 | Terminal symbols (tokens) |
| P | 产生式 / 规则 | Production rules: A → α |
| S | 开始符号 | Start symbol (S ∈ V) |

### Key constraint

The left side of every production is a **single non-terminal**:
`A → α` where A ∈ V and α ∈ (V ∪ T)*. This is why it is
"context-free" — the replacement of A does not depend on surrounding
symbols.

---

## 2. Derivations (推导)

### 2.1 Definition

A **derivation** is a sequence of production applications starting from
S, replacing one non-terminal at a time, until only terminals remain.

```
S ⇒ α1 ⇒ α2 ⇒ ... ⇒ w    (w ∈ T*)
```

### 2.2 Leftmost derivation (最左推导)

Always replace the **leftmost** non-terminal first.

```
S ⇒ AB ⇒ aB ⇒ ab
      ↑
   leftmost non-terminal
```

### 2.3 Rightmost derivation (最右推导)

Always replace the **rightmost** non-terminal first.

```
S ⇒ AB ⇒ Ab ⇒ ab
       ↑
   rightmost non-terminal
```

> Exam tip: every sentence has **at most one** leftmost derivation and
> **at most one** rightmost derivation for an **unambiguous** grammar.
> If there are two different leftmost (or rightmost) derivations, the
> grammar is **ambiguous**.

---

## 3. Parse Trees (语法树 / 解析树)

### 3.1 Structure

- Root: start symbol S
- Internal nodes: non-terminals
- Leaves: terminals (left to right = derived string)
- Children of a node: right side of the production used

### 3.2 Example

Grammar: `E → E + E | E * E | id`

Derivation of `id + id * id`:

```
        E
      / | \
     E  +  E
     |   / | \
    id  E  *  E
        |     |
       id    id
```

### 3.3 Relationship to derivations

- **Leftmost derivation** = left-to-right construction of the parse tree
- **Rightmost derivation** = right-to-left construction
- Both yield the **same parse tree** for unambiguous grammars

---

## 4. Ambiguity (二义性)

### 4.1 Definition

A grammar is **ambiguous** (二义的) if there exists a string that has
**two different parse trees** (equivalently, two different leftmost
derivations or two different rightmost derivations).

### 4.2 Classic example

```
E → E + E | E * E | id
```

String `id + id * id` has two parse trees:

**Tree 1** (add first): `(id + id) * id`
```
        E
      / | \
     E  *  E
   / | \   |
  E  +  E  id
  |     |
 id    id
```

**Tree 2** (multiply first): `id + (id * id)`
```
        E
      / | \
     E  +  E
     |  / | \
    id E  *  E
       |     |
      id    id
```

### 4.3 Resolving ambiguity

| Method | Chinese | Example |
|--------|---------|---------|
| **Rewrite the grammar** | 改写文法 | Add precedence and associativity rules |
| **External rules** | 外部规则 | Parser uses precedence table (Yacc) |

Rewritten grammar with precedence (`*` > `+`):

```
E → E + T | T
T → T * F | F
F → (E) | id
```

Now `id + id * id` has only one parse tree (multiply first).

---

## 5. Left Recursion (左递归)

### 5.1 Definition

A grammar is **left-recursive** if `A ⇒+ Aα` for some α.

**Direct left recursion:** `A → Aα | β`

### 5.2 Problem

Top-down parsers (recursive descent, LL) cannot handle left recursion —
they loop forever.

### 5.3 Elimination

Transform `A → Aα | β` into:

```
A  → βA'
A' → αA' | ε
```

**Example:**

```
Before: E → E + T | T
After:  E  → TE'
        E' → +TE' | ε
```

---

## 6. Left Factoring (提取左公因子)

### 6.1 Problem

When two productions share a common prefix, a predictive parser cannot
choose between them.

```
A → αβ1 | αβ2
```

### 6.2 Solution

Factor out the common prefix:

```
A  → αA'
A' → β1 | β2
```

**Example:**

```
Before: S → if E then S else S | if E then S
After:  S  → if E then S S'
        S' → else S | ε
```

---

## 7. Chomsky Normal Form (CNF / 乔姆斯基范式)

### 7.1 Definition

A CFG is in CNF if every production is of one of two forms:

1. `A → BC` (two non-terminals)
2. `A → a` (one terminal)

(S → ε is also allowed if ε is in the language.)

### 7.2 Conversion steps

1. Eliminate ε-productions (except S → ε)
2. Eliminate unit productions (A → B)
3. Replace terminals in longer productions with new non-terminals
4. Break long right sides into binary productions

**Example:**

```
Before: S → ASB
After:  S → AC
        C → SB
        (where C is a new non-terminal)
```

---

## 8. Worked Examples

**Example 1:** Given grammar `S → aSb | ε`, derive `aabb`.

```
S ⇒ aSb ⇒ aaSbb ⇒ aaεbb = aabb
```

**Example 2:** Is the grammar `S → SS | (S) | ε` ambiguous?

```
Yes. The string ()() has two parse trees:
  S → SS → (S)(S) → ()()
  S → SS → (S)S → ()S → ()(S) → ()()
Both derive ()() but with different tree structures.
```

**Example 3:** Eliminate left recursion from `E → E + E | a`.

```
E  → aE'
E' → +aE' | ε
```

Wait — let's be more careful:

```
E → E + E | a  (direct left recursion)

Let α = +E, β = a:
E  → aE'
E' → +EE' | ε
```

Hmm, actually the standard transformation for `E → E + E | a`:

```
E  → aE'
E' → +aE' | ε
```

But this changes the language slightly. The standard approach is to
first remove the ambiguity, then remove left recursion.

---

## 9. Exam-Style Questions

**Q1.** A context-free grammar has productions of the form:
A. α → β (any strings)  B. A → α (single non-terminal on left)  C. αAβ → γ (context required)  D. A → a (single terminal only)
> Answer: B.

**Q2.** A grammar is ambiguous if a string has:
A. no derivation  B. exactly one derivation  C. two different parse trees  D. an infinite derivation
> Answer: C.

**Q3.** Left recursion causes problems for:
A. bottom-up parsers  B. top-down parsers  C. all parsers  D. no parsers
> Answer: B.

**Q4.** To eliminate `A → Aα | β`, we produce:
A. `A → βA', A' → αA' | ε`  B. `A → αA', A' → βA' | ε`  C. `A → α | β`  D. `A → Aα | β`
> Answer: A.

**Q5.** In CNF, every production has:
A. one terminal on the right  B. two non-terminals or one terminal on the right  C. any number of symbols  D. exactly three symbols
> Answer: B.

**Q6.** Left factoring resolves:
A. left recursion  B. common prefixes in alternatives  C. ambiguity  D. ε-productions
> Answer: B.

---

## 10. Further Reading

* Hopcroft, Motwani, Ullman — *Introduction to Automata Theory*, ch. 5.
* Aho et al. — *Compilers* (Dragon Book), §4.3.

---

## 11. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Context-free grammar (CFG) | 上下文无关文法 | 11 |
| Non-terminal | 非终结符 | 11 |
| Terminal | 终结符 | 11 |
| Production | 产生式 / 规则 | 11 |
| Start symbol | 开始符号 | 11 |
| Derivation | 推导 | 11 |
| Leftmost derivation | 最左推导 | 11 |
| Rightmost derivation | 最右推导 | 11 |
| Parse tree | 语法树 / 解析树 | 11 |
| Ambiguity | 二义性 | 11 |
| Left recursion | 左递归 | 11 |
| Left factoring | 提取左公因子 | 11 |
| Chomsky Normal Form (CNF) | 乔姆斯基范式 | 11 |
