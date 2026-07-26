# 07 — Program Errors and Exceptions

> Syllabus reference: P64–P69
>
> Errors can occur at every stage of compilation and execution. The
> exam classifies errors by **when** they are detected and tests your
> ability to identify the correct phase.

---

## 1. Error Classification by Detection Time

| Phase | Error type | Chinese | Example |
|-------|-----------|---------|---------|
| **Lexical analysis** | Lexical error | 词法错误 | Invalid character `$`, unterminated string `"hello` |
| **Syntax analysis** | Syntax error | 语法错误 | Missing `;`, unbalanced `(`, `if` without condition |
| **Semantic analysis** | Semantic error | 语义错误 | Type mismatch, undeclared variable, wrong argument count |
| **Linking** | Link error | 链接错误 | Undefined symbol, duplicate definition |
| **Run time** | Run-time error / exception | 运行时错误 / 异常 | Division by zero, null pointer, stack overflow, array out of bounds |

> Exam tip: the most common question is "in which phase is this error
> detected?" Memorise the table above.

---

## 2. Compile-Time Errors (编译时错误)

### 2.1 Lexical errors

| Error | Example | Detection |
|-------|---------|-----------|
| Illegal character | `int $x;` (C) | Scanner |
| Malformed number | `3.4.5` | Scanner |
| Unterminated comment | `/* ...` | Scanner |
| Unterminated string | `"hello` | Scanner |

### 2.2 Syntax errors

| Error | Example | Detection |
|-------|---------|-----------|
| Missing semicolon | `x = 1` | Parser |
| Unbalanced parentheses | `(x + 1` | Parser |
| Extra token | `if (x) else else` | Parser |
| Wrong keyword placement | `int if = 5;` | Parser |

### 2.3 Semantic errors

| Error | Example | Detection |
|-------|---------|-----------|
| Undeclared identifier | `y = x;` (x not declared) | Semantic analyser |
| Type mismatch | `int x = "hi";` | Semantic analyser |
| Wrong parameter count | `foo(1)` (foo takes 2 args) | Semantic analyser |
| Non-boolean condition | `if (3) { }` (in strict languages) | Semantic analyser |
| Missing return | `int foo() { }` | Semantic analyser |

---

## 3. Link Errors (链接错误)

| Error | Example |
|-------|---------|
| Undefined reference | Call a function that was declared but never defined |
| Duplicate definition | Two global variables with the same name across files |
| Library not found | `-lm` not linked when using `math.h` |

> Link errors are **not** detected by the compiler; they are detected
> by the **linker** after compilation.

---

## 4. Run-Time Errors and Exceptions (运行时错误与异常)

### 4.1 Common run-time errors

| Error | Chinese | Cause |
|-------|---------|-------|
| Division by zero | 除零错误 | `x / 0` |
| Null pointer dereference | 空指针解引用 | `*NULL` |
| Array index out of bounds | 数组越界 | `a[100]` when size is 10 |
| Stack overflow | 栈溢出 | Infinite recursion |
| Memory leak | 内存泄漏 | `malloc` without `free` |
| Segmentation fault | 段错误 | Accessing unmapped memory |

### 4.2 Exception handling

Most modern languages provide **structured exception handling**:

```
try {
    // code that may throw
} catch (ExceptionType e) {
    // handler
} finally {
    // always executed
}
```

| Component | Chinese | Purpose |
|-----------|---------|---------|
| `try` | 尝试块 | Encloses code that may throw |
| `catch` | 捕获块 | Handles specific exception types |
| `finally` | 最终块 | Always executed (cleanup) |
| `throw` / `raise` | 抛出 | Signals an exception |

### 4.3 Exception propagation

```
foo() → bar() → baz() [throws]
                         │
         baz has no handler → propagate to bar
         bar has no handler → propagate to foo
         foo has handler → caught
         foo has no handler → program terminates
```

---

## 5. Error Recovery Strategies

| Strategy | Chinese | How | Used in |
|----------|---------|-----|---------|
| **Panic mode** | 紧急模式 | Skip tokens until a synchronisation token (e.g. `;`, `}`) | Most parsers |
| **Phrase-level** | 短语级 | Replace / delete / insert a small number of tokens | Some LR parsers |
| **Error productions** | 错误产生式 | Add grammar rules for common errors | Grammar-specific |
| **Global correction** | 全局纠正 | Find the minimum edit to make the input valid | Theoretical; too expensive |

> Exam tip: **panic mode** is the simplest and most commonly used
> recovery strategy.

---

## 6. Worked Examples

**Example 1:** In which phase is the error `undeclared variable`
detected?

```
Semantic analysis. The variable was not found in the symbol table.
```

**Example 2:** In which phase is `missing semicolon` detected?

```
Syntax analysis. The parser expected a `;` but found something else.
```

**Example 3:** Is `int x = 3.14;` a lexical, syntax, or semantic error?

```
Semantic error (type mismatch: float assigned to int without cast).
Some languages allow implicit narrowing → warning, not error.
```

**Example 4:** Is `"hello` (unterminated string) a lexical or syntax
error?

```
Lexical error. The scanner cannot form a complete string token.
```

---

## 7. Exam-Style Questions

**Q1.** "Undeclared identifier" is detected during:
A. lexical analysis  B. syntax analysis  C. semantic analysis  D. code generation
> Answer: C.

**Q2.** A missing right parenthesis is a:
A. lexical error  B. syntax error  C. semantic error  D. run-time error
> Answer: B.

**Q3.** Division by zero is detected at:
A. compile time  B. link time  C. run time  D. load time
> Answer: C.

**Q4.** Panic-mode error recovery works by:
A. inserting missing tokens  B. skipping tokens until a synchronisation point  C. restarting the compiler  D. ignoring all errors
> Answer: B.

**Q5.** An undefined reference error is detected by the:
A. compiler  B. linker  C. loader  D. OS
> Answer: B.

**Q6.** Which of the following is NOT a compile-time error?
A. type mismatch  B. missing semicolon  C. null pointer dereference  D. undeclared variable
> Answer: C (null pointer dereference is a run-time error).

---

## 8. Further Reading

* Aho et al. — *Compilers* (Dragon Book), §4.4 (error recovery).
* Sebesta — *Concepts of Programming Languages*, ch. 14.

---

## 9. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Lexical error | 词法错误 | 07 |
| Syntax error | 语法错误 | 07 |
| Semantic error | 语义错误 | 07 |
| Link error | 链接错误 | 07 |
| Run-time error | 运行时错误 | 07 |
| Exception | 异常 | 07 |
| Exception handling | 异常处理 | 07 |
| Try-catch-finally | 尝试-捕获-最终 | 07 |
| Throw / Raise | 抛出 | 07 |
| Panic mode | 紧急模式 | 07 |
| Error recovery | 错误恢复 | 07 |
| Synchronisation token | 同步记号 | 07 |
