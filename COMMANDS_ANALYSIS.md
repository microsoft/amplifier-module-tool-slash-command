# Amplifier Slash Commands - Feature Analysis

## Executive Summary

This document analyzes Claude Code's slash command system and recommends which commands should be added to Amplifier CLI. The analysis prioritizes commands that enhance user productivity, align with Amplifier's modular philosophy, and provide clear value over existing functionality.

## Current State

### Amplifier's Existing Slash Commands (Interactive REPL)

| Command | Purpose |
|---------|---------|
| `/think` | Enable read-only planning mode |
| `/do` | Exit plan mode, allow modifications |
| `/save` | Save conversation transcript |
| `/status` | Show session status |
| `/clear` | Clear conversation context |
| `/help` | Show available commands |
| `/config` | Show current configuration |
| `/tools` | List available tools |
| `/agents` | List available agents |
| `/allowed-dirs` | Manage allowed write directories |
| `/denied-dirs` | Manage denied write directories |

**Limitation**: Commands are hardcoded in `CommandProcessor.COMMANDS` dict - no extensibility mechanism.

### Claude Code's Command System

**Built-in Commands**: 40+ commands covering:
- Session management (resume, rename, export, rewind)
- Context management (compact, context visualization, memory editing)
- Development workflow (review, bug reporting, security review)
- Integration (MCP, IDE, GitHub, plugins)
- Configuration (model selection, permissions, hooks)
- Monitoring (cost, usage, stats, doctor)

**Extensibility**:
- Custom commands as Markdown files
- Project-scoped (`.claude/commands/`) and user-scoped (`~/.claude/commands/`)
- Frontmatter for metadata and configuration
- Template substitution for arguments
- Bash execution and file references
- SlashCommand tool for programmatic invocation

## Recommended Commands for Amplifier

### Priority 1: Critical Missing Features

#### 1. `/compact` - Context Compression
**Value**: Essential for long conversations hitting context limits

```markdown
**Syntax**: /compact [focus-instructions]

**Purpose**: Compress conversation history while preserving key information

**Use Cases**:
- Long debugging sessions approaching token limits
- Refactor conversation to focus on specific topic
- Remove obsolete context from earlier mistakes

**Example**:
> /compact Focus on the authentication implementation only

**Implementation Notes**:
- Use provider's summarization capability
- Preserve system instructions and agent configuration
- Mark compaction point in transcript for debugging
```

**Priority Justification**: Context limits are a real pain point. This is a must-have.

---

#### 2. `/context` - Context Visualization
**Value**: Transparency into token usage prevents surprises

```markdown
**Syntax**: /context

**Purpose**: Show context breakdown as colored grid or structured display

**Output Example**:
┌─────────────────────────────────────┐
│ Context Usage: 45,234 / 200,000    │
├─────────────────────────────────────┤
│ System Instructions:    8,432 (19%) │
│ Conversation History:  28,901 (64%) │
│ @mentioned Files:       5,234 (12%) │
│ Agent Context:          2,667 (6%)  │
└─────────────────────────────────────┘

**Implementation Notes**:
- Query context manager for message breakdown
- Calculate token counts (use provider's tokenizer)
- Warn when approaching limits (>80%)
```

**Priority Justification**: Users need visibility into what's consuming context budget.

---

#### 3. `/cost` - Token Usage Statistics
**Value**: Cost awareness for budget-conscious users

```markdown
**Syntax**: /cost

**Purpose**: Display token usage and estimated costs for current session

**Output Example**:
Session Cost Analysis
─────────────────────
Input tokens:   12,450 ($0.15)
Output tokens:   3,892 ($0.47)
Total cost:             $0.62

Recent turns:
  #1: $0.08 (1.2k in, 450 out)
  #2: $0.12 (1.8k in, 680 out)
  #3: $0.15 (2.1k in, 890 out)

**Implementation Notes**:
- Hook into provider usage tracking
- Store per-turn token counts
- Use provider-specific pricing
- Aggregate across session
```

**Priority Justification**: Cost transparency builds trust and helps users optimize usage.

---

#### 4. `/export` - Enhanced Transcript Export
**Value**: Better than current `/save` - more formats and destinations

```markdown
**Syntax**: /export [filename] [--format=json|markdown|html]

**Purpose**: Export conversation in various formats

**Formats**:
- JSON: Complete transcript with metadata
- Markdown: Human-readable conversation log
- HTML: Styled output for sharing/documentation

**Example**:
> /export debugging-session.md --format=markdown
✓ Exported to ~/.amplifier/projects/myapp/sessions/abc123/debugging-session.md

**Implementation Notes**:
- Extend current save functionality
- Add markdown formatter (code blocks, thinking blocks)
- Add HTML template with syntax highlighting
- Support clipboard copy (--clipboard flag)
```

