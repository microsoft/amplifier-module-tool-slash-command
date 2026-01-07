---
description: Perform security audit on code
allowed-tools: [read_file, grep]
argument-hint: [file-or-directory]
---

Perform a comprehensive security audit of {{$1 or "the codebase"}}:

## OWASP Top 10 Checks
1. **Injection Flaws**: SQL, command, LDAP injection vulnerabilities
2. **Broken Authentication**: Weak password policies, session management
3. **Sensitive Data Exposure**: Unencrypted data, hardcoded secrets
4. **XML External Entities (XXE)**: XML parsing vulnerabilities
5. **Broken Access Control**: Authorization bypass opportunities
6. **Security Misconfiguration**: Default configs, verbose errors
7. **Cross-Site Scripting (XSS)**: Input sanitization issues
8. **Insecure Deserialization**: Untrusted data deserialization
9. **Using Components with Known Vulnerabilities**: Outdated dependencies
10. **Insufficient Logging & Monitoring**: Security event tracking

## Additional Security Concerns
- Hardcoded credentials or API keys
- Insecure cryptographic practices
- Race conditions or timing attacks
- Denial of service vulnerabilities
- Information disclosure

Provide specific findings with severity levels (Critical, High, Medium, Low) and remediation recommendations.
