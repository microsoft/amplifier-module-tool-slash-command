---
description: Summarize git status and recent commits with recommendations
argument-hint: "[path:.]"
---

Analyze the git status of {{$1 or "the current directory"}} and provide a summary.

Steps:
1. Run `git status` to see current state
2. Run `git log --oneline -10` to see recent commits
3. Run `git diff --stat` to see uncommitted changes summary

Provide:
- Current branch and its relationship to remote
- Summary of uncommitted changes (if any)
- Recent commit history highlights
- Recommendations:
  - Should anything be committed?
  - Are there files that should be in .gitignore?
  - Is a push needed?

Keep it brief and actionable.
