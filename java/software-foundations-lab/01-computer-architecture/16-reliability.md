# 16 — System Reliability

> Syllabus reference: P180–P186
>
> **Reliability** measures how likely a system performs correctly over
> time. The exam tests reliability metrics, series/parallel system
> calculations, and the RAS characteristics of computer systems.

---

## 1. Key Metrics

### 1.1 Reliability R(t)

The probability that a system operates correctly for time t.

```
R(t) = P(system works at time t)
R(0) = 1 (system starts working)
R(∞) = 0 (everything eventually fails)
```

### 1.2 Failure rate λ (故障率)

For a constant failure rate (exponential distribution):

```
R(t) = e^(−λt)
```

| Symbol | Name | Unit |
|--------|------|------|
| λ | Failure rate | failures/hour |
| MTTF | Mean Time To Failure | hours |
| MTBF | Mean Time Between Failures | hours |
| MTTR | Mean Time To Repair | hours |

### 1.3 Relationships

```
MTTF = 1 / λ           (for non-repairable systems)
MTBF = MTTF + MTTR     (for repairable systems)
Availability = MTTF / (MTTF + MTTR) = MTTF / MTBF
```

> Exam tip: **MTTF** = time until first failure (non-repairable).
> **MTBF** = time between failures (repairable). They are different!

---

## 2. Series Systems (串联系统)

All components must work for the system to work.

```
┌──────┐   ┌──────┐   ┌──────┐
│ R₁   │───│ R₂   │───│ R₃   │
└──────┘   └──────┘   └──────┘
```

### Formulas

```
R_system = R₁ × R₂ × R₃ × ... × Rₙ

λ_system = λ₁ + λ₂ + λ₃ + ... + λₙ

MTTF_system = 1 / λ_system
```

> Series reliability is **always less** than the weakest component.

---

## 3. Parallel Systems (并联系统 / 冗余系统)

The system works as long as **at least one** component works.

```
┌──────┐
│ R₁   │─┐
└──────┘ │
┌──────┐ ├──► Output
│ R₂   │─┤
└──────┘ │
┌──────┐ │
│ R₃   │─┘
└──────┘
```

### Formulas

```
R_system = 1 − (1 − R₁)(1 − R₂)(1 − R₃)...(1 − Rₙ)

For identical components (all R):
R_system = 1 − (1 − R)ⁿ
```

> Parallel reliability is **always greater** than the strongest
> component.

---

## 4. Mixed Series-Parallel Systems

### 4.1 Approach: decompose into sub-systems

1. Identify series and parallel groups.
2. Compute reliability of each group.
3. Combine the groups.

### 4.2 Worked example

```
    ┌──[R₂]──┐
──[R₁]──┤       ├──[R₄]──
    └──[R₃]──┘
```

R₁ and R₄ are in series with the parallel group (R₂ ∥ R₃).

```
R_parallel = 1 − (1 − R₂)(1 − R₃)
R_system = R₁ × R_parallel × R₄
```

If R₁ = R₂ = R₃ = R₄ = 0.9:

```
R_parallel = 1 − (1 − 0.9)² = 1 − 0.01 = 0.99
R_system = 0.9 × 0.99 × 0.9 = 0.8019
```

---

## 5. N-Modular Redundancy (N模冗余)

N identical modules vote on the output; the majority wins.

### 5.1 Triple Modular Redundancy (TMR)

3 modules + 1 voter. System works if at least 2 out of 3 modules work.

```
R_TMR = R₁R₂R₃ + R₁R₂(1−R₃) + R₁(1−R₂)R₃ + (1−R₁)R₂R₃
      = 3R² − 2R³    (for identical modules)
```

For R = 0.9:

```
R_TMR = 3(0.81) − 2(0.729) = 2.43 − 1.458 = 0.972
```

> TMR improves reliability when R > 0.5. If R < 0.5, TMR actually
> makes things worse!

### 5.2 General NMR

For N modules (N odd), system works if at least (N+1)/2 modules work.

