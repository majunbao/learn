# 06 — Lexical, Syntax, Semantic Analysis & Target Code Generation

> Syllabus reference: P48–P63
>
> These are the four core analysis/transformations of a compiler. Each
> has a well-defined input, output, and set of techniques. This chapter
> ties them together; chapters 09–11 dive deeper into the formal
> foundations (regular expressions, finite automata, context-free
> grammars).

---

## 1. Lexical Analysis (词法分析)

### 1.1 Task

Convert a **character stream** into a **token stream**.

```
Input:  "if (x <= 10) { y = x + 1; }"
Output: [KW_if] [LPAREN] [ID_x] [OP_le] [NUM_10] [RPAREN]
        [LBRACE] [ID_y] [OP_eq] [ID_x] [OP_plus] [NUM_1] [SEMI] [RBRACE]
```

### 1.2 Token classification

| Token type | Chinese | Examples |
|-----------|---------|----------|
| Keywords | 关键字 / 保留字 | `if`, `while`, `int`, `return` |
| Identifiers | 标识符 | `x`, `foo`, `myVar` |
| Literals / Constants | 常量 | `42`, `3.14`, `"hello"` |
| Operators | 运算符 | `+`, `<=`, `==`, `&&` |
| Delimiters | 界符 / 分隔符 | `;`, `{`, `(`, `,` |

### 1.3 How it works

1. Read characters one at a time.
2. Use the **longest match** principle: keep reading as long as the
   characters form a valid token.
3. On failure, backtrack to the longest valid match.

```
Input: "++x"
Longest match: "++" → OP_increment (not two OP_plus)
```

### 1.4 Lexical errors

| Error type | Example | Handling |
|-----------|---------|----------|
| Invalid character | `$` in C | Report and skip |
| Unterminated string | `"hello` | Report error |
| Illegal number format | `3.4.5` | Report error |

---

## 2. Syntax Analysis (语法分析 / Parsing)

### 2.1 Task

Convert the **token stream** into a **parse tree** (or AST) according
to the grammar rules.

```
Tokens: [ID_x] [OP_eq] [ID_y] [OP_plus] [NUM_1] [SEMI]

Parse tree:
        Assignment
       /    |     \
    ID_x   =    AddExpr
                /    \
            ID_y   NUM_1
```

### 2.2 Parsing strategies

| Strategy | Chinese | Direction | Grammar class | Example |
|----------|---------|-----------|---------------|---------|
| **Top-down** | 自顶向下 | Root → leaves | LL(k) | Recursive descent |
| **Bottom-up** | 自底向上 | Leaves → root | LR(k) | SLR, LALR, LR(1) |

### 2.3 Top-down parsing (LL)

- Start from the start symbol; try to match the input by expanding
  non-terminals.
- **Recursive descent**: one function per non-terminal.
- **Predictive parsing (LL(1))**: use one lookahead token to choose
  which production to apply.
- Requires **no left recursion** and **no ambiguity** in the grammar.

```
For production: E → T | T + E
LL(1) table: if lookahead is '+' → choose T + E
             else → choose T
```

### 2.4 Bottom-up parsing (LR)

- Start from the input tokens; try to **reduce** them to the start
  symbol.
- Uses a **shift-reduce** algorithm with a stack.
- More powerful than LL; handles a larger class of grammars.

| Variant | Power | Table size | Use |
|---------|-------|-----------|-----|
| **SLR(1)** | Weakest | Small | Simple grammars |
| **LALR(1)** | Medium | Medium | **Yacc/Bison** (most common) |
| **LR(1)** | Most powerful | Large | Full LR grammars |

### 2.5 Shift-reduce conflicts

| Conflict | Cause | Example |
|----------|-------|---------|
| **Shift-reduce conflict** | Can either shift or reduce | Dangling else |
| **Reduce-reduce conflict** | Two different reductions possible | Ambiguous grammar |

> Exam tip: LALR(1) is what Yacc/Bison uses. Most programming language
> grammars are LALR(1).

---

## 3. Semantic Analysis (语义分析)

### 3.1 Task

Check **meaning** — things the grammar cannot express:

| Check | Chinese | Example |
|-------|---------|---------|
| Type checking | 类型检查 | `int x = "hello";` → error |
| Declaration before use | 先声明后使用 | `y = x;` where x is undeclared |
| Scope rules | 作用域规则 | Accessing a private field |
| Parameter count | 参数个数 | `foo(1,2)` but `foo` takes 3 args |
| Return type | 返回类型 | Missing return in non-void function |

