---
description: Scan codebase for TODO/FIXME comments and prioritize them
argument-hint: "[path:.]"
---

Scan {{$1 or "the current directory"}} for TODO, FIXME, HACK, and XXX comments.

Steps:
1. Run `grep -rn "TODO\|FIXME\|HACK\|XXX" {{$1 or "."}} --include="*.py" --include="*.ts" --include="*.js" --include="*.md" 2>/dev/null | head -50`
2. Group findings by type (TODO vs FIXME vs HACK)
3. For each item, assess:
   - Is this still relevant?
   - What's the effort level (quick fix vs major work)?
   - Any that look stale or already done?

Provide a prioritized action list:
1. **Quick wins** - Items that could be fixed in < 30 min
2. **Should track** - Items that need issues created
3. **Clean up** - Stale TODOs that should just be removed
