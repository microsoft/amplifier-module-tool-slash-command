---
description: Request comprehensive code review
allowed-tools: [read_file, grep, task]
argument-hint: [file-or-directory]
---

Please review {{$1 or "recent changes"}} with focus on:

## Code Quality
- Readability and maintainability
- Adherence to best practices
- Code organization and structure

## Correctness
- Potential bugs or edge cases
- Logic errors or incorrect assumptions
- Error handling completeness

## Security
- Input validation and sanitization
- Authentication and authorization
- Sensitive data handling
- Common vulnerabilities (SQL injection, XSS, etc.)

## Performance
- Algorithmic efficiency
- Resource usage (memory, CPU)
- Database query optimization
- Caching opportunities

## Testing
- Test coverage adequacy
- Edge cases covered
- Error scenario testing

Provide specific, actionable recommendations with code examples where helpful.
