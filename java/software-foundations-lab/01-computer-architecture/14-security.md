# 14 — Computer Security

> Syllabus reference: P152–P168
>
> Security is about protecting information and systems from
> unauthorised access, modification, and destruction. The exam covers
> security classification, common threats, access control models, and
> firewall basics.

---

## 1. Security Fundamentals — The CIA Triad

| Property | Chinese | Meaning |
|----------|---------|---------|
| **Confidentiality** | 机密性 | Data is disclosed only to authorised parties |
| **Integrity** | 完整性 | Data is not altered in unauthorised ways |
| **Availability** | 可用性 | Data and services are accessible when needed |

> Every security mechanism protects one or more of these three
> properties. Exam questions often ask "which CIA property is violated?"

---

## 2. Security Classification Levels

### 2.1 Chinese standard (GB 17859-1999)

| Level | Chinese | Name | Description |
|-------|---------|------|-------------|
| 1 | 第一级 | 用户自主保护级 | Basic access control; user-managed |
| 2 | 第二级 | 系统审计保护级 | + Audit logging; discretionary access control |
| 3 | 第三级 | 安全标记保护级 | + Security labels; mandatory access control |
| 4 | 第四级 | 结构化保护级 | + Structured protection; covert channel analysis |
| 5 | 第五级 | 访问验证保护级 | + Formal verification; highest trust |

### 2.2 TCSEC (Orange Book) — US DoD standard

| Level | Name | Key requirement |
|-------|------|-----------------|
| **D** | Minimal protection | No requirements |
| **C1** | Discretionary security | DAC, identification/authentication |
| **C2** | Controlled access | + Fine-grained DAC, audit |
| **B1** | Labeled security | + Mandatory labels (MAC) |
| **B2** | Structured protection | + Covert channel analysis, TCB |
| **B3** | Security domains | + Reference monitor, trusted recovery |
| **A1** | Verified design | + Formal verification |

> Exam tip: **C1/C2 = DAC**, **B1+ = MAC**. The jump from C2 to B1 is
> the shift from discretionary to mandatory access control.

---

## 3. Common Security Threats

### 3.1 Attack types

| Threat | Chinese | Description | CIA violated |
|--------|---------|-------------|-------------|
| **Eavesdropping / Sniffing** | 窃听 | Intercepting communication | Confidentiality |
| **Tampering** | 篡改 | Modifying data in transit | Integrity |
| **Denial of Service (DoS)** | 拒绝服务 | Overwhelming a system | Availability |
| **Spoofing** | 伪造 | Pretending to be someone else | Confidentiality, Integrity |
| **Replay attack** | 重放攻击 | Re-sending captured valid messages | Integrity |
| **Man-in-the-middle** | 中间人攻击 | Intercepting and possibly altering communication | All three |
| **SQL injection** | SQL注入 | Injecting SQL through user input | Integrity, Confidentiality |
| **Phishing** | 钓鱼 | Tricking users into revealing credentials | Confidentiality |
| **Trojan horse** | 特洛伊木马 | Malware disguised as legitimate software | All three |
| **Virus** | 病毒 | Self-replicating malware attached to a host file | All three |
| **Worm** | 蠕虫 | Self-replicating malware that spreads autonomously | Availability |

### 3.2 Malware comparison

| Type | Self-replicating? | Needs host? | Spreads autonomously? |
|------|-------------------|-------------|----------------------|
| Virus | Yes | Yes | No (user action needed) |
| Worm | Yes | No | Yes |
| Trojan | No | — | No (social engineering) |
| Logic bomb | No | — | No (triggered by condition) |

---

## 4. Access Control Models

### 4.1 DAC — Discretionary Access Control (自主访问控制)

