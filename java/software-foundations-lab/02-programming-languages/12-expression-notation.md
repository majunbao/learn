# 12 — Infix, Prefix, and Postfix Expressions (中缀、前缀、后缀表达式)

> Syllabus reference: P114–P130
>
> Expression notation is a perennial exam topic. You must be able to
> **convert** between the three notations and **evaluate** postfix
> expressions using a stack. The key insight: postfix and prefix
> eliminate the need for parentheses and precedence rules.

---

## 1. Three Notations

| Notation | Chinese | Operator position | Example |
|----------|---------|-------------------|---------|
| **Infix** | 中缀 | Between operands | `a + b * c` |
| **Prefix** (Polish) | 前缀 / 波兰式 | Before operands | `+ a * b c` |
| **Postfix** (Reverse Polish) | 后缀 / 逆波兰式 | After operands | `a b c * +` |

---

## 2. Infix Notation (中缀表达式)

### 2.1 Rules

- Operators go **between** operands.
- **Precedence** and **associativity** determine evaluation order.
- **Parentheses** override precedence.

### 2.2 Precedence (high → low)

```
1. ()           (parentheses)
2. ^            (exponentiation, right-associative)
3. * / %        (multiplicative, left-associative)
4. + −          (additive, left-associative)
```

### 2.3 Problem with infix

Ambiguity: `a + b * c` could mean `(a + b) * c` or `a + (b * c)`.
Precedence rules resolve this, but parsing is complex.

---

## 3. Postfix Notation (后缀表达式 / 逆波兰式)

### 3.1 Properties

- No parentheses needed
- No precedence rules needed
- Evaluated **left to right** using a stack
- Ideal for computers

### 3.2 Infix → Postfix conversion (algorithm)

Use a stack for operators:

```
For each token in the infix expression (left to right):
  If operand: output it
  If '(':
      push to stack
  If ')':
      pop and output until '(' is found (discard '(')
  If operator:
      while stack top has ≥ precedence AND top ≠ '(':
          pop and output
      push current operator
After all tokens: pop and output remaining operators
```

### 3.3 Worked example

Convert `a + b * c - d` to postfix:

| Token | Action | Stack | Output |
|-------|--------|-------|--------|
| a | output | | a |
| + | push | + | a |
| b | output | + | a b |
| * | push (* > +) | + * | a b |
| c | output | + * | a b c |
| − | pop * (+ ≥ −? no, but * ≥ −) pop + | − | a b c * + |
| d | output | − | a b c * + d |
| end | pop all | | a b c * + d − |

Result: `a b c * + d −`

### 3.4 Evaluating postfix expressions (stack algorithm)

```
For each token (left to right):
  If operand: push onto stack
  If operator:
      pop right operand
      pop left operand
      compute left op right
      push result
Final result is the only value on the stack
```

**Example:** Evaluate `5 3 2 * + 4 −`

| Token | Stack | Action |
|-------|-------|--------|
| 5 | 5 | push |
| 3 | 5 3 | push |
| 2 | 5 3 2 | push |
| * | 5 6 | 3*2=6 |
| + | 11 | 5+6=11 |
| 4 | 11 4 | push |
| − | 7 | 11−4=7 |

Result: **7**

---

## 4. Prefix Notation (前缀表达式 / 波兰式)

### 4.1 Properties

- No parentheses needed
- No precedence rules needed
- Evaluated **right to left** using a stack

### 4.2 Infix → Prefix conversion

**Method:** Reverse the infix expression, convert to postfix (with
adjusted parentheses), then reverse the result.

```
Infix:  a + b * c
Step 1: Reverse: c * b + a
Step 2: Convert to postfix: c b * a +
Step 3: Reverse: + a * b c
Result: + a * b c
```

> Important: when reversing, also swap `(` and `)`.

### 4.3 Evaluating prefix expressions

Scan **right to left**, same stack method as postfix:

```
For each token (right to left):
  If operand: push
  If operator:
      pop left operand
      pop right operand
      compute left op right
      push result
```

**Example:** Evaluate `+ * 3 2 5`

| Token (R→L) | Stack | Action |
|-------------|-------|--------|
| 5 | 5 | push |
| 2 | 5 2 | push |
| 3 | 5 2 3 | push |
| * | 5 6 | 3*2=6 |
| + | 11 | 5+6=11 |

Result: **11**

---

## 5. Quick Conversion Tricks

### 5.1 Infix → Postfix (parenthesise first)

1. Fully parenthesise the infix expression
2. Move each operator to the right of its closing parenthesis
3. Remove all parentheses

