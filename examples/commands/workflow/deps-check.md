---
description: Check for outdated dependencies and security issues
argument-hint: "[path:.]"
---

Analyze dependencies in {{$1 or "the current directory"}} for updates and issues.

Steps:
1. Check what package manager is used (look for pyproject.toml, package.json, Cargo.toml, etc.)
2. For Python projects:
   - Run `uv pip list --outdated 2>/dev/null || pip list --outdated 2>/dev/null` 
   - Check for any known security advisories
3. For Node projects:
   - Run `npm outdated 2>/dev/null`
   - Run `npm audit 2>/dev/null | head -30`

Summarize:
- **Critical updates** - Security patches that should be applied ASAP
- **Major updates** - Breaking changes to review
- **Minor/Patch** - Safe to update, low risk
- **Pinned for reason** - Note any that seem intentionally held back

Be concise and focus on actionable items.
