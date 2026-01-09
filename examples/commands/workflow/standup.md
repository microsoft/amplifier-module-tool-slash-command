---
description: Generate a standup summary from recent git activity
argument-hint: "[days:1]"
---

Generate a standup-ready summary of what I've been working on.

Steps:
1. Run `git log --oneline --since="{{$1 or "1"}} days ago" --author="$(git config user.name)"` to see my recent commits
2. Run `git diff --stat HEAD~5` to see recent changes (if available)
3. Check `git status` for work in progress

Format the output as:
**Yesterday/Recently:**
- [Bullet points of completed work based on commits]

**Today/Next:**
- [Suggestions based on uncommitted work or recent patterns]

**Blockers:**
- [Any if obvious from context, otherwise "None identified"]

Keep it concise - this should be speakable in under 60 seconds.
