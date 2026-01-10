---
description: Audit project dependencies for issues
argument-hint: ""
allowed-tools: [bash]
max-chars: 10000
---

## Dependency Audit

### Python Dependencies
!`pip list --outdated 2>/dev/null | head -20 || echo "No pip available"`

### Security Check (if pip-audit available)
!`pip-audit 2>/dev/null | head -30 || echo "pip-audit not installed - consider: pip install pip-audit"`

### Requirements Files
!`cat requirements*.txt 2>/dev/null | head -30 || cat pyproject.toml 2>/dev/null | grep -A 30 "dependencies" | head -30 || echo "No requirements found"`

### Node Dependencies (if applicable)
!`npm outdated 2>/dev/null | head -15 || echo "No npm project"`

Please analyze:
1. Which dependencies need updates?
2. Are there any security concerns?
3. Recommendations for dependency management
