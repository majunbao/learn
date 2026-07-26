# 15 — Encryption Algorithms

> Syllabus reference: P169–P179
>
> Cryptography transforms readable data (plaintext) into unreadable
> form (ciphertext) to protect confidentiality and integrity. The exam
> covers symmetric encryption, asymmetric encryption, hash functions,
> digital signatures, and PKI.

---

## 1. Cryptography Basics

```
Plaintext ──[Encryption algorithm + Key]──► Ciphertext
Ciphertext ──[Decryption algorithm + Key]──► Plaintext
```

| Term | Chinese | Meaning |
|------|---------|---------|
| Plaintext | 明文 | Original readable data |
| Ciphertext | 密文 | Encrypted unreadable data |
| Key | 密钥 | Secret value used in encryption/decryption |
| Cryptanalysis | 密码分析 | Breaking encryption without the key |

---

## 2. Symmetric Encryption (对称加密 / 共享密钥加密)

Same key for encryption and decryption.

```
Sender:  Plaintext + Key → Ciphertext
Receiver: Ciphertext + Key → Plaintext
```

### 2.1 Properties

| Property | Value |
|----------|-------|
| Key count | 1 (shared) |
| Speed | Fast |
| Key distribution problem | Yes — how to share the key securely? |
| Scalability | n users → n(n−1)/2 keys |

### 2.2 Classical ciphers

| Cipher | Type | Description |
|--------|------|-------------|
| **Caesar cipher** | Substitution | Shift each letter by k positions |
| **Vigenère cipher** | Poly-alphabetic substitution | Use a keyword to vary the shift |
| **DES** | Block cipher | 56-bit key, 64-bit blocks; **insecure** today |
| **3DES** | Block cipher | Triple DES; 112 or 168-bit effective key |
| **AES** | Block cipher | 128/192/256-bit key; **current standard** |
| **RC4** | Stream cipher | Variable key length; **deprecated** |

### 2.3 Block cipher modes

| Mode | Chinese | Description |
|------|---------|-------------|
| **ECB** (Electronic Codebook) | 电子密码本模式 | Each block encrypted independently; same plaintext → same ciphertext (insecure for patterns) |
| **CBC** (Cipher Block Chaining) | 密码分组链接模式 | Each block XORed with previous ciphertext before encryption; needs IV |
| **CTR** (Counter) | 计数器模式 | Encrypt a counter; XOR with plaintext; parallelisable |
| **OFB** (Output Feedback) | 输出反馈模式 | Keystream generated independently; no error propagation |
| **CFB** (Cipher Feedback) | 密码反馈模式 | Similar to OFB but uses ciphertext as feedback |

> Exam tip: **ECB is the weakest mode** — identical plaintext blocks
> produce identical ciphertext blocks, leaking patterns. CBC is the
> minimum acceptable mode.

---

## 3. Asymmetric Encryption (非对称加密 / 公钥加密)

Two keys: a **public key** (shared openly) and a **private key** (kept
secret).

```
Encryption:  Plaintext + Public key → Ciphertext
Decryption:  Ciphertext + Private key → Plaintext

OR (for signatures):
Signing:     Message + Private key → Signature
Verification: Signature + Public key → Valid/Invalid
```

### 3.1 Properties

| Property | Value |
|----------|-------|
| Key count | 2 (public + private) per user |
| Speed | Slow (100–1000× slower than symmetric) |
| Key distribution | Easy (public key is public) |
| Scalability | n users → 2n keys |

### 3.2 Algorithms

| Algorithm | Key size | Security basis | Use |
|-----------|----------|---------------|-----|
| **RSA** | 1024–4096 bit | Integer factorisation | Encryption, signatures |
| **ECC** | 256–521 bit | Elliptic curve discrete log | Mobile, IoT (smaller keys) |
| **Diffie-Hellman** | — | Discrete log | Key exchange (not encryption) |
| **ElGamal** | — | Discrete log | Encryption, signatures |

### 3.3 RSA — how it works (simplified)

```
1. Choose two large primes p and q
2. n = p × q
3. φ(n) = (p−1)(q−1)
4. Choose e such that 1 < e < φ(n) and gcd(e, φ(n)) = 1
5. Compute d such that e × d ≡ 1 (mod φ(n))
6. Public key = (e, n); Private key = (d, n)

Encrypt: C = M^e mod n
Decrypt: M = C^d mod n
```

### 3.4 Diffie-Hellman key exchange

Allows two parties to establish a **shared secret** over an insecure
channel without ever transmitting the secret.

```
Public: prime p, generator g
Alice: chooses secret a, sends A = g^a mod p
Bob:   chooses secret b, sends B = g^b mod p

Shared secret:
Alice computes: B^a = g^(ab) mod p
Bob computes:   A^b = g^(ab) mod p
```

> Vulnerable to **man-in-the-middle** attack without authentication.

---

## 4. Hash Functions (哈希函数 / 散列函数)

A hash function maps arbitrary-length input to a **fixed-length** digest.

| Property | Meaning |
|----------|---------|
| **One-way** | Computationally infeasible to find input from hash |
| **Collision-resistant** | Hard to find two inputs with the same hash |
| **Avalanche effect** | Small change in input → large change in hash |

