# 03 — Pass by Value vs Pass by Reference

> Syllabus reference: P20–P37
>
> How arguments are passed to functions is one of the most frequently
> tested topics. The exam asks you to trace code that uses different
> parameter-passing mechanisms and predict the output. Master the four
> methods and their effects on the caller's variables.

---

## 1. The Core Question

When a function is called with an argument, does the function receive
a **copy** of the value, or a **reference** to the original variable?
The answer determines whether changes inside the function affect the
caller.

```
Caller:  x = 10
         foo(x)
              │
              ▼
         ┌─ Pass by value:  foo receives a copy → x unchanged
         ├─ Pass by ref:    foo receives x's address → x may change
         ├─ Pass by result: foo writes back on return
         └─ Pass by name:   foo uses textual substitution
```

---

## 2. Pass by Value (传值调用)

### 2.1 Mechanism

The **value** of the actual parameter is copied into the formal
parameter. The function operates on the copy; the original is
unaffected.

```
void foo(int a) {   // a is a copy of x
    a = 20;         // modifies the copy only
}

int x = 10;
foo(x);
// x is still 10
```

### 2.2 Properties

| Property | Detail |
|----------|--------|
| Direction | One-way (caller → callee) |
| Caller's variable | Unchanged |
| Memory | Extra copy created |
| Safety | High (no side effects on caller) |

---

## 3. Pass by Reference (传引用调用 / 传地址调用)

### 3.1 Mechanism

The **address** (reference) of the actual parameter is passed. The
formal parameter is an alias for the actual parameter; changes affect
the original.

```
void foo(int &a) {  // a is an alias for x
    a = 20;         // modifies x directly
}

int x = 10;
foo(x);
// x is now 20
```

### 3.2 Properties

| Property | Detail |
|----------|--------|
| Direction | Two-way (caller ↔ callee) |
| Caller's variable | Can be modified |
| Memory | No copy; just an address |
| Safety | Lower (unintended side effects possible) |

### 3.3 Simulating pass-by-reference in C

C does not have true pass-by-reference. Instead, we pass a **pointer
by value**:

```c
void foo(int *a) {   // a is a copy of &x
    *a = 20;         // modifies x through the pointer
}

int x = 10;
foo(&x);
// x is now 20
```

> Exam tip: passing a pointer is **pass by value** (the pointer itself
> is copied), but the effect is the same as pass by reference because
> the pointer points to the original data.

---

## 4. Pass by Result (传结果调用)

### 4.1 Mechanism

The formal parameter has no initial value. When the function returns,
the final value of the formal parameter is **copied back** to the
actual parameter.

```
void foo(out int a) {   // a starts undefined
    a = 20;             // assigned inside
}                        // on return, x = a = 20

int x = 10;
foo(x);
// x is now 20
```

### 4.2 Properties

| Property | Detail |
|----------|--------|
| Direction | One-way (callee → caller) |
| Initial value | Undefined (no copy in) |
| Final value | Copied out on return |

---

## 5. Pass by Value-Result (传值-结果调用)

### 5.1 Mechanism

Combines pass by value and pass by result: the value is **copied in**
at call time, and the final value is **copied out** at return time.

```
void foo(int a) {   // a starts as a copy of x
    a = 20;         // modifies the local copy
}                    // on return, x = a = 20

int x = 10;
foo(x);
// x is now 20 (value was copied back)
```

### 5.2 Difference from pass by reference

| Feature | Pass by reference | Pass by value-result |
|---------|------------------|---------------------|
| Aliasing | Yes (a and x are the same) | No (a is a copy) |
| When caller sees change | Immediately | Only after return |
| With aliasing | Changes visible immediately | Changes visible only after return |

### 5.3 The aliasing trap (exam classic)

```c
// Pass by reference:
void foo(int &a, int &b) { a = 1; b = 2; }
int x = 0;
foo(x, x);   // a and b both alias x
// After a=1: x=1; after b=2: x=2
// Final: x = 2

// Pass by value-result:
void foo(int a, int b) { a = 1; b = 2; /* copy back */ }
int x = 0;
foo(x, x);   // a and b are separate copies
// a = 1, b = 2; copy back: which one wins?
// Typically: x = b = 2 (last parameter copied back last)
// But this is implementation-defined!
```

> Exam tip: when the same variable is passed to two parameters,
> pass-by-reference and pass-by-value-result can give **different**
> results.

