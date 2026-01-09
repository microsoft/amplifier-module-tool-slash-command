---
description: Review GitHub issues with no comments that need attention
argument-hint: "[repo or org/repo]"
---

Use the gh CLI to find and analyze GitHub issues that have no comments and may need attention.

Repository: {{$1 or "microsoft/amplifier"}}

Steps:
1. Run `gh issue list --repo {{$1 or "microsoft/amplifier"}} --state open --json number,title,author,createdAt,labels,comments --limit 50`
2. Filter to issues where comments array is empty or has 0 items
3. Sort by creation date (oldest first - these need attention most)
4. For each uncommented issue, summarize:
   - Issue number and title
   - Who opened it and when
   - Labels if any
   - A brief assessment: is this actionable, needs-info, or stale?

Present as a prioritized list with recommendations for which issues to address first.
