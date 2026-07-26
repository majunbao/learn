# 10 — Finite Automata (有限自动机)

> Syllabus reference: P83–P103
>
> Finite automata are the **computational model** behind lexical
> analysis. The exam heavily tests DFA/NFA definitions, NFA→DFA
> conversion (subset construction), and DFA minimisation. This is one
> of the most calculation-intensive topics.

---

## 1. Deterministic Finite Automaton (DFA / 确定的有限自动机)

### 1.1 Formal definition

A DFA is a 5-tuple **M = (Q, Σ, δ, q₀, F)**:

| Component | Chinese | Meaning |
|-----------|---------|---------|
| Q | 状态集 | Finite set of states |
| Σ | 字母表 | Input alphabet |
| δ | 转移函数 | Q × Σ → Q (exactly one next state) |
| q₀ | 初态 | Start state (exactly one) |
| F | 终态集 / 接受状态集 | Set of accepting states |

### 1.2 Key property

For every state and every input symbol, there is **exactly one**
transition. No ambiguity.

### 1.3 Example

DFA that accepts strings over {0,1} ending with "01":

```
States: {A, B, C}
Start: A
Accept: {C}

Transitions:
  A --0--> B
  A --1--> A
  B --0--> B
  B --1--> C
  C --0--> B
  C --1--> A
```

Transition table:

| State | 0 | 1 |
|-------|---|---|
| →A | B | A |
| B | B | C |
| *C | B | A |

(`→` = start, `*` = accept)

---

## 2. Nondeterministic Finite Automaton (NFA / 不确定的有限自动机)

### 2.1 Formal definition

An NFA is a 5-tuple **M = (Q, Σ, δ, q₀, F)**, but δ allows:

- **Multiple transitions** from the same state on the same symbol
- **ε-transitions** (move without consuming input)

```
δ: Q × (Σ ∪ {ε}) → 2^Q    (set of possible next states)
```

### 2.2 Key differences from DFA

| Feature | DFA | NFA |
|---------|-----|-----|
| Transitions per (state, symbol) | Exactly 1 | 0, 1, or many |
| ε-transitions | Not allowed | Allowed |
| Computation path | Unique | May branch |
| Acceptance | One path reaches accept | Any path reaches accept |

### 2.3 Example

NFA that accepts strings ending with "01":

```
→ (A) ─0─→ (B) ─1─→ *((C))
         ε↑
```

Or more simply:

```
→ (A) ─0─→ (B) ─1─→ *((C))
  A also has: A --0--> A, A --1--> A
```

---

## 3. NFA → DFA Conversion (子集构造法 / Subset Construction)

### 3.1 Key idea

Each DFA state corresponds to a **set of NFA states**. The DFA
simulates "being in all NFA states simultaneously".

### 3.2 ε-closure

**ε-closure(T)** = set of states reachable from T by following only
ε-transitions (including T itself).

```
Example:
  A ─ε─→ B ─ε─→ C
  ε-closure({A}) = {A, B, C}
```

### 3.3 Algorithm

```
1. Compute ε-closure({q₀}) → DFA start state
2. For each unmarked DFA state T:
     For each input symbol a:
       U = ε-closure(move(T, a))
       If U ≠ ∅: add transition T ─a─→ U
       If U is new: add U as a DFA state
3. Any DFA state containing an NFA accept state is a DFA accept state
```

### 3.4 Worked example

NFA:
```
→ (0) ─a─→ (1) ─b─→ *((2))
  (0) ─b─→ (2)
```

Step 1: Start = ε-closure({0}) = {0} → DFA state A

Step 2: Process A = {0}:
- move({0}, a) = {1} → ε-closure = {1} → DFA state B
- move({0}, b) = {2} → ε-closure = {2} → DFA state C (accept)

Step 3: Process B = {1}:
- move({1}, a) = {} → no transition
- move({1}, b) = {2} → ε-closure = {2} → DFA state C

Step 4: Process C = {2}:
- move({2}, a) = {} → no transition
- move({2}, b) = {} → no transition

DFA transition table:

| DFA state | NFA states | a | b |
|-----------|-----------|---|---|
| →A | {0} | B | C |
| B | {1} | — | C |
| *C | {2} | — | — |

---