- The **owner** of a resource decides who can access it.
- Implemented via ACLs (Access Control Lists) or capability lists.
- Flexible but vulnerable to Trojan horse attacks (a malicious program
  can inherit the owner's permissions).

### 4.2 MAC — Mandatory Access Control (强制访问控制)

- The **system** enforces access based on security labels and
  clearances.
- Subjects have **clearance levels**; objects have **classification
  levels**.
- Two rules:
  - **No read up** (Simple Security Property): a subject cannot read an
    object at a higher classification.
  - **No write down** (*-Property): a subject cannot write to an object
    at a lower classification.

```
Subject clearance:  SECRET
Object classification:  TOP SECRET → cannot read (no read up)
Object classification:  CONFIDENTIAL → cannot write (no write down)
Object classification:  SECRET → can read and write
```

### 4.3 RBAC — Role-Based Access Control (基于角色的访问控制)

- Permissions are assigned to **roles**, not individual users.
- Users are assigned to roles.
- Simplifies administration in large organisations.

```
User → Role → Permission
Alice → Manager → {read salary, approve leave, write reports}
Bob → Engineer → {read specs, write code}
```

---

## 5. Firewall (防火墙)

### 5.1 Types

| Type | Chinese | How | Pros | Cons |
|------|---------|-----|------|------|
| **Packet filtering** | 包过滤 | Inspects packet headers (IP, port, protocol) | Fast; simple | Cannot inspect payload; vulnerable to spoofing |
| **Stateful inspection** | 状态检测 | Tracks connection state; allows return traffic | More secure than simple filtering | More memory; slower |
| **Application proxy** | 应用代理 | Full proxy at application layer; inspects payload | Deep inspection; hides internal network | Slow; needs proxy per protocol |
| **Circuit-level gateway** | 电路级网关 | Validates TCP handshake; no payload inspection | Faster than app proxy | No content inspection |

### 5.2 Firewall architectures

| Architecture | Description |
|-------------|-------------|
| **Dual-homed host** | Firewall with two NICs (one external, one internal); no IP forwarding |
| **Screened host** | Packet-filtering router + bastion host on internal network |
| **Screened subnet (DMZ)** | Two firewalls with a DMZ between them; public servers in DMZ |

```
Internet ──[Router/FW]── DMZ (public servers) ──[FW]── Internal network
```

---

## 6. Intrusion Detection

| Type | Chinese | How | Example |
|------|---------|-----|---------|
| **Signature-based** | 特征检测 | Match known attack patterns | Snort rules |
| **Anomaly-based** | 异常检测 | Detect deviations from normal behaviour | Statistical models |

---

## 7. Exam-Style Questions

**Q1.** A DoS attack primarily violates which CIA property?
A. Confidentiality  B. Integrity  C. Availability  D. All
> Answer: C.

**Q2.** In MAC, "no read up" is called:
A. the *-Property  B. the Simple Security Property  C. DAC  D. RBAC
> Answer: B.

**Q3.** Which access control model is most vulnerable to Trojan horse
attacks?
A. DAC  B. MAC  C. RBAC  D. All equally
> Answer: A (DAC — a Trojan inherits the owner's permissions).

**Q4.** A worm differs from a virus in that a worm:
A. needs a host file  B. spreads autonomously  C. does not replicate  D. is less dangerous
> Answer: B.

**Q5.** TCSEC level B1 introduces:
A. DAC  B. audit logging  C. mandatory labels (MAC)  D. formal verification
> Answer: C.

**Q6.** A DMZ is used to:
A. encrypt traffic  B. isolate public-facing servers from the internal network  C. prevent all external access  D. detect intrusions
> Answer: B.

---

## 8. Further Reading

* Stallings, *Computer Security: Principles and Practice*, ch. 1–4.
* Bishop, *Computer Security: Art and Science*, ch. 1–5.

---

## 9. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Confidentiality | 机密性 | 14 |
| Integrity | 完整性 | 14 |
| Availability | 可用性 | 14 |
| DAC | 自主访问控制 | 14 |
| MAC | 强制访问控制 | 14 |
| RBAC | 基于角色的访问控制 | 14 |
| Firewall | 防火墙 | 14 |
| DMZ | 隔离区 / 非军事区 | 14 |
| Packet filtering | 包过滤 | 14 |
| Application proxy | 应用代理 | 14 |
| Virus | 病毒 | 14 |
| Worm | 蠕虫 | 14 |
| Trojan horse | 特洛伊木马 | 14 |
| DoS | 拒绝服务攻击 | 14 |
| Replay attack | 重放攻击 | 14 |
| Man-in-the-middle | 中间人攻击 | 14 |
| Intrusion detection | 入侵检测 | 14 |