**Priority Justification**: Current `/save` is JSON-only. Users want shareable formats.

---

#### 5. `/memory` - Edit Memory Files
**Value**: Quick access to AGENTS.md without leaving session

```markdown
**Syntax**: /memory [edit|show]

**Purpose**: View or edit AGENTS.md memory file in-session

**Behavior**:
- /memory show: Display current AGENTS.md content
- /memory edit: Open in $EDITOR (if available) or provide inline edit prompt

**Use Cases**:
- Document discovered patterns mid-session
- Update agent preferences without exiting
- Record project-specific conventions

**Implementation Notes**:
- Locate AGENTS.md (check .amplifier/, then ~/.amplifier/)
- Show diff before/after edits
- Warn that changes apply to future messages (not retroactive)
```

**Priority Justification**: Friction-free memory updates improve long-term productivity.

---

### Priority 2: High-Value Enhancements

#### 6. `/rename` - Session Naming
**Value**: Organize session history meaningfully

```markdown
**Syntax**: /rename <name>

**Purpose**: Give current session a memorable name

**Example**:
> /rename auth-bug-investigation
✓ Session renamed: auth-bug-investigation

**Implementation Notes**:
- Update session metadata in SessionStore
- Use name for resume command (amplifier resume auth-bug-investigation)
- Slug generation (lowercase, hyphens)
```

---

#### 7. `/rewind` - Conversation Rollback
**Value**: Undo mistakes without starting over

```markdown
**Syntax**: /rewind [n-turns|message-id]

**Purpose**: Roll back conversation to earlier state

**Examples**:
> /rewind 2          # Go back 2 turns
> /rewind abc123     # Go back to specific message ID

**Implementation Notes**:
- Truncate context to specified point
- Backup current state before rewind
- Show diff of what's being removed
- Emit rewind event for hooks
```

---

#### 8. `/doctor` - Health Check
**Value**: Self-service debugging

```markdown
**Syntax**: /doctor

**Purpose**: Diagnose common configuration issues

**Checks**:
- Provider connectivity and authentication
- Module availability and versions
- Configuration validity
- File permissions
- Cache integrity

**Output Example**:
Amplifier Health Check
─────────────────────
✓ Provider: anthropic (claude-sonnet-4.5)
✓ Modules: 12 loaded, 0 failed
✓ Configuration: Valid
✗ Cache: 3 stale modules detected
  └─ Run: amplifier cache clean

**Implementation Notes**:
- Ping provider API
- Validate module contracts
- Check file permissions on .amplifier/
- Scan for common misconfigurations
```

---

#### 9. `/review` - Request Code Review
**Value**: Streamlined workflow for common task

```markdown
**Syntax**: /review [file-or-directory]

**Purpose**: Delegate to code review agent with standardized prompt

**Behavior**:
- If file specified: Review that file
- If no file: Review git diff
- Uses foundation:code-reviewer agent (or falls back to inline prompt)

**Implementation Notes**:
- Check for code-reviewer agent availability
- Pass file contents or git diff
- Standard review checklist (security, performance, style, bugs)
```

---

#### 10. `/model` - Switch Model Mid-Session
**Value**: Cost optimization and capability matching

```markdown
**Syntax**: /model [provider/model-name]

**Purpose**: Change model for subsequent messages

**Examples**:
> /model                          # Show current model
> /model anthropic/haiku          # Switch to Haiku
> /model openai/gpt-4o            # Switch to GPT-4o

**Implementation Notes**:
- Update provider configuration
- Emit model-changed event
- Show cost implications
- Preserve conversation history
```

---

### Priority 3: Nice-to-Have

#### 11. `/stats` - Usage Analytics
**Value**: Gamification and self-awareness

```markdown
**Syntax**: /stats [daily|weekly|monthly]

**Purpose**: Visualize usage patterns

**Metrics**:
- Sessions per day/week/month
- Most-used agents
- Token consumption trends
- Streaks (consecutive days)
- Model distribution

**Implementation Notes**:
- Aggregate from SessionStore metadata
- Store daily rollups for performance
- ASCII chart visualization
```

---

#### 12. `/diff` - Show Pending Changes
**Value**: Awareness of what's about to be modified

```markdown
**Syntax**: /diff

**Purpose**: Show git diff of uncommitted changes

**Use Cases**:
- Review AI's modifications before committing
- Verify no unintended changes
- Copy-paste for PR descriptions

**Implementation Notes**:
- Run git diff
- Syntax highlight output
- Group by file
```

---

#### 13. `/undo` - Revert Last File Change
**Value**: Quick rollback of bad edits

```markdown
**Syntax**: /undo [file-path]

**Purpose**: Revert last write/edit operation

**Behavior**:
- If file specified: Revert that file
- If no file: Show list of recent changes to pick from

**Implementation Notes**:
- Track file modification events via hooks
- Store before/after snapshots
- Use git checkout for git-tracked files
- Use backup files for non-git files
```