## 4. DFA Minimisation (DFA最小化 / Hopcroft算法)

### 4.1 Key idea

Two states are **equivalent** (等价) if for every input string, they
either both accept or both reject. Equivalent states can be merged.

### 4.2 Algorithm (table-filling / partition method)

```
1. Split states into two groups: accept vs non-accept
2. Repeat until no changes:
     For each group G and each symbol a:
       If states in G go to different groups on a → split G
3. Merge each group into a single state
```

### 4.3 Worked example

DFA:

| State | a | b |
|-------|---|---|
| →A | B | C |
| B | A | D |
| C | D | A |
| *D | D | D |

Step 1: Split into {A, B, C} (non-accept) and {D} (accept)

Step 2: Check {A, B, C}:
- On 'a': A→B, B→A, C→D → C goes to different group → split {A,B} and {C}

Step 3: Check {A, B}:
- On 'a': A→B, B→A → both in {A,B} ✓
- On 'b': A→C, B→D → different groups → split {A} and {B}

Final groups: {A}, {B}, {C}, {D} → already minimal.

### 4.4 Distinguishable vs Indistinguishable

| Concept | Chinese | Meaning |
|---------|---------|---------|
| Distinguishable | 可区分 | States that can be told apart |
| Indistinguishable | 不可区分 / 等价 | States that behave identically |

---

## 5. Equivalence of DFA and NFA

| Property | Detail |
|----------|--------|
| DFA ⊆ NFA | Every DFA is trivially an NFA |
| NFA → DFA | Always possible (subset construction) |
| Expressive power | **Equal** — both recognise exactly the regular languages |
| Size | NFA may be exponentially smaller than equivalent DFA |

> Exam tip: DFA and NFA have the **same expressive power**. The
> difference is convenience, not capability.

---

## 6. Chomsky Hierarchy Context

| Level | Grammar | Automaton | Language |
|-------|---------|-----------|----------|
| Type 3 | Regular | DFA / NFA | Regular |
| Type 2 | Context-free | PDA | Context-free |
| Type 1 | Context-sensitive | LBA | Context-sensitive |
| Type 0 | Unrestricted | TM | Recursively enumerable |

Finite automata sit at **Type 3** — the simplest level.

---

## 7. Exam-Style Questions

**Q1.** In a DFA, for each state and input symbol, the number of
transitions is:
A. 0 or 1  B. exactly 1  C. 0, 1, or many  D. at least 1
> Answer: B.

**Q2.** An NFA can have:
A. only one start state  B. ε-transitions  C. at most one transition per symbol  D. no accept states
> Answer: B.

**Q3.** The subset construction converts:
A. DFA → NFA  B. NFA → DFA  C. DFA → minimal DFA  D. regular expression → NFA
> Answer: B.

**Q4.** DFA and NFA have:
A. different expressive power  B. the same expressive power  C. NFA is more powerful  D. DFA is more powerful
> Answer: B.

**Q5.** In DFA minimisation, two states are equivalent if:
A. they have the same name  B. they behave identically for all inputs  C. they are both accept states  D. they have the same number of transitions
> Answer: B.

**Q6.** The ε-closure of a state includes:
A. only the state itself  B. all states reachable via ε-transitions  C. all states reachable via any transition  D. only accept states
> Answer: B.

---

## 8. Further Reading

* Hopcroft, Motwani, Ullman — *Introduction to Automata Theory*,
  ch. 2–4.
* Aho et al. — *Compilers* (Dragon Book), §3.6–3.9.

---

## 9. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Finite automaton | 有限自动机 | 10 |
| DFA | 确定的有限自动机 | 10 |
| NFA | 不确定的有限自动机 | 10 |
| State | 状态 | 10 |
| Transition | 转移 / 转换 | 10 |
| Start state / Initial state | 初态 / 开始状态 | 10 |
| Accept state / Final state | 终态 / 接受状态 | 10 |
| ε-transition | ε转移 / 空转移 | 10 |
| ε-closure | ε闭包 | 10 |
| Subset construction | 子集构造法 | 10 |
| DFA minimisation | DFA最小化 | 10 |
| Distinguishable | 可区分 | 10 |
| Indistinguishable / Equivalent | 不可区分 / 等价 | 10 |
| Regular language | 正规语言 / 正则语言 | 10 |
