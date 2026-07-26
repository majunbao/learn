# 10 — Functional Dependencies & Attribute Closure

> Syllabus reference: P67–P81
>
> Functional dependencies (FDs) are the algebra of "this column
> determines that column". They are the foundation of normalisation
> (chapter 11) and the most-tested calculation on the exam. Master
> Armstrong's axioms and the **attribute closure algorithm** — the
> rest follows.

---

## 1. Definition

Let `R(U)` be a relation with attribute set `U`. Given `X, Y ⊆ U`, we say

> **X → Y**   ("X functionally determines Y")

iff for every two tuples `t1, t2` in any legal instance of R,

> if `t1[X] = t2[X]` then `t1[Y] = t2[Y]`.

In plain English: whenever the X-columns agree, the Y-columns must
also agree.

### Trivial vs. non-trivial

* **Trivial FD** — `Y ⊆ X` (always true). E.g. `(A,B) → A`.
* **Non-trivial FD** — `Y ⊄ X`.
* **Completely non-trivial FD** — `X ∩ Y = ∅`.

### Partial vs. full functional dependency

For an FD `X → Y` where X is a **composite** attribute set:

* **Full FD (完全函数依赖)**: no proper subset of X also determines Y.
  Notation: `X →F Y`.
* **Partial FD (部分函数依赖)**: some `X' ⊂ X` already determines Y.
  Notation: `X →P Y`.

> Exam example: `R(sid, cid, grade, sname)` with FDs `sid → sname` and
> `(sid, cid) → grade`.
> `(sid, cid) → sname` is a **partial** FD (because `sid` alone
> already determines `sname`). Partial FDs cause **2NF violations** —
> see chapter 11.

### Transitive functional dependency

If `X → Y`, `Y → Z`, and `Y ⊄ X` and `X ⊄ Y`, then `X → Z` is a
**transitive FD**. Transitive FDs cause **3NF violations**.

---

## 2. Armstrong's Axioms

The three **sound and complete** inference rules for FDs:

| Rule          | Statement                                          |
|---------------|----------------------------------------------------|
| **Reflexivity** | If `Y ⊆ X`, then `X → Y`.                        |
| **Augmentation** | If `X → Y`, then `XZ → YZ` for any Z.            |
| **Transitivity** | If `X → Y` and `Y → Z`, then `X → Z`.            |

From these three you can derive the secondary rules used in practice:

| Rule             | Statement                                           |
|------------------|-----------------------------------------------------|
| **Union**        | If `X → Y` and `X → Z`, then `X → YZ`.              |
| **Decomposition**| If `X → YZ`, then `X → Y` and `X → Z`.              |
| **Pseudo-transitivity** | If `X → Y` and `WY → Z`, then `WX → Z`.      |

---

## 3. Attribute Closure  `X⁺`

`X⁺` (with respect to a set of FDs F) is **the set of all attributes
that can be functionally derived from X using F**.

### The standard algorithm — memorise it

```
1. result ← X
2. repeat
       for every FD  A → B  in F:
           if A ⊆ result then
               result ← result ∪ B
   until result stops growing
3. return result   // this is X⁺
```

### Why it matters
With `X⁺` you can answer almost every FD question:

| Question                                  | Test                                        |
|-------------------------------------------|---------------------------------------------|
| Is `X → Y` implied by F?                  | Yes iff `Y ⊆ X⁺`.                           |
| Is X a **super key** of R(U)?             | Yes iff `X⁺ = U`.                           |
| Is X a **candidate key** of R(U)?         | `X⁺ = U` AND no proper subset of X has that |

### Worked example
`R(A, B, C, D, E)` with `F = { AB → C, B → D, CD → E }`.

Compute `(AB)⁺`:

| Step | Apply             | Result   |
|------|-------------------|----------|
| 0    | start             | {A, B}   |
| 1    | AB → C            | {A, B, C} |
| 2    | B → D             | {A, B, C, D} |
| 3    | CD → E            | {A, B, C, D, E} |

`(AB)⁺ = {A,B,C,D,E} = U`, so **AB is a super key**. Check minimality:
* `A⁺ = {A}` (only reflexivity applies), not full.
* `B⁺ = {B, D}`, not full.
Both proper subsets fail → **AB is a candidate key**.

---

## 4. Finding ALL Candidate Keys (typical exam question)

Strategy:

1. Compute the set of attributes that **never appear on the right-hand
   side** of any FD. Call this set **L** (must be in every key).
2. Compute the set of attributes that **never appear on the left-hand
   side**. They are determined by others (cannot be a key alone).
