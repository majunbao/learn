# 12 — Schema Decomposition

> Syllabus reference: P100–P103
>
> Normalisation works by **decomposing** an over-loaded relation into
> several smaller relations. A "good" decomposition must satisfy two
> non-trivial properties: it must be **lossless** and it should be
> **dependency-preserving**. This chapter shows the mechanics;
> chapter 13 gives the formal tests.

---

## 1. What "Decomposition" Means

A decomposition of `R(U, F)` is a set of relations
`{R1(U1, F1), R2(U2, F2), ..., Rn(Un, Fn)}` such that
`U = U1 ∪ U2 ∪ ... ∪ Un`.

The two desirable properties:

| Property                  | Question it answers                                    |
|---------------------------|--------------------------------------------------------|
| **Lossless join**         | Can we reconstruct R exactly by joining the pieces?    |
| **Dependency preservation** | Can every original FD be checked locally inside one piece? |

You should **always** preserve lossless join. Dependency preservation
is desirable but sometimes traded away for BCNF.

---

## 2. Two Standard Decomposition Algorithms

### 2.1 BCNF Decomposition (top-down)

Repeatedly find an FD `X → Y` in R where X is not a super key, and split:

```
R  →  R1 = X ∪ Y        (the "violating" FD)
      R2 = R − (Y − X)  (everything else)
```

Repeat on each piece until every relation is in BCNF.

* **Lossless**: yes (the common attribute X is a super key of R1).
* **Dependency-preserving**: not guaranteed.

### 2.2 3NF Synthesis (bottom-up)

Goal: produce a 3NF schema that is **both lossless and dependency-preserving**.

```
1. Compute a canonical (minimal) cover Fc of F.
2. For every FD X → A1, ..., An in Fc, output one relation
   Ri = X ∪ {A1, ..., An}.
3. If none of the Ri contains a candidate key of R, add an extra
   relation whose attributes form a candidate key. (Ensures lossless join.)
4. Remove any Ri whose schema is a subset of another Rj.
```

This algorithm guarantees:
* every Ri is in 3NF;
* the decomposition is dependency-preserving (each FD lives entirely in one Ri);
* it is lossless because of step 3.

---

## 3. Worked Example — BCNF Decomposition

`R(sid, sname, cid, cname, instructor)` with FDs:

* `sid → sname`
* `cid → cname`
* `(sid, cid) → instructor`

**Step 1.** Find a violating FD. `sid → sname`: `sid` is not a super key (it
doesn't determine `cid, cname, instructor`). Split:

* `R1(sid, sname)`
* `R2(sid, cid, cname, instructor)`

**Step 2.** In `R2`, `cid → cname` violates BCNF. Split:

* `R3(cid, cname)`
* `R4(sid, cid, instructor)`

Final decomposition: `R1(sid, sname)`, `R3(cid, cname)`,
`R4(sid, cid, instructor)`. All are in BCNF.

---

## 4. Worked Example — 3NF Synthesis

`R(A, B, C, D, E)` with `F = { A → B, B → C, A → D, AE → C }`.

**Step 1 — Canonical cover Fc**

* RHS to single attributes: `A → B, B → C, A → D, AE → C`.
* `AE → C` is redundant: `A → B` and `B → C` give `A → C`, so adding `E` is
  extraneous → reduce LHS to `A → C`, which is already implied → remove
  the FD entirely.
* Canonical cover: `Fc = { A → B, B → C, A → D }`.

**Step 2 — One relation per FD**

* `R1(A, B)`
* `R2(B, C)`
* `R3(A, D)`

**Step 3 — Add a key relation if needed**
Candidate key of R: `{A, E}` (you can check: `(AE)⁺ = U`). No `Ri` contains
this key, so add:

* `R4(A, E)`

**Final 3NF decomposition**: `R1, R2, R3, R4`. Lossless and dependency-preserving.

---

## 5. The Trade-Off

| Algorithm      | Reaches | Lossless? | Dependency-preserving? |
|----------------|---------|-----------|------------------------|
| BCNF top-down  | BCNF    | Always    | Sometimes              |
| 3NF synthesis  | 3NF     | Always    | Always                 |

Conclusion:

* If you can achieve BCNF **and** preserve dependencies — do it.
* If they conflict — prefer **3NF + dependency preservation** for OLTP
  systems where local constraint checking matters most.

---

## 6. Common Pitfalls

1. **Forgetting lossless check** — always verify the chase test
   (chapter 13) or rely on a proven algorithm.
2. **Forgetting the key relation in 3NF synthesis** — leads to a
   lossy decomposition.
3. **Splitting attributes that are not connected by any FD** —
   guarantees losslessness, but the result is meaningless data.
4. **Reading a partial FD as "OK because the attribute moved into
   another table"** — that introduces redundancy elsewhere.

---

## 7. Exam-Style Questions

**Q1.** Which decomposition is guaranteed to preserve all FDs?
A. BCNF decomposition  B. 3NF synthesis  C. ad-hoc  D. natural-join recomposition
> Answer: B.

**Q2.** A lossless decomposition guarantees:
> That `R = R1 ⋈ R2 ⋈ ... ⋈ Rn` for **every** legal instance — no spurious
> tuples appear and no information is lost.

**Q3.** `R(A,B,C)` with FDs `A → B, B → C`. Decompose `R` into
`R1(A,B)` and `R2(B,C)`. Is the decomposition lossless?
> Yes — the common attribute `B` is a key of `R2`, satisfying the
> two-relation lossless test (chapter 13).

**Q4.** Same R, decomposed into `R1(A,B)` and `R2(A,C)`. Lossless?
> Yes — common attribute `A` is a key of both pieces (A → B and A → C
> are implied), so lossless. But dependency `B → C` is **not** preserved
> (no relation contains both B and C).

**Q5.** What is the canonical cover of `F = { A → BC, B → C, AB → C }`?
> Decompose RHSs: `A → B, A → C, B → C, AB → C`. Remove `AB → C`
> (since `A → C`). Remove `A → C` (since `A → B, B → C` gives it).
> Canonical cover: `{ A → B, B → C }`.

---

## 8. Further Reading

* Maier, *The Theory of Relational Databases*, ch. 5–6.
* Ullman, *Principles of Database and Knowledge-Base Systems*, vol. 1.