---

## 6. Pass by Name (传名调用)

### 6.1 Mechanism

The actual parameter is **textually substituted** into the function
body wherever the formal parameter appears. Evaluation is **delayed**
until the formal parameter is actually used (lazy evaluation).

### 6.2 Jensen's Device (exam classic)

```
// Pass by name:
real sum(name real x, integer i, integer lo, integer hi) {
    real s = 0;
    for i = lo to hi do
        s = s + x;
    return s;
}

// Call: sum(A[i], i, 1, 100)
// Equivalent to: A[1] + A[2] + ... + A[100]
```

The `i` in `A[i]` is re-evaluated each time `x` is accessed, using
the current value of `i`.

### 6.3 Properties

| Property | Detail |
|----------|--------|
| Evaluation | Lazy (on each use) |
| Aliasing effects | Can cause unexpected behaviour |
| Used in | Algol 60, Scala `=>` parameters, Haskell (lazy) |

---

## 7. Comparison Table — Memorise This

| Method | Chinese | Copy in? | Copy out? | Alias? | Caller changed? |
|--------|---------|----------|-----------|--------|-----------------|
| Value | 传值 | Yes | No | No | No |
| Reference | 传引用 | No | No | Yes | Yes (immediately) |
| Result | 传结果 | No | Yes | No | Yes (on return) |
| Value-result | 传值-结果 | Yes | Yes | No | Yes (on return) |
| Name | 传名 | No | No | Textual | Depends on substitution |

---

## 8. Worked Examples

**Example 1:** Trace the following code with pass by value.

```c
void swap(int a, int b) {
    int t = a;
    a = b;
    b = t;
}
int x = 1, y = 2;
swap(x, y);
// x = ?, y = ?
```

```
Pass by value: a and b are copies.
x = 1, y = 2  (unchanged — swap has no effect!)
```

**Example 2:** Same code with pass by reference.

```
a is an alias for x, b is an alias for y.
After swap: x = 2, y = 1  ✓
```

**Example 3:** Trace with pass by value-result.

```c
void foo(int a, int b) {
    a = a + 1;
    b = b + 1;
}
int x = 10;
foo(x, x);
```

```
Copy in: a = 10, b = 10
Execute: a = 11, b = 11
Copy out: x = a = 11, then x = b = 11
Final: x = 11
```

**Example 4:** Same code with pass by reference.

```
a and b both alias x.
a = a + 1 → x = 11
b = b + 1 → x = 12
Final: x = 12
```

> Key insight: pass by reference gives x = 12, pass by value-result
> gives x = 11. This difference is a favourite exam question.

---

## 9. Exam-Style Questions

**Q1.** In pass by value, the caller's variable is:
A. always changed  B. never changed  C. sometimes changed  D. changed on return
> Answer: B.

**Q2.** Pass by value-result differs from pass by reference when:
A. the function has no parameters  B. the same variable is passed to multiple parameters (aliasing)  C. the function returns a value  D. there is a loop
> Answer: B.

**Q3.** In C, `void foo(int *p)` is an example of:
A. pass by reference  B. pass by value (of a pointer)  C. pass by name  D. pass by result
> Answer: B (the pointer is passed by value; dereferencing it achieves
> the effect of pass by reference).

**Q4.** Jensen's Device exploits which parameter-passing method?
A. pass by value  B. pass by reference  C. pass by name  D. pass by result
> Answer: C.

**Q5.** In pass by name, the actual parameter is evaluated:
A. once at call time  B. once at return time  C. every time the formal parameter is used  D. never
> Answer: C.

**Q6.** `swap(x, y)` with pass by value results in:
A. x and y swapped  B. only x changed  C. only y changed  D. no change to x or y
> Answer: D.

---

## 10. Further Reading

* Sebesta — *Concepts of Programming Languages*, ch. 9.
* Scott — *Programming Language Pragmatics*, ch. 8.

---

## 11. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Pass by value | 传值调用 | 03 |
| Pass by reference | 传引用调用 / 传地址调用 | 03 |
| Pass by result | 传结果调用 | 03 |
| Pass by value-result | 传值-结果调用 | 03 |
| Pass by name | 传名调用 | 03 |
| Aliasing | 别名 | 03 |
| Formal parameter | 形式参数 / 形参 | 03 |
| Actual parameter | 实际参数 / 实参 | 03 |
| Side effect | 副作用 | 03 |