```
R_NMR = Σ C(N,k) × R^k × (1−R)^(N−k)  for k = ⌈N/2⌉ to N
```

---

## 6. RAS — Reliability, Availability, Serviceability

| Property | Chinese | Meaning |
|----------|---------|---------|
| **Reliability** | 可靠性 | System operates correctly for as long as possible |
| **Availability** | 可用性 | System is ready for use when needed |
| **Serviceability** | 可维护性 | System can be easily repaired / maintained |

### Availability formula

```
Availability = MTTF / (MTTF + MTTR)

Typical targets:
  2 nines:  99%     → 3.65 days downtime/year
  3 nines:  99.9%   → 8.76 hours downtime/year
  5 nines:  99.999% → 5.26 minutes downtime/year
```

---

## 7. Worked Examples

**Example 1:** A system has 3 components in series with failure rates
λ₁ = 0.001, λ₂ = 0.002, λ₃ = 0.003 (per hour). Find MTTF.

```
λ_system = 0.001 + 0.002 + 0.003 = 0.006/hour
MTTF = 1/0.006 = 166.67 hours
```

**Example 2:** Two identical components in parallel, each with R = 0.8.
Find system reliability.

```
R_system = 1 − (1 − 0.8)² = 1 − 0.04 = 0.96
```

**Example 3:** A system has MTTF = 1000 hours and MTTR = 10 hours.
Find availability.

```
Availability = 1000 / (1000 + 10) = 1000/1010 ≈ 0.9901 = 99.01%
```

**Example 4:** A complex system:

```
    ┌──[0.9]──┐
──[0.8]──┤       ├──
    └──[0.9]──┘
```

```
R_parallel = 1 − (1−0.9)² = 0.99
R_system = 0.8 × 0.99 = 0.792
```

---

## 8. Exam-Style Questions

**Q1.** In a series system of 4 components each with R = 0.95, the
system reliability is:
A. 0.95  B. 0.8145  C. 0.9975  D. 0.85
> Answer: B (0.95⁴ = 0.8145).

**Q2.** Two components in parallel, each with R = 0.9. System
reliability is:
A. 0.9  B. 0.99  C. 0.81  D. 1.0
> Answer: B (1 − 0.1² = 0.99).

**Q3.** MTBF = MTTF + MTTR. If MTTF = 2000h and MTTR = 50h, the
availability is:
A. 95%  B. 97.5%  C. 99%  D. 99.5%
> Answer: B (2000/2050 ≈ 0.9756).

**Q4.** In TMR with R = 0.7, the system reliability is:
> R_TMR = 3(0.49) − 2(0.343) = 1.47 − 0.686 = 0.784.

**Q5.** Adding more components in series ___ system reliability.
A. increases  B. decreases  C. does not change  D. depends on component R
> Answer: B (series reliability = product; adding a factor < 1
> decreases the product).

**Q6.** A system with 99.99% availability has how much downtime per
year?
A. 5.26 min  B. 52.6 min  C. 8.76 hours  D. 3.65 days
> Answer: B (0.01% × 365 × 24 × 60 ≈ 52.56 minutes).

---

## 9. Further Reading

* Stallings, *Computer Organization and Architecture*, ch. 2.
* Avizienis et al., "Basic Concepts and Taxonomy of Dependable and
  Secure Computing", *IEEE TDSC*, 2004.

---

## 10. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Reliability | 可靠性 | 16 |
| Availability | 可用性 | 16 |
| Serviceability | 可维护性 | 16 |
| MTTF | 平均无故障时间 | 16 |
| MTBF | 平均故障间隔时间 | 16 |
| MTTR | 平均修复时间 | 16 |
| Failure rate | 故障率 | 16 |
| Series system | 串联系统 | 16 |
| Parallel system | 并联系统 | 16 |
| Redundancy | 冗余 | 16 |
| TMR | 三模冗余 | 16 |
| NMR | N模冗余 | 16 |
| RAS | 可靠性、可用性、可维护性 | 16 |
