# 04 — Compiler Basics

> Syllabus reference: P38–P42
>
> A **compiler** is not a monolithic program — it is a pipeline of
> distinct phases, each performing a well-defined transformation.
> Understanding the overall architecture is the foundation for chapters
> 05–12, which dive into each phase in detail.

---

## 1. The Compilation Pipeline

```
Source code
    │
    ▼
┌──────────────┐
│ Lexical      │  → Token stream
│ Analysis     │
└──────┬───────┘
       │
┌──────▼───────┐
│ Syntax       │  → Parse tree / AST
│ Analysis     │
└──────┬───────┘
       │
┌──────▼───────┐
│ Semantic     │  → Annotated AST
│ Analysis     │
└──────┬───────┘
       │
┌──────▼───────┐
│ Intermediate │  → IR (three-address code, etc.)
│ Code Gen     │
└──────┬───────┘
       │
┌──────▼───────┐
│ Code         │  → Optimised IR
│ Optimisation │
└──────┬───────┘
       │
┌──────▼───────┐
│ Target Code  │  → Assembly / machine code
│ Generation   │
└──────┬───────┘
       │
       ▼
  Executable
```

---

## 2. The Phases in Detail

### 2.1 Lexical analysis (词法分析)

- Reads the source character by character.
- Groups characters into **tokens** (keywords, identifiers, literals,
  operators, delimiters).
- Removes whitespace and comments.

```
Input:  "int x = 42;"
Output: [KW_int] [ID_x] [OP_eq] [NUM_42] [SEMI]
```

### 2.2 Syntax analysis (语法分析 / 解析)

- Takes the token stream and builds a **parse tree** (or AST) according
  to the grammar rules.
- Detects syntax errors (malformed structures).

```
Tokens: [ID_x] [OP_eq] [NUM_42] [SEMI]
Parse tree:
      Assignment
      /   |    \
    ID_x  =   NUM_42
```

### 2.3 Semantic analysis (语义分析)

- Checks **meaning**: type checking, scope resolution, declaration
  before use.
- Builds / updates the **symbol table**.
- Detects semantic errors (type mismatch, undeclared variable).

```
Error: "cannot assign string to int variable x"
```

### 2.4 Intermediate code generation (中间代码生成)

- Translates the AST into a machine-independent **intermediate
  representation (IR)**.
- Common forms: three-address code, quadruples, triples, SSA.

```
x = 42  →  t1 = 42
            x = t1
```

### 2.5 Code optimisation (代码优化)

- Transforms the IR to make the program **faster** or **smaller**
  without changing its behaviour.
- Examples: constant folding, dead code elimination, loop optimisation.

```
Before:  t1 = 2 * 3     After:  t1 = 6
         x = t1                  x = t1
```

### 2.6 Target code generation (目标代码生成)

- Translates the optimised IR into **assembly** or **machine code** for
  the target architecture.
- Handles register allocation, instruction selection, instruction
  scheduling.

```
x = 42  →  MOV EAX, 42
            MOV [x], EAX
```

---

## 3. Front-End vs Back-End

```
┌─────────────────────────────────┐
│          FRONT-END              │
│  (language-dependent)           │
│                                 │
│  Lexical analysis               │
│  Syntax analysis                │
│  Semantic analysis              │
│  Intermediate code generation   │
└──────────────┬──────────────────┘
               │ IR
┌──────────────▼──────────────────┐
│          BACK-END               │
│  (machine-dependent)            │
│                                 │
│  Code optimisation              │
│  Target code generation         │
└─────────────────────────────────┘
```

| Part | Depends on | Portable? |
|------|-----------|-----------|
| Front-end | Source language only | Reusable across targets |
| Back-end | Target machine only | Reusable across languages |

> This separation means: **n languages × m targets = n + m** modules,
> not n × m. This is the key insight behind LLVM, GCC, and .NET.

---

## 4. Symbol Table and Error Handler

### 4.1 Symbol table (符号表)

Used by **all phases** to store information about identifiers:

| Phase | What it looks up / stores |
|-------|--------------------------|
| Lexical | — (not used) |
| Syntax | — (not used) |
| Semantic | Type, scope, declaration info |
| Code gen | Size, offset, storage class |

### 4.2 Error handler (出错处理)

| Phase | Typical errors |
|-------|---------------|
| Lexical | Invalid characters, malformed tokens |
| Syntax | Missing semicolons, unbalanced parentheses |
| Semantic | Type mismatch, undeclared variable |
| Other | Code too large, register overflow |

---

## 5. Passes vs Phases

| Concept | Chinese | Meaning |
|---------|---------|---------|
| **Phase** | 阶段 | A logical step in compilation |
| **Pass** | 遍 | One complete read of the source / IR |

- A compiler can have **multiple phases in one pass** or **one phase
  across multiple passes**.
- **Single-pass compiler**: reads the source once; requires forward
  declarations (e.g. Pascal, C with care).
- **Multi-pass compiler**: reads the source/IR multiple times; allows
  forward references and more optimisation (e.g. most modern compilers).

---

## 6. Exam-Style Questions

**Q1.** Which phase detects a type mismatch error?
A. Lexical  B. Syntax  C. Semantic  D. Code generation
> Answer: C.

**Q2.** The front-end of a compiler is dependent on:
A. the target machine  B. the source language  C. both  D. neither
> Answer: B.

**Q3.** Lexical analysis converts source code into:
A. parse tree  B. tokens  C. IR  D. machine code
> Answer: B.

**Q4.** A single-pass compiler:
A. reads the source multiple times  B. reads the source once  C. has no optimisation  D. cannot detect errors
> Answer: B.

**Q5.** The symbol table is primarily used by:
A. lexical analysis only  B. syntax analysis only  C. semantic analysis and code generation  D. code optimisation only
> Answer: C.

**Q6.** Code optimisation occurs:
A. before lexical analysis  B. between semantic analysis and target code generation  C. after target code generation  D. only in interpreters
> Answer: B.

---

## 7. Further Reading

* Aho, Lam, Sethi, Ullman — *Compilers* (Dragon Book), ch. 1.
* Cooper & Torczon — *Engineering a Compiler*, ch. 1.

---

## 8. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Lexical analysis | 词法分析 | 04 |
| Syntax analysis | 语法分析 | 04 |
| Semantic analysis | 语义分析 | 04 |
| Intermediate code | 中间代码 | 04 |
| Code optimisation | 代码优化 | 04 |
| Target code generation | 目标代码生成 | 04 |
| Front-end | 前端 | 04 |
| Back-end | 后端 | 04 |
| Symbol table | 符号表 | 04 |
| Parse tree | 解析树 / 语法树 | 04 |
| AST | 抽象语法树 | 04 |
| Token | 记号 / 单词 | 04 |
| Pass | 遍 | 04 |
| Phase | 阶段 | 04 |