```
a + b * c
→ (a + (b * c))
→ (a (b c *) +)
→ a b c * +
```

### 5.2 Infix → Prefix (parenthesise first)

1. Fully parenthesise
2. Move each operator to the left of its opening parenthesis
3. Remove all parentheses

```
a + b * c
→ (a + (b * c))
→ (+ a (* b c))
→ + a * b c
```

### 5.3 Postfix → Infix

Read postfix left to right; build expression tree; infix = inorder
traversal with parentheses.

### 5.4 Prefix → Infix

Read prefix right to left; build expression tree; infix = inorder
traversal with parentheses.

---

## 6. Expression Trees (表达式树)

An expression tree is a binary tree where:
- **Leaves** = operands
- **Internal nodes** = operators

| Traversal | Notation |
|-----------|----------|
| Inorder (LNR) | Infix |
| Preorder (NLR) | Prefix |
| Postorder (LRN) | Postfix |

**Example:** `a + b * c`

```
      +
     / \
    a   *
       / \
      b   c

Inorder:   a + b * c    (infix)
Preorder:  + a * b c    (prefix)
Postorder: a b c * +    (postfix)
```

---

## 7. Comparison Table

| Feature | Infix | Prefix | Postfix |
|---------|-------|--------|---------|
| Operator position | Between | Before | After |
| Parentheses needed? | Yes | No | No |
| Precedence rules? | Yes | No | No |
| Evaluation direction | Complex | Right→Left | Left→Right |
| Easy for humans? | Yes | No | No |
| Easy for computers? | No | Yes | Yes |
| Also called | — | Polish notation | Reverse Polish notation |

---

## 8. Worked Examples

**Example 1:** Convert `(a + b) * (c - d)` to postfix.

```
Token  Stack   Output
(      (
a              a
+      ( +     a
b              a b
)      pop +   a b +
*      *       a b +
(      * (     a b +
c              a b + c
-      * ( -   a b + c
d              a b + c d
)      pop -   a b + c d -
end    pop *   a b + c d - *

Result: a b + c d - *
```

**Example 2:** Evaluate postfix `3 4 + 2 * 7 /`

```
3 → push 3
4 → push 4
+ → 3+4=7, push 7
2 → push 2
* → 7*2=14, push 14
7 → push 7
/ → 14/7=2, push 2

Result: 2
```

**Example 3:** Convert `a * b + c * d` to prefix.

```
Step 1: Reverse: d * c + b * a
Step 2: Postfix of reversed: d c * b a * +
Step 3: Reverse: + * a b * c d

Result: + * a b * c d
```

---

## 9. Exam-Style Questions

**Q1.** The postfix expression for `a + b * c` is:
A. `a b c + *`  B. `a b c * +`  C. `+ a b c`  D. `a + b c *`
> Answer: B.

**Q2.** Postfix notation does NOT require:
A. operands  B. operators  C. parentheses  D. a stack
> Answer: C.

**Q3.** Evaluate `5 1 2 + 4 * + 3 −`:
```
5 → push 5
1 → push 1
2 → push 2
+ → 1+2=3, push 3
4 → push 4
* → 3*4=12, push 12
+ → 5+12=17, push 17
3 → push 3
− → 17−3=14
```
> Answer: 14.

**Q4.** The prefix expression for `a + b * c` is:
A. `+ a * b c`  B. `* + a b c`  C. `a b c * +`  D. `+ * a b c`
> Answer: A.

**Q5.** In an expression tree, postorder traversal yields:
A. infix  B. prefix  C. postfix  D. the original source
> Answer: C.

**Q6.** To convert infix to prefix, you can:
A. convert to postfix then reverse  B. reverse infix, convert to postfix, then reverse  C. just add parentheses  D. read right to left
> Answer: B.

---

## 10. Further Reading

* Aho et al. — *Compilers* (Dragon Book), §2.5.
* Standish — *Data Structures, Algorithms, and Software Principles*,
  ch. 4 (expression evaluation).

---

## 11. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Infix expression | 中缀表达式 | 12 |
| Prefix expression / Polish notation | 前缀表达式 / 波兰式 | 12 |
| Postfix expression / Reverse Polish notation | 后缀表达式 / 逆波兰式 | 12 |
| Expression tree | 表达式树 | 12 |
| Precedence | 优先级 | 12 |
| Associativity | 结合性 | 12 |
| Inorder traversal | 中序遍历 | 12 |
| Preorder traversal | 前序遍历 | 12 |
| Postorder traversal | 后序遍历 | 12 |
| Stack | 栈 | 12 |
