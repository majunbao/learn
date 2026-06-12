# Common Web Attacks and Defenses

| Attack                      | Description                                                   | Defense                                                                |
|-----------------------------|---------------------------------------------------------------|------------------------------------------------------------------------|
| SQL Injection               | Untrusted input is concatenated into SQL                      | Use `PreparedStatement` / MyBatis `#{}` parameters — never `${}` with user input |
| XSS (Cross-Site Scripting)  | Untrusted input is rendered as HTML / JS in the browser       | Output-encode by context; CSP header; framework auto-escaping          |
| CSRF                        | Browser is tricked into using the victim's session cookie     | CSRF tokens; `SameSite=Lax/Strict` cookies                             |
| Broken authentication       | Weak/replayable session tokens                                | Strong hashing (BCrypt); short-lived JWT + refresh; rotate secrets     |
| Insecure deserialization    | Untrusted bytes are turned into objects                       | Avoid Java native serialization for untrusted data; use JSON + DTOs    |
| Sensitive data exposure     | TLS not used; secrets in source                               | HTTPS everywhere; HSTS; secrets in a vault, never in git               |
| Privilege escalation        | Missing per-request authorization checks                      | Check `@PreAuthorize` on every endpoint; deny by default               |
| Mass-assignment             | Framework binds attacker-controlled fields                    | Explicit DTOs; never bind directly to JPA entities                     |
| Replay attack               | Old request is re-sent                                        | Nonces, short token TTLs, signed timestamps                            |
| Open redirect / SSRF        | Server follows attacker-supplied URLs                         | Allow-list of destinations; deny private IP ranges                     |
