---
description: Summarize recent PR activity in a repository
argument-hint: "[repo] [days:7]"
---

Analyze recent pull request activity for {{$1 or "microsoft/amplifier"}}.

Time period: last {{$2 or "7"}} days

Steps:
1. Run `gh pr list --repo {{$1 or "microsoft/amplifier"}} --state all --json number,title,author,state,createdAt,mergedAt,closedAt,additions,deletions,reviewDecision --limit 30`
2. Filter to PRs created or merged in the last {{$2 or "7"}} days
3. Provide a summary:
   - Total PRs opened, merged, and closed
   - Top contributors by PR count
   - Largest PRs by lines changed
   - Any PRs waiting for review (state=OPEN, no reviewDecision)

Keep the summary concise and actionable.
