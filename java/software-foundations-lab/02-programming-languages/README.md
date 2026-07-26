# 02 — Programming Languages & Compilers

> 12 chapters covering the complete programming-languages and compiler
> section of the Chinese software engineer exam syllabus (P2–P130),
> rewritten in textbook-level depth. Each chapter is self-contained:
> theory → worked examples → exam-style Q&A → further reading.

## Roadmap

| #  | File                                                | Syllabus  | Topic |
|----|-----------------------------------------------------|-----------|-------|
| 01 | [`01-compiler-interpreter.md`](01-compiler-interpreter.md) | P2–P7   | Compilers vs interpreters, hybrid systems |
| 02 | [`02-language-components.md`](02-language-components.md)   | P8–P19  | Data types, operators, control flow, subprograms |
| 03 | [`03-pass-by-value-ref.md`](03-pass-by-value-ref.md)      | P20–P37 | Call by value, call by reference, parameter passing |
| 04 | [`04-compiler-basics.md`](04-compiler-basics.md)          | P38–P42 | Compiler phases, front-end / back-end |
| 05 | [`05-symbol-table.md`](05-symbol-table.md)                | P43–P47 | Symbol table structure, scope, storage |
| 06 | [`06-analysis-codegen.md`](06-analysis-codegen.md)        | P48–P63 | Lexical, syntax, semantic analysis; target code generation |
| 07 | [`07-errors-exceptions.md`](07-errors-exceptions.md)      | P64–P69 | Compile-time vs run-time errors, exception handling |
| 08 | [`08-intermediate-code.md`](08-intermediate-code.md)      | P70–P76 | Three-address code, quadruples, triples, DAG |
| 09 | [`09-regular-expressions.md`](09-regular-expressions.md)  | P77–P82 | Regular expressions, operators, equivalence |
| 10 | [`10-finite-automata.md`](10-finite-automata.md)          | P83–P103| DFA, NFA, NFA→DFA conversion, minimisation |
| 11 | [`11-context-free-grammar.md`](11-context-free-grammar.md) | P104–P113 | CFG, derivations, parse trees, ambiguity |
| 12 | [`12-expression-notation.md`](12-expression-notation.md)   | P114–P130 | Infix, prefix, postfix; expression evaluation |

## Suggested Reading Order

- **Theory-first path**: 01 → 04 → 06 → 09 → 10 → 11 → 08 → 12.
- **Language-focused path**: 02 → 03 → 07 → 05.
- **Compiler crammer**: 04 → 05 → 06 → 08 → 09 → 10 → 11.

## How Each Chapter Is Structured

```
1. Concept / definition
2. Diagrams or tables
3. Worked examples
4. Algorithms / formulas
5. Exam-style Q&A with answers
6. Further reading (books / papers / online docs)
```

## Why This Folder Has No `pom.xml`

It contains only Markdown. Maven would only get in the way. The folder
is **not** registered in the parent `pom.xml`'s `<modules>` list.
