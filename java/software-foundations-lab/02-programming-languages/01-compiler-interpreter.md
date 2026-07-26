# 01 — Compilers vs Interpreters

> Syllabus reference: P2–P7
>
> High-level programming languages must be translated into machine code
> before the CPU can execute them. Two fundamental approaches exist:
> **compilation** (translate the whole program first, then run) and
> **interpretation** (translate and execute one statement at a time).
> Understanding their differences — and how modern systems blend both —
> is essential.

---

## 1. Compilation (编译)

### 1.1 Definition

A **compiler** translates the **entire source program** into an
equivalent target program (usually machine code or object code). The
target program is then executed separately.

```
Source code ──[Compiler]──► Object code ──[Linker/Loader]──► Executable ──[CPU]──► Result
```

### 1.2 Characteristics

| Feature | Detail |
|---------|--------|
| Translation timing | Before execution (ahead-of-time) |
| Output | Standalone executable file |
| Execution speed | Fast (no translation overhead at run time) |
| Error detection | All errors found during compilation |
| Distribution | Only the executable is distributed (source hidden) |
| Portability | Must recompile for each target platform |

### 1.3 Typical compiled languages

C, C++, Go, Rust, Pascal, Fortran

---

## 2. Interpretation (解释)

### 2.1 Definition

An **interpreter** reads, translates, and **executes one statement at a
time**, without producing a standalone executable.

```
Source code ──[Interpreter]──► Result
                  │
         Read → Translate → Execute → Repeat
```

### 2.2 Characteristics

| Feature | Detail |
|---------|--------|
| Translation timing | During execution (line by line) |
| Output | No separate executable; result produced directly |
| Execution speed | Slower (translation overhead every run) |
| Error detection | Errors found only when the offending line is reached |
| Distribution | Source code must be distributed |
| Portability | Runs on any platform with an interpreter |

### 2.3 Typical interpreted languages

Python, Ruby, JavaScript (traditionally), Bash, PHP

---

## 3. Side-by-Side Comparison — Memorise This

| Feature | Compiler | Interpreter |
|---------|----------|-------------|
| Translation unit | Entire program | One statement at a time |
| Output | Executable file | Direct result |
| Execution speed | Fast | Slow |
| Memory usage | Stores object code | No object code stored |
| Error detection | All at compile time | At run time, line by line |
| Debugging | Harder (no source at run time) | Easier (source available) |
| Code obfuscation | Yes (binary) | No (source distributed) |
| Portability | Recompile per platform | Same source runs anywhere |
| Example | C, C++ | Python, Ruby |

> Exam tip: the most common exam question is "which is faster at
> execution?" → Compiler. "Which is easier to debug?" → Interpreter.

---

## 4. Hybrid Approaches (混合方式)

Modern languages often combine compilation and interpretation for the
best of both worlds.

### 4.1 Compile to bytecode, then interpret

```
Source ──[Compiler]──► Bytecode ──[Virtual Machine / Interpreter]──► Result
```

| Language | Bytecode | Virtual Machine |
|----------|----------|-----------------|
| Java | `.class` files | JVM |
| C# / VB.NET | CIL / MSIL | CLR |
| Python | `.pyc` files | CPython VM |
| Kotlin | `.class` files | JVM |

### 4.2 JIT compilation (Just-In-Time)

The VM compiles bytecode into native machine code **at run time**, just
before execution. Frequently-executed code ("hot spots") are compiled
and cached.

```
Bytecode ──[JIT Compiler]──► Native code ──[CPU]──► Result
```

| Benefit | Explanation |
|---------|-------------|
| Portability | Bytecode is platform-independent |
| Speed | JIT-compiled hot paths approach native speed |
| Adaptivity | JIT can optimise based on actual run-time profiling |

### 4.3 AOT compilation (Ahead-Of-Time)

Some modern systems compile bytecode to native code **before** execution
(e.g. Android ART, GraalVM native-image, Go).

```
Source ──[Compiler]──► Bytecode ──[AOT Compiler]──► Native executable
```

---

## 5. Language Classification Summary

| Category | Chinese | Examples | Key trait |
|----------|---------|----------|-----------|
| Compiled | 编译型 | C, C++, Go, Rust | Produces native executable |
| Interpreted | 解释型 | Python, Ruby, PHP | Executes line by line |
| Hybrid | 混合型 | Java, C#, Kotlin | Bytecode + VM/JIT |

> Exam trap: Java is **not** a purely compiled language. It compiles to
> bytecode, which is then interpreted or JIT-compiled by the JVM.

---

## 6. Worked Examples

**Example 1:** A program has 1000 lines. Compilation takes 2 seconds.
Execution of the compiled program takes 0.5 seconds. Interpretation
takes 0.01 seconds per line. Compare total run times.

```
Compiled:  2 + 0.5 = 2.5 seconds (first run)
           0.5 seconds (subsequent runs, no recompilation)

Interpreted: 1000 × 0.01 = 10 seconds (every run)
```

**Example 2:** A hybrid language compiles to bytecode in 1 second.
Bytecode interpretation takes 0.005 seconds per line. JIT compilation
of hot code takes 0.3 seconds but reduces execution time to 0.002
seconds per line for 80% of the code. Total for 1000 lines?

```
Without JIT: 1 + 1000 × 0.005 = 6 seconds
With JIT:    1 + 0.3 + 800 × 0.002 + 200 × 0.005 = 1 + 0.3 + 1.6 + 1.0 = 3.9 seconds
```

---

## 7. Exam-Style Questions

**Q1.** Which of the following is an advantage of compilation over
interpretation?
A. Easier debugging  B. Faster execution  C. Smaller code size  D. Better portability
> Answer: B.

**Q2.** Java is best classified as:
A. purely compiled  B. purely interpreted  C. hybrid (compiled to bytecode, then interpreted/JIT)  D. assembly language
> Answer: C.

**Q3.** An interpreter detects errors:
A. before execution  B. during execution, when the error line is reached  C. only at the end  D. never
> Answer: B.

**Q4.** JIT compilation improves performance by:
A. compiling the entire program before execution  B. compiling frequently-executed bytecode to native code at run time  C. interpreting faster  D. reducing source code size
> Answer: B.

**Q5.** Which language produces a standalone executable file?
A. Python  B. Java  C. C  D. JavaScript
> Answer: C.

**Q6.** The main disadvantage of interpretation is:
A. large executable size  B. slow execution speed  C. early error detection  D. difficult debugging
> Answer: B.

---

## 8. Further Reading

* Aho, Lam, Sethi, Ullman — *Compilers: Principles, Techniques, and
  Tools* (the "Dragon Book"), ch. 1.
* Sebesta — *Concepts of Programming Languages*, ch. 1.

---

## 9. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Compiler | 编译程序 / 编译器 | 01 |
| Interpreter | 解释程序 / 解释器 | 01 |
| Compilation | 编译 | 01 |
| Interpretation | 解释 | 01 |
| Bytecode | 字节码 | 01 |
| Virtual Machine (VM) | 虚拟机 | 01 |
| JIT compilation | 即时编译 | 01 |
| AOT compilation | 预先编译 | 01 |
| Object code | 目标代码 | 01 |
| Executable | 可执行文件 | 01 |
| Hybrid | 混合型 | 01 |
