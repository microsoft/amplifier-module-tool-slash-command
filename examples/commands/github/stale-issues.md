---
description: Find stale issues that may need closing or follow-up
argument-hint: "[repo] [days:30]"
---

Find issues in {{$1 or "microsoft/amplifier"}} that haven't had activity in {{$2 or "30"}} days.

Steps:
1. Run `gh issue list --repo {{$1 or "microsoft/amplifier"}} --state open --json number,title,author,createdAt,updatedAt,labels,comments --limit 100`
2. Filter to issues where updatedAt is more than {{$2 or "30"}} days ago
3. Categorize each stale issue:
   - **Close candidate**: No recent activity, vague description, or superseded
   - **Needs ping**: Good issue but author went silent
   - **Needs triage**: No labels or unclear priority
   - **Still valid**: Important but blocked on something

Provide actionable recommendations for each category.