### 3.2 Type checking

| System | Chinese | When | Example |
|--------|---------|------|---------|
| **Static type checking** | 静态类型检查 | Compile time | Java, C, C++ |
| **Dynamic type checking** | 动态类型检查 | Run time | Python, Ruby |

### 3.3 Type conversion

| Conversion | Chinese | Automatic? | Example |
|-----------|---------|-----------|---------|
| **Widening** | 宽化转换 | Yes (safe) | `int → float` |
| **Narrowing** | 窄化转换 | No (may lose data) | `float → int` (needs cast) |
| **Coercion** | 隐式转换 | Language-dependent | `int + float → float` |

---

## 4. Target Code Generation (目标代码生成)

### 4.1 Task

Translate the optimised IR into **target machine code** (or assembly).

### 4.2 Key sub-problems

| Sub-problem | Chinese | Description |
|-------------|---------|-------------|
| **Instruction selection** | 指令选择 | Choose machine instructions for each IR operation |
| **Register allocation** | 寄存器分配 | Map virtual registers / temporaries to physical registers |
| **Instruction scheduling** | 指令调度 | Reorder instructions to avoid pipeline stalls |

### 4.3 Register allocation

The most studied sub-problem. Number of physical registers is limited;
the compiler must decide which values stay in registers and which are
**spilled** to memory.

| Algorithm | Approach | Quality |
|-----------|----------|---------|
| **Linear scan** | One pass; fast | Good for JIT |
| **Graph colouring** | NP-hard; heuristic | Optimal (near-optimal) |

Graph colouring:
1. Build an **interference graph**: nodes = variables; edge = variables
   live at the same time.
2. Try to colour the graph with K colours (K = number of registers).
3. If a variable cannot be coloured → **spill** to memory.

### 4.4 Output forms

| Form | Chinese | Description |
|------|---------|-------------|
| **Assembly code** | 汇编代码 | Needs assembler to produce object code |
| **Relocatable object code** | 可重定位目标代码 | Needs linker |
| **Absolute machine code** | 绝对机器代码 | Can be loaded and executed directly |

---

## 5. Exam-Style Questions

**Q1.** Lexical analysis converts:
A. characters → tokens  B. tokens → parse tree  C. parse tree → IR  D. IR → machine code
> Answer: A.

**Q2.** Bottom-up parsing is also called:
A. LL parsing  B. LR parsing  C. predictive parsing  D. recursive descent
> Answer: B.

**Q3.** Type checking is performed during:
A. lexical analysis  B. syntax analysis  C. semantic analysis  D. code generation
> Answer: C.

**Q4.** A shift-reduce conflict occurs when:
A. the grammar is left-recursive  B. the parser can either shift or reduce  C. there are too many tokens  D. the symbol table is full
> Answer: B.

**Q5.** Register allocation by graph colouring uses:
A. a dependency graph  B. an interference graph  C. a call graph  D. a control-flow graph
> Answer: B.

**Q6.** The "longest match" principle in lexical analysis means:
A. match the longest keyword  B. keep reading characters as long as they form a valid token  C. always match two characters  D. prefer shorter matches
> Answer: B.

---

## 6. Further Reading

* Aho et al. — *Compilers* (Dragon Book), ch. 2–3, 8–9.
* Appel — *Modern Compiler Implementation*, ch. 2–4, 11.

---

## 7. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Lexical analysis | 词法分析 | 06 |
| Syntax analysis / Parsing | 语法分析 | 06 |
| Semantic analysis | 语义分析 | 06 |
| Target code generation | 目标代码生成 | 06 |
| Token | 记号 / 单词 | 06 |
| Parse tree | 解析树 / 语法树 | 06 |
| AST | 抽象语法树 | 06 |
| Top-down parsing | 自顶向下分析 | 06 |
| Bottom-up parsing | 自底向上分析 | 06 |
| LL parsing | LL分析 | 06 |
| LR parsing | LR分析 | 06 |
| Shift-reduce | 移进-归约 | 06 |
| Type checking | 类型检查 | 06 |
| Register allocation | 寄存器分配 | 06 |
| Instruction selection | 指令选择 | 06 |
| Spill | 溢出 / 淘汰 | 06 |
