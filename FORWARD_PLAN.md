# Forward Plan - Slash Command System

> **Reference**: Aligned with [Claude Code Slash Commands](https://code.claude.com/docs/en/slash-commands) feature set

## Feature Comparison: Claude Code vs Amplifier

| Feature | Claude Code | Amplifier Status |
|---------|-------------|------------------|
| **Core Features** | | |
| Project commands (`.claude/commands/`) | Yes | Yes `.amplifier/commands/` |
| Personal commands (`~/.claude/commands/`) | Yes | Yes `~/.amplifier/commands/` |
| Namespacing via subdirectories | Yes | Yes |
| Precedence (project > user) | Yes | Yes |
| **Arguments** | | |
| `$ARGUMENTS` (all args) | Yes | Yes |
| `$1`, `$2`, etc. (positional) | Yes | Yes |
| `{{$1 or "default"}}` fallbacks | Not documented | Yes |
| **Template Processing** | | |
| Bash execution `` !`command` `` | Yes | Yes (E2E verified) |
| File references `@path` | Yes | Yes (code complete) |
| **Frontmatter** | | |
| `description` | Yes | Yes |
| `argument-hint` | Yes | Yes |
| `allowed-tools` (list) | Yes `[bash]` | Yes |
| `allowed-tools` (granular) | Yes `Bash(git add:*)` | Phase 3 |
| `model` (override) | Yes | Phase 4 |
| `disable-model-invocation` | Yes | Phase 4 |
| `hooks` (per-command) | Yes | **Use hooks-shell module** |
| `max-chars` (char budget) | Yes (env var) | Yes (frontmatter) |
| `requires-approval` | Not in Claude Code | Yes (our addition) |
| **Advanced Features** | | |
| Skill tool (LLM invokes commands) | Yes | Phase 4 |
| Plugin commands | Yes | Phase 4 |
| MCP slash commands | Yes | Phase 4 |
| Character budget limit | Yes 15k default | Yes Per-command only |
| Autocomplete anywhere in input | Yes | Not planned |

---

## Phase 1: Core Integration - COMPLETE

### 1.1 Core Module
- [x] Markdown-based command definition with YAML frontmatter
- [x] Command discovery from `.amplifier/commands/` and `~/.amplifier/commands/`
- [x] Template variable substitution (`$ARGUMENTS`, `$1`, `$2`, etc.)
- [x] Fallback syntax `{{$1 or "default"}}`
- [x] Namespace support via subdirectories
- [x] Command registry with precedence (project > user)
- [x] Full test suite (29 tests)

### 1.2 CLI Integration
- [x] Modify `CommandProcessor` in amplifier-app-cli
- [x] Load commands on session start
- [x] Merge custom commands into command processor
- [x] Update `/help` to show custom commands with descriptions
- [x] Add `/reload-commands` for development workflow
- [x] README documentation

### 1.3 Frontmatter Support
- [x] `description` - Brief description
- [x] `argument-hint` - Shown in help/autocomplete
- [x] `allowed-tools` - List of tools command can use

---

## Phase 2: Template Processing - COMPLETE

### 2.1 Bash Command Execution - COMPLETE
Execute bash commands and substitute output into template.

**Syntax:**
```markdown
---
description: Create commit with context
allowed-tools: [bash]
---

## Current Status
!`git status`

## Recent Changes  
!`git diff HEAD`

Based on the above, create an appropriate commit message.
```

**Implementation:**
- [x] Detect `` !`command` `` inline syntax
- [x] Detect `` !```\ncommand\n``` `` block syntax
- [x] Execute via subprocess with timeout
- [x] Substitute output into template
- [x] Require `allowed-tools: [bash]` in frontmatter
- [x] Security: Skip execution if bash not in allowed-tools
- [x] Unit tests (6 tests)
- [x] E2E test with real LLM session

### 2.2 File References - CODE COMPLETE
Include file contents in commands.

**Syntax:**
```markdown
Review the implementation in @src/utils/helpers.js

Compare @src/old-version.js with @src/new-version.js
```

**Implementation:**
- [x] Detect `@path` syntax
- [x] Load file contents
- [x] Handle missing files gracefully
- [x] Respect working directory boundaries
- [x] Unit tests (4 tests)
- [ ] E2E test with real LLM session

### 2.3 Character Budget - CODE COMPLETE
Prevent context overflow from large outputs.

**Syntax:**
```yaml
---
max-chars: 8000
---
```

**Implementation:**
- [x] `max-chars` frontmatter field
- [x] Truncate at sensible boundaries (paragraph > sentence > word)
- [x] Add truncation indicator
- [x] Warn when content truncated
- [ ] E2E test with real LLM session

### 2.4 Approval Gates - CODE COMPLETE
Require approval for sensitive commands.

**Syntax:**
```yaml
---
requires-approval: true
approval-message: "This will modify production. Proceed?"
---
```

**Implementation:**
- [x] `requires-approval` frontmatter field
- [x] `approval-message` frontmatter field
- [x] Return approval requirement in ExecutionResult
- [ ] CLI integration to show approval dialog
- [ ] E2E test with real LLM session

### 2.5 Tool Module Integration - COMPLETE
- [x] Package renamed to `amplifier_module_tool_slash_command`
- [x] Tool protocol implementation (name, description, input_schema, execute)
- [x] Entry point in pyproject.toml
- [x] E2E test: Tool loads and LLM can invoke it
- [x] 43 unit tests passing

---

## Phase 3: Granular Permissions

### 3.1 Granular Tool Permissions
Align with Claude Code's fine-grained `allowed-tools`:

```yaml
---
description: Safe git operations only
allowed-tools: 
  - Bash(git add:*)
  - Bash(git status:*)
  - Bash(git commit:*)
  - Bash(git diff:*)
---
```

**Implementation:**
- [ ] Parse granular tool specifications `Tool(pattern:*)`
- [ ] Validate bash commands against allowed patterns
- [ ] Block execution if command doesn't match any pattern
- [ ] Clear error messages when blocked
- [ ] Unit tests
- [ ] E2E tests

**Design:**
```python
@dataclass
class GranularPermission:
    tool: str           # "Bash", "Edit", etc.
    pattern: str | None # "git add:*", None = all commands allowed
    
def parse_permission(spec: str) -> GranularPermission:
    """Parse 'Bash(git add:*)' -> GranularPermission"""
    # "Bash" -> GranularPermission(tool="Bash", pattern=None)
    # "Bash(git add:*)" -> GranularPermission(tool="Bash", pattern="git add:*")
```

---

## Phase 4: Advanced Features

### 4.1 Model Override
```yaml
model: claude-3-5-haiku-20241022
```
- [ ] Parse model field
- [ ] Override session model for command execution
- [ ] Restore original model after

### 4.2 Skill Tool (LLM Invokes Commands)
Allow the LLM to programmatically invoke slash commands.

- [ ] Expose command metadata to LLM via tool
- [ ] Handle `disable-model-invocation` flag
- [ ] Respect character budget for command metadata

### 4.3 Command Composition
```markdown
First, run security audit:
/security $1

Then, check code quality:
/review $1
```
- [ ] Detect slash commands in template
- [ ] Execute commands sequentially
- [ ] Aggregate results
- [ ] Prevent infinite recursion

### 4.4 Plugin/Bundle Commands
Commands provided by installed bundles.

- [ ] Discover commands from bundle `commands/` directories
- [ ] Namespace as `(bundle:name)`
- [ ] Support `/bundle:command` invocation pattern

### 4.5 MCP Slash Commands
Commands exposed from MCP servers.

- [ ] Discover prompts from connected MCP servers
- [ ] Expose as `/mcp__server__prompt` commands
- [ ] Pass arguments to MCP prompts

---

## Phase 5: Ecosystem Integration (LAST)

### 5.1 Foundation Bundle Integration
- [ ] Create PR to amplifier-foundation with behavior definition
- [ ] Add `tool-slash-command` as optional behavior
- [ ] Include default commands in foundation
- [ ] Update foundation documentation

### 5.2 Community Command Library
- [ ] Create `amplifier-commands` repository
- [ ] Port example commands from module
- [ ] Contribution guidelines
- [ ] Quality criteria and review process

---

## Per-Command Hooks: Use hooks-shell Module

**Note:** Per-command hooks are NOT implemented in this module. Instead, use the 
[amplifier-module-hooks-shell](https://github.com/robotdad/amplifier-module-hooks-shell) module.

The hooks-shell module provides:
- Shell-based hooks at lifecycle points (PreToolUse, PostToolUse, etc.)
- Regex pattern matching for selective execution
- Claude Code format compatibility
- Hooks embedded in frontmatter (skills, agents, commands)

### Integration Pattern

Slash commands that need hooks should document the required hooks-shell configuration:

**Example: Command with validation hook**

1. Create the slash command (`.amplifier/commands/deploy.md`):
```markdown
---
description: Deploy to production
allowed-tools: [bash]
requires-approval: true
---

Deploy the current branch to production.

!`./scripts/deploy.sh`
```

2. Create the hook (`.amplifier/hooks/deploy-validator/hooks.json`):
```json
{
  "description": "Validate deployment commands",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${AMPLIFIER_HOOKS_DIR}/deploy-validator/check.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

3. Add hooks-shell to your bundle:
```yaml
hooks:
  - module: hooks-shell
    source: git+https://github.com/robotdad/amplifier-module-hooks-shell@main
```

### Why Separate Modules?

1. **Single Responsibility**: Slash commands handle template processing; hooks-shell handles lifecycle hooks
2. **Reusability**: Hooks can be shared across commands, skills, and agents
3. **Claude Code Compatibility**: hooks-shell uses the same format as Claude Code hooks
4. **Already Implemented**: hooks-shell is mature with full test coverage

---

## Current Test Commands

### Phase 1 Commands (basic templates)
| Command | Description |
|---------|-------------|
| `/review` | Request comprehensive code review |
| `/test` | Generate comprehensive unit tests |
| `/security` | Perform security audit on code |
| `/optimize` | Analyze for performance optimization |
| `/explain` | Explain code in simple terms |
| `/document` | Generate comprehensive documentation |

### Phase 2 Commands (bash + file refs)
| Command | Description | Features |
|---------|-------------|----------|
| `/context-dump` | Dump project context | `` !`bash` ``, `max-chars` |
| `/diff-review` | Review git diff | `` !`bash` ``, `max-chars` |
| `/file-review <file>` | Review file with history | `` !`bash` ``, `@file`, `max-chars` |
| `/deps-audit` | Audit dependencies | `` !`bash` ``, `max-chars` |

### Workflow Commands
| Command | Description |
|---------|-------------|
| `/standup` | Generate standup summary |
| `/todo-scan` | Scan for TODO/FIXME comments |
| `/deps-check` | Check for outdated dependencies |

### GitHub Commands (namespaced)
| Command | Description |
|---------|-------------|
| `/pr-activity` | Summarize recent PR activity |
| `/stale-issues` | Find stale issues |
| `/issues-no-comments` | Find uncommented issues |

---

## Repositories

| Repository | Purpose | Status |
|------------|---------|--------|
| `robotdad/amplifier-module-tool-slash-command` | Core module | Public, main branch |
| `robotdad/amplifier-module-hooks-shell` | Shell hooks module | Public, main branch |
| `robotdad/amplifier-app-cli` | Fork with CLI integration | Branch: `feat/custom-slash-commands` |

---

## Immediate Next Steps

1. **Complete Phase 2 E2E tests** - file refs, max-chars, approval gates
2. **Implement Phase 3** - Granular permissions `Bash(git add:*)`
3. **Phase 4 features** - Model override, skill tool, command composition
4. **Phase 5** - Foundation integration (deferred until after Phase 4)

---

## Open Questions

1. ~~Should we support Claude Code's granular `Bash(git add:*)` syntax?~~ **YES - Phase 3**
2. Should commands be discoverable by the LLM (Skill tool pattern)? **Phase 4.2**
3. Should we add MCP slash command support? **Phase 4.5**
4. Where should this module live? (`robotdad` vs `microsoft`) **TBD**
