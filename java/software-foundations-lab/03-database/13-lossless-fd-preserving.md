# 13 — Lossless Join & Dependency Preservation

> Syllabus reference: P104–P107
>
> Chapter 12 introduced the *properties*; this chapter gives you the
> *tests* — the algorithms you actually apply on the exam.

---

## 1. Lossless-Join Property — Formal Statement

A decomposition `ρ = {R1, R2, ..., Rn}` of `R(U, F)` is **lossless**
iff for every legal instance `r` of R:

> `r = π_{U1}(r) ⋈ π_{U2}(r) ⋈ ... ⋈ π_{Un}(r)`

If the decomposition is lossy, the natural join produces **spurious
tuples** that were never in the original relation.

---

## 2. The Two-Relation Lossless Test (most-tested!)

A decomposition into exactly **two** relations `R1` and `R2` is
lossless iff

> `(R1 ∩ R2) → (R1 − R2)`     **or**     `(R1 ∩ R2) → (R2 − R1)`

i.e. the common attributes functionally determine **either side**.

### Worked example

`R(A, B, C)` with `F = {A → B}`.

**Decomposition 1**: `R1(A, B)`, `R2(A, C)`.
* `R1 ∩ R2 = {A}`. `A → B` (R1−R2). **Lossless.**

**Decomposition 2**: `R1(A, B)`, `R2(B, C)`.
* `R1 ∩ R2 = {B}`. We need `B → A` or `B → C`. Neither holds. **Lossy.**

---

## 3. The Chase Test (for ≥ 3 relations)

Used when the decomposition has three or more pieces.

### Procedure

1. Build a matrix with one row per `Ri` and one column per attribute in `U`.
2. For each cell `(i, A)`: write `aA` if `A ∈ Ui`, otherwise `bi,A`.
3. Apply every FD `X → Y` in F: if two rows agree on all X-columns,
   make them agree on all Y-columns (prefer `a` symbols over `b` symbols).
4. Repeat until no changes.
5. If any row becomes **all `a`** → decomposition is **lossless**.

### Worked example

`R(A, B, C, D, E)` with `F = { A → C, B → C, C → D, DE → C, CE → A }`.
Decomposition: `R1(A, D), R2(A, B), R3(B, E), R4(C, D, E), R5(A, E)`.

Build the chase matrix, then apply FDs. (The full table-by-table chase
is long; the standard textbook conclusion is that this decomposition is
**lossless** once you propagate the FDs.)

Tip for the exam: most chase questions only ask whether at least one row
becomes all-`a`. Make the propagation table neat and walk row by row.

---

## 4. Dependency-Preservation Test

A decomposition preserves an FD `X → Y` if **all attributes of `XY`
appear together in some `Ri`**, so that the FD can be enforced inside
that single relation.

Formally:
> Decomposition ρ preserves F iff
> `(F1 ∪ F2 ∪ ... ∪ Fn)⁺ = F⁺`
> where `Fi` is the projection of F on `Ui`.

### Procedure

1. For each FD `X → Y` in F:
   * Compute `X⁺` using only the **projected** FDs `F1 ∪ ... ∪ Fn`.
   * If `Y ⊆ X⁺`, the FD is preserved.
2. If every FD passes, the decomposition is dependency-preserving.

### Quick visual check (sufficient but not necessary)
* If every FD's LHS and RHS together fit inside **one** Ri, you are done.
* If some FD spans two relations, you must compute closures explicitly.

---

## 5. Worked End-to-End Example

`R(A, B, C, D)` with `F = { A → B, B → C, C → D, D → A }`.
Candidate keys: every single attribute! (the closure chain wraps around).

**Decomposition** `ρ = { R1(A,B), R2(B,C), R3(C,D) }`.

### Lossless?
Use the chase (or pair-wise):
* `R1 ⋈ R2`: common attr `B`. Need `B → A` (or `B → C`). `B → C` holds. **Lossless** here.
* Combined relation `R1 ⋈ R2` has attrs `{A,B,C}`. Now join with `R3(C,D)`. Common = `C`. Need `C → A,B` or `C → D`. `C → D` holds. **Lossless** overall.

### Dependency-preserving?

* `A → B` lives in R1 ✔
* `B → C` lives in R2 ✔
* `C → D` lives in R3 ✔
* `D → A` — does any Ri contain both D and A? No.

  Compute `D⁺` using only projected FDs `{A→B, B→C, C→D}`:
  starting from `{D}`, no rule applies → `D⁺ = {D}`. We need `A ∈ D⁺`. Fails.

→ **Not dependency-preserving**.

### Diagnosis
Even though every individual relation is in BCNF, the cyclic FD set
cannot be checked locally. To preserve `D → A` we would also need to
include `A` in a relation with `D`, e.g. add `R4(D, A)` — which restores
the cycle but increases redundancy.

This is the classic illustration of the trade-off discussed in
chapter 12.

---

## 6. Exam-Style Questions

**Q1.** `R(A,B,C)` with `F = {A → C}`. Decomposition `{R1(A,B), R2(A,C)}`.
Lossless? Dependency-preserving?
> Common attr `A`. `A → C` covers `R2 − R1 = {C}`. **Lossless.**
> `A → C` fits inside R2. **Dependency-preserving.**

**Q2.** `R(A,B,C)` with `F = {A → B, C → B}`. Decompose into
`R1(A,B), R2(B,C)`. Lossless?
> Common attr `B`. Need `B → A` or `B → C`. Neither holds. **Lossy.**

**Q3.** A decomposition into BCNF is always:
A. lossless and dependency-preserving
B. lossless but not always dependency-preserving
C. dependency-preserving but not always lossless
D. neither
> Answer: B.

**Q4.** A decomposition via 3NF synthesis is:
A. always lossless and dependency-preserving
B. lossless but not always dependency-preserving
C. dependency-preserving but not always lossless
D. neither
> Answer: A.

**Q5.** State the necessary and sufficient condition for a two-relation
decomposition to be lossless.
> The intersection of the two schemas must be a **super key** of at
> least one of them.

---

## 7. Further Reading

* Maier, *The Theory of Relational Databases*, ch. 7 (the chase).
* Garcia-Molina et al., *Database Systems: The Complete Book*, ch. 3.
