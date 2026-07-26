# 05 — Symbol Tables

> Syllabus reference: P43–P47
>
> The **symbol table** is the compiler's central database. Every
> identifier — variable, function, type, label — must be recorded with
> its attributes so that later phases can look them up. The exam tests
> symbol table structure, scope handling, and implementation choices.

---

## 1. What Is a Symbol Table?

A symbol table maps **identifiers (names)** to their **attributes**:

| Attribute | Example |
|-----------|---------|
| Name | `x`, `foo`, `Point` |
| Kind | variable, function, type, constant |
| Type | `int`, `float*`, `char[]` |
| Scope level | global, local (depth 1), local (depth 2) |
| Storage class | auto, static, extern, register |
| Offset / address | stack offset, heap address |
| Size | 4 bytes, 8 bytes |
| Other | number of parameters, return type, visibility |

```
┌──────────┬──────┬──────┬───────┬────────┬────────┬──────┐
│  Name    │ Kind │ Type │ Scope │ Offset │ Size   │ ...  │
├──────────┼──────┼──────┼───────┼────────┼────────┼──────┤
│  x       │ var  │ int  │ 1     │ −4     │ 4      │      │
│  foo     │ func │ int  │ 0     │ —      │ —      │ 2par │
│  Point   │ type │ struct│ 0    │ —      │ 8      │      │
└──────────┴──────┴──────┴───────┴────────┴────────┴──────┘
```

---

## 2. Scope Handling (作用域处理)

### 2.1 The problem

Most languages allow **nested scopes**. An inner scope can declare a
variable with the same name as an outer one (shadowing). The symbol
table must correctly resolve which declaration each reference refers to.

### 2.2 Approach 1: One table with scope numbers

Every entry has a **scope level**. On scope exit, delete all entries at
that level.

```
Enter scope 0:  x (scope=0)
Enter scope 1:  x (scope=1)    ← shadows outer x
Exit scope 1:   delete x (scope=1)
Now x refers to scope=0 again
```

### 2.3 Approach 2: Separate table per scope (scope stack)

Each scope has its own symbol table. A **stack** of tables is
maintained.

```
Scope stack:
  [global table: x → int]
  [local table:  x → float]    ← on top, found first

Lookup: search top table first, then next, then global.
On scope exit: pop the top table.
```

### 2.4 Approach 3: Tree-structured symbol tables

For languages with module/package nesting (e.g. Java classes, C++
namespaces), symbol tables form a **tree** reflecting the program
structure.

```
Global
├── ClassA
│   ├── field x
│   └── method foo
└── ClassB
    └── field y
```

---

## 3. Implementation Choices

### 3.1 Data structures

| Structure | Lookup | Insert | Pros | Cons |
|-----------|--------|--------|------|------|
| **Unordered array** | O(n) | O(1) | Simple | Slow for large tables |
| **Ordered array** | O(log n) binary search | O(n) shift | Fast lookup | Slow insert |
| **Hash table** | O(1) avg | O(1) avg | Fast both | Hash collisions; memory overhead |
| **Binary search tree** | O(log n) avg | O(log n) avg | Ordered traversal | Worst case O(n) if unbalanced |

> Exam tip: **hash table** is the most common implementation in real
> compilers because insert and lookup are both O(1) on average.

### 3.2 Hash table for symbol tables

```
Hash function: h(name) = name % TABLE_SIZE

Bucket 0: → [entry: "x"] → [entry: "max"]
Bucket 1: → [entry: "foo"]
Bucket 2: → (empty)
Bucket 3: → [entry: "y"] → [entry: "count"]
...
```

Collision resolution: **chaining** (linked list per bucket) or **open
addressing** (linear probing, etc.).

---

## 4. Symbol Table Operations

| Operation | Description |
|-----------|-------------|
| **Insert(name, attributes)** | Add a new identifier; error if already in current scope |
| **Lookup(name)** | Find the identifier; return attributes or "not found" |
| **Delete(name)** | Remove entries for a scope being exited |
| **Modify(name, attr, value)** | Update an attribute (e.g. set offset after allocation) |
| **Traverse()** | Iterate over all entries (for code generation) |

---

## 5. When Each Phase Uses the Symbol Table

| Phase | Operation |
|-------|-----------|
| **Lexical analysis** | Does NOT use the symbol table (tokens only) |
| **Syntax analysis** | Does NOT use the symbol table (structure only) |
| **Semantic analysis** | Insert declarations; lookup references; type check |
| **Intermediate code gen** | Lookup types and offsets for code generation |
| **Target code gen** | Lookup sizes, offsets, register assignments |
| **Optimisation** | May read/update attributes |

> Exam tip: lexical and syntax analysis do **not** use the symbol
> table. Semantic analysis is the first phase to heavily use it.

---

## 6. Worked Example

Given the following C code:

```c
int x = 10;              // global
void foo(int a) {        // function
    int x = 20;          // local, shadows global
    {                    // inner block
        int y = x + a;  // x refers to local x (scope 2)
    }                    // y destroyed
    // x is still 20
}
```

Symbol table state at the line `int y = x + a`:

| Name | Kind | Type | Scope | Offset |
|------|------|------|-------|--------|
| x | var | int | 0 (global) | — |
| foo | func | void | 0 | — |
| a | param | int | 1 | +4 |
| x | var | int | 1 (local) | −4 |
| y | var | int | 2 (inner) | −8 |

Lookup `x` in scope 2: not found → scope 1: found (local x = 20).

---

## 7. Exam-Style Questions

**Q1.** Which phase first uses the symbol table?
A. Lexical analysis  B. Syntax analysis  C. Semantic analysis  D. Code generation
> Answer: C.

**Q2.** The most efficient data structure for a symbol table is:
A. unordered array  B. ordered array  C. hash table  D. linked list
> Answer: C (O(1) average for both insert and lookup).

**Q3.** When a scope is exited, the symbol table should:
A. keep all entries  B. delete entries of that scope  C. delete all entries  D. do nothing
> Answer: B.

**Q4.** An inner-scope variable with the same name as an outer-scope
variable:
A. causes a compilation error  B. shadows the outer variable  C. merges with the outer variable  D. is ignored
> Answer: B.

**Q5.** The symbol table stores all EXCEPT:
A. variable names  B. types  C. source code comments  D. scope levels
> Answer: C (comments are discarded by the lexical analyser).

**Q6.** In a scope-stack symbol table, lookup searches:
A. only the global table  B. only the top table  C. from the top table downward  D. all tables in parallel
> Answer: C (innermost scope first).

---

## 8. Further Reading

* Aho et al. — *Compilers* (Dragon Book), §2.7.
* Cooper & Torczon — *Engineering a Compiler*, ch. 5.

---

## 9. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Symbol table | 符号表 | 05 |
| Identifier | 标识符 | 05 |
| Scope | 作用域 | 05 |
| Scope level | 作用域层次 | 05 |
| Shadow | 遮蔽 / 屏蔽 | 05 |
| Hash table | 哈希表 / 散列表 | 05 |
| Storage class | 存储类别 | 05 |
| Offset | 偏移量 | 05 |
| Declaration | 声明 | 05 |
| Reference | 引用 / 使用 | 05 |