### Common hash algorithms

| Algorithm | Digest size | Status |
|-----------|-----------|--------|
| MD5 | 128 bit | **Broken** — do not use |
| SHA-1 | 160 bit | **Broken** — deprecated |
| SHA-256 | 256 bit | Current standard |
| SHA-3 | Variable | Newest standard |

---

## 5. Digital Signatures (数字签名)

A digital signature provides **authentication**, **integrity**, and
**non-repudiation**.

### 5.1 Signing process

```
1. Hash the message: H = Hash(M)
2. Sign the hash with sender's private key: Sig = Encrypt_PRV(H)
3. Send (M, Sig) to receiver
```

### 5.2 Verification process

```
1. Hash the received message: H' = Hash(M)
2. Decrypt the signature with sender's public key: H'' = Decrypt_PUB(Sig)
3. If H' = H'' → signature is valid
```

### 5.3 Properties

| Property | How achieved |
|----------|-------------|
| **Authentication** | Only the private key holder can sign |
| **Integrity** | Any change to M changes the hash |
| **Non-repudiation** | Signer cannot deny signing (private key is theirs) |

> Exam tip: digital signature = hash + asymmetric encryption of the
> hash with the **private** key. Verification uses the **public** key.

---

## 6. Digital Certificates & PKI (公钥基础设施)

### 6.1 The trust problem

How do you know a public key really belongs to Alice and not an
impostor?

### 6.2 Digital certificate

A certificate binds a **public key** to an **identity**, signed by a
trusted **Certificate Authority (CA)**.

```
Certificate = {
  Subject: "Alice"
  Public key: (e, n)
  Issuer: "CA"
  Valid period: 2025-01-01 to 2026-12-31
  CA's signature: ...
}
```

### 6.3 PKI components

| Component | Role |
|-----------|------|
| **CA** (Certificate Authority) | Issues and signs certificates |
| **RA** (Registration Authority) | Verifies identity before CA issues certificate |
| **Certificate repository** | Stores published certificates |
| **CRL** (Certificate Revocation List) | Lists revoked certificates |
| **OCSP** (Online Certificate Status Protocol) | Real-time certificate status check |

### 6.4 Certificate chain

```
Root CA → Intermediate CA → End-entity certificate
```

The root CA is self-signed and pre-trusted by browsers/OSes.

---

## 7. Hybrid Encryption (混合加密)

In practice, we combine symmetric and asymmetric encryption:

```
1. Generate a random symmetric session key K
2. Encrypt the message with K (fast): C = SymEnc(M, K)
3. Encrypt K with receiver's public key: Ck = AsymEnc(K, PUB_R)
4. Send (C, Ck) to receiver

Receiver:
1. Decrypt K with private key: K = AsymDec(Ck, PRV_R)
2. Decrypt message: M = SymDec(C, K)
```

This gives the **speed of symmetric** encryption with the **key
distribution convenience** of asymmetric encryption. This is how
HTTPS/TLS works.

---

## 8. Exam-Style Questions

**Q1.** AES is a ___ encryption algorithm.
A. asymmetric  B. symmetric block  C. hash  D. stream
> Answer: B.

**Q2.** n users using symmetric encryption need how many keys?
A. n  B. 2n  C. n(n−1)/2  D. n²
> Answer: C.

**Q3.** A digital signature provides all EXCEPT:
A. authentication  B. confidentiality  C. integrity  D. non-repudiation
> Answer: B (signatures do not encrypt the message; they only sign it).

**Q4.** Diffie-Hellman is vulnerable to ___ without authentication.
A. brute force  B. man-in-the-middle  C. replay  D. SQL injection
> Answer: B.

**Q5.** ECB mode is insecure because:
A. it is too slow  B. identical blocks produce identical ciphertext  C. it needs an IV  D. it uses a public key
> Answer: B.

**Q6.** In PKI, a Certificate Authority (CA):
A. encrypts messages  B. issues and signs certificates  C. generates session keys  D. stores private keys
> Answer: B.

---

## 9. Further Reading

* Stallings, *Cryptography and Network Security*, ch. 2–10.
* Schneier, *Applied Cryptography*.

---

## 10. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Symmetric encryption | 对称加密 | 15 |
| Asymmetric encryption | 非对称加密 | 15 |
| Public key | 公钥 | 15 |
| Private key | 私钥 | 15 |
| Block cipher | 分组密码 | 15 |
| Stream cipher | 流密码 | 15 |
| DES | 数据加密标准 | 15 |
| AES | 高级加密标准 | 15 |
| RSA | RSA算法 | 15 |
| Hash function | 哈希函数 / 散列函数 | 15 |
| Digital signature | 数字签名 | 15 |
| Digital certificate | 数字证书 | 15 |
| PKI | 公钥基础设施 | 15 |
| CA | 证书授权中心 | 15 |
| CRL | 证书撤销列表 | 15 |
| ECB | 电子密码本模式 | 15 |
| CBC | 密码分组链接模式 | 15 |
| Diffie-Hellman | Diffie-Hellman密钥交换 | 15 |
| Non-repudiation | 不可否认性 | 15 |