---

## Commands NOT Recommended

These Claude Code commands are not a good fit for Amplifier:

### `/mcp` - MCP Server Management
**Reason**: Amplifier has `tool-mcp` module. Command-line `amplifier module` interface is sufficient. Adding REPL command would be redundant.

### `/plugin` - Plugin Management
**Reason**: Amplifier uses bundles, not plugins. Different architecture.

### `/bashe` - Background Tasks
**Reason**: Niche feature. Tool-bash already supports `run_in_background` parameter. Don't need dedicated command.

### `/statusline` - Status Line UI
**Reason**: Terminal UI customization is out of scope. Rich console already provides good UX.

### `/vim` - Vim Mode
**Reason**: Prompt_toolkit already has vim keybindings. Configuration, not a command.

### `/sandbox` - Sandboxed Bash
**Reason**: Docker/container execution is better suited to infrastructure tooling. Too complex for a command.

### `/pr-comments` - PR Comments Viewer
**Reason**: Use `gh` CLI or web interface. Not core to Amplifier's value prop.

### `/install-github-app` - GitHub Actions Setup
**Reason**: One-time setup, not a recurring command. Documentation is better.

## Implementation Strategy

### Phase 1: Priority 1 Commands (Critical)
- `/compact` - Context compression
- `/context` - Usage visualization
- `/cost` - Cost tracking
- `/export` - Enhanced export
- `/memory` - AGENTS.md editing

**Timeline**: 2-3 weeks
**Effort**: Medium (requires provider integration for compact/context)

### Phase 2: Priority 2 Commands (High Value)
- `/rename` - Session naming
- `/rewind` - Conversation rollback
- `/doctor` - Health checks
- `/review` - Code review workflow
- `/model` - Model switching

**Timeline**: 2 weeks
**Effort**: Low-Medium (mostly composition of existing capabilities)

### Phase 3: Priority 3 Commands (Nice-to-Have)
- `/stats` - Usage analytics
- `/diff` - Git diff viewer
- `/undo` - File revert

**Timeline**: 1-2 weeks
**Effort**: Low (UI and state management)

## Extensibility Architecture

### Custom Command Format

Commands are Markdown files with YAML frontmatter:

```markdown
---
description: Brief description of command
allowed-tools: [tool-name, ...]
argument-hint: [arg1] [arg2] [optional-arg]
model: provider/model-name
disable-model-invocation: false
---

# Command Instructions

Template content with variable substitution:
- $ARGUMENTS - All arguments as string
- $1, $2, $3 - Individual positional arguments
- {{$1 or "default"}} - With fallback

## Bash Execution

Commands can execute bash:
!`git status`

## File References

Commands can reference files:
Review @src/auth.py for security issues
```

### Discovery Locations

1. `.amplifier/commands/` - Project-scoped (versioned)
2. `~/.amplifier/commands/` - User-scoped (personal)
3. Precedence: Project > User (project commands override)

### Namespacing

Subdirectories create namespaces:
- `.amplifier/commands/frontend/review.md` → `/review` (shows as "project:frontend" in help)
- `.amplifier/commands/backend/review.md` → `/review` (shows as "project:backend" in help)

Both can coexist; description shows which namespace they're from.

## Success Metrics

- **Adoption**: % of sessions using custom commands
- **Productivity**: Reduction in command-line exits for common tasks
- **Community**: # of shared custom commands in ecosystem
- **Retention**: Do users who adopt commands have higher retention?

## Risks and Mitigations

### Risk: Command Bloat
**Mitigation**: Start conservative (Priority 1 only). Add more based on user feedback.

### Risk: Security (Arbitrary Bash Execution)
**Mitigation**: 
- Commands inherit session's allowed-tools restrictions
- Bash execution requires explicit `allowed-tools: [bash]`
- Hooks can intercept and approve/deny
- User education on reviewing command files

### Risk: Discoverability
**Mitigation**:
- `/help` shows all custom commands with descriptions
- Create amplifier-commands community repo for sharing
- Documentation with examples
- Default commands shipped with foundation

### Risk: Complexity
**Mitigation**:
- Start with simple text substitution
- Add advanced features (bash, file refs) incrementally
- Clear error messages for malformed commands
- Schema validation with helpful feedback

## Conclusion

Adding extensible slash commands to Amplifier will:
1. **Close feature gap** with Claude Code
2. **Empower users** to build custom workflows
3. **Enable ecosystem** to share best practices
4. **Maintain simplicity** through modular architecture

The proposed architecture aligns with Amplifier's philosophy: simple, modular, and user-extensible. Starting with Priority 1 commands provides immediate value while establishing infrastructure for community innovation.
