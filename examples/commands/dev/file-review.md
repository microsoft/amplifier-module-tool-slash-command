---
description: Review a file with its recent git history
argument-hint: "<file>"
allowed-tools: [bash]
max-chars: 15000
---

Review this file with its history context:

## File: $1

### Current Content
@$1

### Recent Changes (last 5 commits)
!`git log --oneline -5 -- "$1" 2>/dev/null || echo "No git history for this file"`

### Last Modified By
!`git log -1 --format="%an <%ae> on %ad" -- "$1" 2>/dev/null || echo "Unknown"`

Please analyze:
1. Code quality and structure
2. Potential improvements
3. Any issues based on recent change patterns
