# 08 — Intermediate Code

> Syllabus reference: P70–P76
>
> **Intermediate code** sits between the front-end and back-end of a
> compiler. It is machine-independent, making optimisation portable
> across target architectures. The exam tests the three common
> representations: three-address code, quadruples/triples, and DAGs.

---

## 1. Why Intermediate Code?

```
Source → Front-end → IR → Optimiser → IR → Back-end → Target

                         ↑
              Machine-independent
              Language-independent
              Easy to optimise
```

| Benefit | Explanation |
|---------|-------------|
| **Portability** | One front-end per language, one back-end per target |
| **Optimisation** | Machine-independent optimisations apply once |
| **Simplicity** | IR is simpler than source or machine code |

---

## 2. Three-Address Code (三地址码)

### 2.1 Definition

Each instruction has **at most three operands** (two sources + one
destination) and **one operator**.

```
x = y op z      (binary operation)
x = op y        (unary operation)
x = y           (copy)
goto L          (unconditional jump)
if x relop y goto L  (conditional jump)
param x         (set parameter)
call f, n       (call function f with n params)
return x        (return value)
x = y[i]        (array read)
x[i] = y        (array write)
x = *y          (pointer dereference)
*x = y          (pointer write)
```

### 2.2 Example

Source:
```c
if (a < b) {
    c = a + b;
} else {
    c = a - b;
}
```

Three-address code:
```
    if a < b goto L1
    t1 = a - b
    c = t1
    goto L2
L1: t2 = a + b
    c = t2
L2:
```

---

## 3. Quadruples (四元式)

### 3.1 Format

Each instruction is represented as a 4-tuple: **(op, arg1, arg2, result)**

| Field | Meaning |
|-------|---------|
| **op** | Operator |
| **arg1** | First operand |
| **arg2** | Second operand |
| **result** | Destination |

### 3.2 Examples

| Source | Quadruple |
|--------|-----------|
| `t1 = a + b` | `(+, a, b, t1)` |
| `t2 = -c` | `(uminus, c, —, t2)` |
| `c = t1` | `(=, t1, —, c)` |
| `if a < b goto L1` | `(j<, a, b, L1)` |
| `goto L2` | `(jump, —, —, L2)` |
| `param x` | `(param, x, —, —)` |
| `call foo, 2` | `(call, foo, 2, —)` |

### 3.3 Full example

For `c = (a + b) * (a - b)`:

| # | op | arg1 | arg2 | result |
|---|-----|------|------|--------|
| 0 | + | a | b | t1 |
| 1 | − | a | b | t2 |
| 2 | * | t1 | t2 | t3 |
| 3 | = | t3 | — | c |

---

## 4. Triples (三元式)

### 4.1 Format

Each instruction is a 3-tuple: **(op, arg1, arg2)**. The **result** is
implicitly the **position** (index) of the triple.

| # | op | arg1 | arg2 |
|---|-----|------|------|
| 0 | + | a | b |
| 1 | − | a | b |
| 2 | * | (0) | (1) |
| 3 | = | c | (2) |

> Note: `(0)` and `(1)` refer to the results of triples 0 and 1.

### 4.2 Pros & Cons vs Quadruples

| Feature | Quadruples | Triples |
|---------|-----------|---------|
| Result field | Explicit | Implicit (position) |
| Referencing result | By name | By index |
| Reordering | Easy (just change result name) | Hard (must update all references) |
| Space | More (4 fields) | Less (3 fields) |

> Exam tip: **quadruples** are easier to reorder (important for
> optimisation); **triples** save space but make reordering difficult.

---

## 5. Indirect Triples (间接三元式)

Separate the **execution order** from the **triples themselves**:

```
Triples table:          Execution order table:
#  op   arg1  arg2      #  pointer
0  +    a     b         0  (0)
1  −    a     b         1  (1)
2  *    (0)  (1)        2  (2)
3  =    c    (2)        3  (3)
```

To reorder: just change the execution order table; the triples stay
in place.

> Indirect triples combine the space efficiency of triples with the
> reordering convenience of quadruples.

---

## 6. DAG — Directed Acyclic Graph (有向无环图)

### 6.1 Purpose

A DAG represents a **basic block** of code, eliminating **common
sub-expressions** and identifying **redundant computations**.

### 6.2 Construction rules

1. For each statement `x = y op z`:
   - If a node for `y op z` already exists, reuse it (CSE).
   - Otherwise, create a new node.
2. Attach variable names to the node that defines their current value.

### 6.3 Example

Source:
```
t1 = a + b
t2 = a + b    ← same as t1 (common sub-expression)
t3 = t1 * t2
c = t3
```

DAG:
```
        (*)
       /   \
     (+)   (+) ← same node! (common sub-expression)
    /   \
   a     b

Labels on the (+) node: t1, t2
Labels on the (*) node: t3, c
```

Optimised code (from DAG):
```
t1 = a + b
t3 = t1 * t1
c = t3
```

### 6.4 What DAGs reveal

| Optimisation | How DAG helps |
|-------------|---------------|
| **Common sub-expression elimination** | Reuse existing nodes |
| **Dead code elimination** | Nodes with no used labels |
| **Copy propagation** | Variables pointing to same node |
| **Constant folding** | Evaluate constant expressions at compile time |

---

## 7. Comparison of Representations

| Feature | Three-address code | Quadruples | Triples | DAG |
|---------|-------------------|-----------|---------|-----|
| Fields per instruction | 3–4 | 4 | 3 | Graph |
| Result reference | By name | By name | By position | By node |
| Reordering | Easy | Easy | Hard | N/A |
| CSE detection | Manual | Manual | Manual | Automatic |
| Use | General | Most common | Space-saving | Basic block optimisation |

---

## 8. Exam-Style Questions

**Q1.** A quadruple has how many fields?
A. 2  B. 3  C. 4  D. 5
> Answer: C (op, arg1, arg2, result).

**Q2.** In a triple, the result is represented by:
A. an explicit result field  B. the position (index) of the triple  C. a label  D. a pointer
> Answer: B.

**Q3.** A DAG can automatically detect:
A. syntax errors  B. common sub-expressions  C. type errors  D. lexical errors
> Answer: B.

**Q4.** Quadruples are preferred over triples for optimisation because:
A. they use less space  B. they are easier to reorder  C. they are faster  D. they detect more errors
> Answer: B.

**Q5.** The intermediate code `t1 = a + b; t2 = t1 * c` in quadruple
form is:
> `(+, a, b, t1)` and `(*, t1, c, t2)`.

**Q6.** Indirect triples solve the problem of:
A. code size  B. reordering difficulty in triples  C. type checking  D. lexical analysis
> Answer: B.

---

## 9. Further Reading

* Aho et al. — *Compilers* (Dragon Book), ch. 8.
* Cooper & Torczon — *Engineering a Compiler*, ch. 5, 9.

---

## 10. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Intermediate code | 中间代码 | 08 |
| Three-address code | 三地址码 | 08 |
| Quadruple | 四元式 | 08 |
| Triple | 三元式 | 08 |
| Indirect triple | 间接三元式 | 08 |
| DAG | 有向无环图 | 08 |
| Common sub-expression | 公共子表达式 | 08 |
| Basic block | 基本块 | 08 |
| Temporary variable | 临时变量 | 08 |
| Dead code | 死代码 | 08 |
| Constant folding | 常量折叠 | 08 |