3. Try `L` first — if `L⁺ = U`, `L` is the unique candidate key.
4. Otherwise extend `L` with one of the remaining attributes at a time
   and recompute the closure.

### Worked example
`R(A, B, C, D)` with `F = { A → B, B → C, C → D }`.

* L = `{A}` (A never appears on the right).
* `A⁺ = {A, B, C, D} = U` → **A is the only candidate key**.

### Another example
`R(A, B, C, D, E)` with `F = { AB → C, CD → E, B → D, E → A }`.

* Attributes never on the RHS: `B`.
* `B⁺ = {B, D}`. Not full → extend.
* Try `{B, C}`: `(BC)⁺` = via CD→E? need D first: {B,C,D} (B→D), {B,C,D,E} (CD→E), {A,B,C,D,E} (E→A). **Key**.
* Try `{B, E}`: {B,E,A} (E→A), {B,E,A,D} (B→D), {B,E,A,D,C} (AB→C). **Key**.
* Try `{B, A}`: AB→C gives C, then CD via B→D gives D, then E. **Key**.
* So candidate keys are `{AB}, {BC}, {BE}`.

---

## 5. Equivalence and Cover

* Two sets of FDs `F` and `G` are **equivalent** if `F⁺ = G⁺`, i.e. they
  imply the same set of FDs.
* A **minimal (canonical) cover** `Fc` of F is a smallest set
  equivalent to F. Three reduction steps:
  1. Make every RHS a single attribute (decomposition).
  2. Remove extraneous attributes from LHSs.
  3. Remove redundant FDs.

The canonical cover is used by the 3NF synthesis algorithm
(chapter 12).

---

## 6. Worked Mini-Problem — End-to-End

`R(A, B, C, D, E, F)` with
`F = { A → BC, CD → EF, B → E, E → A }`.

**Step 1 — closures of singletons** (sanity check):

| Attribute | Closure                       |
|-----------|-------------------------------|
| `A⁺`      | {A, B, C, E} (A→BC, B→E)      |
| `B⁺`      | {B, E, A, C} (B→E, E→A, A→BC) |
| `C⁺`      | {C}                           |
| `D⁺`      | {D}                           |
| `E⁺`      | {E, A, B, C}                  |
| `F⁺`      | {F}                           |

**Step 2 — must-be-in-every-key set L = {D, F}?**
F never appears on RHS, D never appears on RHS → both must be in every
key. So start with `{D}` extended.

**Step 3 — candidate keys**:
* `{A, D}⁺` = via A→BC + CD→EF gives {A,B,C,D,E,F}. **Key**.
* `{B, D}⁺` = B→E, E→A, A→BC, then CD→EF: full. **Key**.
* `{E, D}⁺` = E→A→BC, then CD→EF: full. **Key**.

> F (the attribute) is never on the LHS, so it can't be derived from
> any other attribute → F must be in every key. Wait — check the FD
> list: `CD → EF`. So F is derivable from CD. Then F does NOT need to
> be in the key; revise: the only must-be-in-every-key attribute is
> `D`. (Always re-check by walking the algorithm; don't trust visual
> "never on RHS" without scanning every FD.)

**Lesson**: scan the *entire RHS multiset*, not just visual scanning.

---

## 7. Exam-Style Questions

**Q1.** Which of the following is **not** one of Armstrong's three
axioms?
A. Reflexivity  B. Augmentation  C. Decomposition  D. Transitivity
> Answer: C — decomposition is a *derived* rule.

**Q2.** Given F = {A→B, B→C, A→C}, the FD `A → C` is:
A. Trivial  B. Derivable from F by transitivity (redundant)  C. Independent
> Answer: B. After computing the canonical cover, A→C can be removed.

**Q3.** For `R(A,B,C,D)` with F = {AB→C, C→D, D→A}, find all candidate keys.
> `(AB)⁺` = {A,B,C,D} → key.
> `(BC)⁺` = {B,C,D,A} (C→D, D→A) → key.
> `(BD)⁺` = {B,D,A,C} (D→A, AB→C) → key.
> Candidate keys: `AB, BC, BD`.

**Q4.** If `X⁺ = U`, then X is:
> A super key. It is a candidate key **iff** no proper subset has the
> same property.

**Q5.** A partial functional dependency exists only when:
A. the LHS is a single attribute
B. the LHS is composite and a proper subset already determines the RHS
C. the FD is trivial
D. the FD is transitive
> Answer: B.

---

## 8. Further Reading

* W. W. Armstrong, "Dependency Structures of Data Base Relationships",
  *IFIP*, 1974.
* Silberschatz et al., *Database System Concepts*, ch. 8.
