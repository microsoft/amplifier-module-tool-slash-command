# Shadow Environment Testing Experience

**Date**: 2026-01-09  
**Module**: amplifier-module-tool-slash-command  
**Shadow Version**: Current (amplifier-foundation)

## Summary

Used shadow environments to test a newly created Amplifier module before integration. The shadow environment caught real bugs that would have been missed without isolated testing.

## What We Tested

Created `amplifier-module-tool-slash-command`, an extensible slash command system with:
- YAML frontmatter parser
- Command discovery from filesystem
- Template variable substitution
- Registry and executor components
- 29 unit tests

## The Testing Flow

### 1. Create Shadow with Local Sources

```bash
shadow create \
  --name slash-command-test \
  --local-sources amplifier-module-tool-slash-command:robotdad/amplifier-module-tool-slash-command \
  --local-sources amplifier-core:microsoft/amplifier-core
```

**What happened**: Shadow created a local Gitea server with snapshots of both repositories, including uncommitted changes.

### 2. Git URL Rewriting (The Magic)

Inside the shadow, git config showed:
```
url.http://localhost:3000/robotdad/amplifier-module-tool-slash-command.git
    .insteadOf=https://github.com/robotdad/amplifier-module-tool-slash-command
```

This means `git clone https://github.com/robotdad/...` fetches from the **local snapshot**, not GitHub.

### 3. Install and Test

```bash
# Clone module (uses local snapshot)
git clone https://github.com/robotdad/amplifier-module-tool-slash-command

# Install amplifier-core (also uses local snapshot)
uv pip install "git+https://github.com/microsoft/amplifier-core"

# Run tests
pytest tests/ -v
```

### 4. Bugs Discovered

**First run**: 2 failures out of 29 tests

| Bug | Description | Root Cause |
|-----|-------------|------------|
| `test_parse_command_with_all_fields` | YAML parsing error | `argument-hint: [file-path] [pattern]` interpreted as YAML list, not string |
| `test_substitute_arguments_fallback` | Wrong substitution | Regex `(\$\d+|ARGUMENTS)` should be `(\$\d+|\$ARGUMENTS)` |

### 5. Fix and Verify

1. Fixed bugs locally
2. Destroyed shadow: `shadow destroy slash-command-test`
3. Created new shadow (picks up local changes)
4. Re-ran tests: **29 passed** ✅

### 6. Commit with Confidence

```bash
git commit -m "Fix parser regex for \$ARGUMENTS fallback syntax

Bug found via shadow environment testing"
```

## What Worked Well

### Immediate Value
- **Caught real bugs** - Both bugs would have caused runtime failures
- **Uncommitted changes tested** - Didn't have to commit broken code to test
- **Dependency isolation** - Could test with specific amplifier-core version

### Developer Experience
- **Simple API** - `create`, `exec`, `destroy` is intuitive
- **Fast iteration** - Destroy/create cycle takes seconds
- **Clear feedback** - URL rewriting confirmation was helpful

### Integration Testing Potential
- Could include entire stack (core + foundation + cli)
- Test module loading and registration
- Verify end-to-end command execution

## Feedback for Shadow Environment Maintainer

### What's Great

1. **Local source snapshots** - The killer feature. Testing uncommitted changes is invaluable.

2. **Selective URL rewriting** - Only specified repos are rewritten; everything else goes to real GitHub. This is exactly right.

3. **Container isolation** - Clean environment every time, no pollution from previous tests.

4. **Simple mental model** - "Git clones inside shadow use your local code" is easy to understand.

### Suggestions for Improvement

#### 1. Documentation: Add Common Patterns

Would love a "recipes" section showing:
```markdown
## Pattern: Test Module with Dependencies
shadow create --local-sources mymodule:org/mymodule --local-sources amplifier-core:microsoft/amplifier-core

## Pattern: Full Stack Integration Test
shadow create --local-sources core:... --local-sources foundation:... --local-sources cli:...

## Pattern: Test PR Against Main
shadow create --local-sources feature-branch:org/repo  # Your branch
# Everything else uses main from GitHub
```

#### 2. Shell Compatibility Note

The container uses `sh`, not `bash`. Had to use `. .venv/bin/activate` instead of `source`. Minor, but worth documenting.

#### 3. Consider: Pre-built Test Environment

For common cases like "test a Python module", a helper might be nice:
```bash
shadow test-python --local-sources mymodule:org/mymodule
# Automatically: creates venv, installs deps, runs pytest
```

Though this might be over-engineering - the current primitives are flexible.

#### 4. Consider: Diff Against Real GitHub

After testing, it would be useful to see:
```bash
shadow diff-from-upstream slash-command-test
# Shows: Your local changes vs what's on GitHub
```

This helps verify you're testing the right delta.

#### 5. Session Persistence Option

Sometimes you want to iterate inside a shadow:
```bash
shadow create --persistent  # Don't auto-destroy on error
shadow shell               # Drop into interactive shell
# Debug, fix, re-test
shadow destroy
```

Currently, each `exec` is stateless (new shell). An interactive mode could help debugging.

### Minor Issues Encountered

1. **Lock file collision** - Had git index.lock issues, but that was my host environment, not shadow's fault.

2. **No pytest pre-installed** - Had to install test dependencies manually. Expected, but could document the pattern.

### Overall Assessment

**Rating: 9/10** - Shadow environments are a game-changer for testing Amplifier modules.

The core value proposition - testing local changes in isolation before committing - worked exactly as advertised. Found real bugs, fixed them, and verified fixes all without polluting my environment or pushing broken code.

The only missing piece is more documentation with common patterns. The tool is powerful but you have to discover the patterns yourself.

## Recommended Workflow

For future module development:

```bash
# 1. Write code locally

# 2. Create shadow with local sources
shadow create --name test --local-sources mymodule:org/mymodule

# 3. Run tests in shadow
shadow exec test "cd /workspace && git clone https://github.com/org/mymodule && cd mymodule && uv venv && . .venv/bin/activate && uv pip install -e '.[dev]' && pytest"

# 4. If tests fail: fix locally, destroy, recreate, re-test

# 5. If tests pass: commit and push with confidence

# 6. Clean up
shadow destroy test
```

This caught 2 bugs in our first module. Will use for all future development.

---

*Document created as feedback for shadow environment feature in amplifier-foundation.*
