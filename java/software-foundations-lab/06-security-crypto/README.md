# Module 06 — Security & Cryptography

> Goal: stop hand-waving about "security" and actually understand what a
> hash, a symmetric cipher, an asymmetric key-pair, a signature, a TLS
> handshake and a JWT are — by implementing tiny demos of each.

## Sub-packages

| Folder               | Concept                                     | Java API                              |
|----------------------|---------------------------------------------|---------------------------------------|
| `hashing/`           | One-way hashing for passwords               | `MessageDigest` (SHA-256), BCrypt     |
| `symmetric/`         | Same key encrypts & decrypts                | `Cipher` with `AES/GCM/NoPadding`     |
| `asymmetric/`        | Public key encrypts, private key decrypts   | `KeyPairGenerator`, `Cipher` (RSA)    |
| `digital-signature/` | Private key signs, public key verifies      | `Signature` (SHA256withRSA)           |
| `tls-https/`         | Real HTTPS with a self-signed cert          | `keytool`, Spring Boot SSL config     |
| `jwt-auth/`          | Stateless tokens                            | `io.jsonwebtoken:jjwt`                |
| `common-attacks.md`  | SQL injection, XSS, CSRF, replay — and fix  | (notes only)                          |

## Big-picture analogy

| Idea                    | Real-world analogy                                         |
|-------------------------|------------------------------------------------------------|
| Hash                    | A fingerprint — easy to compute, hard to reverse           |
| Symmetric encryption    | One shared key to lock & unlock a safe                     |
| Asymmetric encryption   | Public mailbox slot anyone can drop in; only you can open  |
| Digital signature       | A wax seal — anyone can verify it; only you can stamp it   |
| TLS handshake           | Asymmetric crypto to agree on a symmetric session key      |
| JWT                     | A signed claim ticket the server can verify without state  |

## Why "public key encrypts / private key decrypts" AND "private key signs / public key verifies"?

Same key pair, opposite directions, different goals:

* **Encryption goal**: confidentiality → use the *recipient's public* key so
  only the recipient (who holds the matching private key) can read it.
* **Signing goal**: authenticity → use *your own private* key so anyone with
  your public key can prove the message came from you.

## Exercises

1. Hash the same password twice with `MessageDigest` — identical output.
   Hash it twice with BCrypt — different output. Explain why (salt).
2. Encrypt a file with AES, then try to decrypt with the wrong key. Observe
   the `AEADBadTagException` from GCM.
3. Generate an RSA key-pair, sign a message, then change a single byte and
   verify — the verification must fail.
4. Generate a self-signed cert with `keytool` and run a Spring Boot app on
   `https://localhost:8443`.
5. Issue a JWT, decode it on https://jwt.io and inspect the header/payload.
   Notice: encoded ≠ encrypted.
