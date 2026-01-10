---
description: Review current git diff with AI analysis
argument-hint: "[file]"
allowed-tools: [bash]
max-chars: 12000
---

Review the following code changes:

## Changes
!`git diff {{$1 or "HEAD"}} 2>/dev/null || echo "No changes to review"`

## Staged Changes
!`git diff --cached {{$1 or ""}} 2>/dev/null`

Please review these changes for:
1. **Correctness** - Any bugs or logic errors?
2. **Style** - Consistent with surrounding code?
3. **Security** - Any potential vulnerabilities?
4. **Performance** - Any obvious inefficiencies?

Provide specific, actionable feedback.
