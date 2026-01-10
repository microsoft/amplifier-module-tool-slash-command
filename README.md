# amplifier-module-tool-slash-command

Extensible slash command system for Amplifier, enabling custom commands defined as Markdown files.

## Overview

This module provides:
- **Custom slash commands** as Markdown files with YAML frontmatter
- **Project-scoped** commands (`.amplifier/commands/`)
- **User-scoped** commands (`~/.amplifier/commands/`)
- **Template substitution** for arguments (`$ARGUMENTS`, `$1`, `$2`, etc.)
- **Bash execution** in templates (`!`command`` syntax)
- **File references** (`@path/to/file` includes file content)
- **Granular permissions** (`Bash(git add:*)` restricts which commands can run)
- **Command composition** (commands can invoke other commands)
- **Model override** (per-command model selection)
- **LLM discovery** (AI can list and invoke commands programmatically)

Inspired by Claude Code's extensible slash command system, adapted for Amplifier's modular architecture.

## Installation

### As an Amplifier Module

Add to your bundle:

```yaml
tools:
  - module: tool-slash-command
    source: git+https://github.com/robotdad/amplifier-module-tool-slash-command@main
```

Or install directly:

```bash
amplifier module add tool-slash-command \
  --source git+https://github.com/robotdad/amplifier-module-tool-slash-command@main
```

## Usage

### Creating Custom Commands

Create a Markdown file in `.amplifier/commands/` (project) or `~/.amplifier/commands/` (personal):

**Example: `.amplifier/commands/review.md`**

```markdown
---
description: Request comprehensive code review
allowed-tools: [read_file, grep, task]
argument-hint: [file-or-directory]
---

Please review {{$1 or "recent changes"}} with focus on:
- Code quality and readability
- Potential bugs or edge cases
- Security vulnerabilities
- Performance considerations
- Best practices compliance
```

### Using Commands

In the Amplifier REPL:

```bash
> /review src/auth.py
# Executes command with file argument

> /review
# Executes command with default (recent changes)
```

### Command Discovery

The module automatically discovers commands from:
1. `.amplifier/commands/` (project-scoped, version controlled)
2. `~/.amplifier/commands/` (user-scoped, personal)

Commands are registered when the session starts.

## Command Format

### Frontmatter Options

```yaml
description: Brief description shown in /help
allowed-tools:                    # Tool restrictions (see Granular Permissions)
  - bash                          # Allow all bash commands
  - Bash(git status:*)            # Allow only specific bash commands
  - read_file                     # Allow specific tools
argument-hint: [arg1] [arg2]      # Shown in autocomplete
model: claude-3-5-haiku-20241022  # Override session model for this command
max-chars: 10000                  # Truncate output to character limit
requires-approval: true           # Require user confirmation before execution
approval-message: "This will..."  # Custom approval prompt
disable-model-invocation: true    # Hide from LLM discovery (user-only command)
```

### Template Variables

- `$ARGUMENTS` - All arguments as a single string
- `$1`, `$2`, `$3`, ... - Individual positional arguments
- `{{$1 or "default"}}` - Variable with fallback value

### Bash Execution

Execute shell commands during template processing:

**Inline bash:**
```markdown
Current branch: !`git branch --show-current`
```

**Block bash:**
```markdown
!```
git status --short
git log --oneline -5
```
```

**Requires** `bash` in `allowed-tools`. See Granular Permissions for fine-grained control.

### File References

Include file contents in templates:

```markdown
Review this code:
@src/main.py

Compare with:
@src/utils.py
```

### Command Composition

Commands can invoke other commands:

```markdown
---
description: Full project review
allowed-tools: [Bash(git status:*), Bash(git diff:*)]
---

## Git Status
/git-status

## Code Review
/review src/

Summarize the project state above.
```

Nested commands are executed and their output is substituted into the parent template.
Maximum nesting depth: 5 levels (prevents infinite loops).

## Granular Permissions

Control exactly which bash commands a slash command can execute:

```yaml
allowed-tools:
  - Bash(git status:*)    # Only git status commands
  - Bash(git diff:*)      # Only git diff commands
  - Bash(git log:*)       # Only git log commands
```

**Pattern matching:**
- `Bash(git add:*)` - Allows `git add .`, `git add -A`, `git add file.txt`
- `Bash(ls:*)` - Allows `ls`, `ls -la`, `ls /path`

**Security:**
- Commands not matching any pattern are **blocked**
- Blocked commands show `[Command blocked: reason]` in output
- Warnings are returned to the caller

**Example - Safe git operations only:**

```markdown
---
description: Safe git status check
allowed-tools:
  - Bash(git status:*)
  - Bash(git diff:*)
  - Bash(git log:*)
---

!`git status`      # Allowed
!`git diff HEAD`   # Allowed
!`git push`        # BLOCKED - not in allowed patterns
!`rm -rf /`        # BLOCKED - not in allowed patterns
```

## LLM Command Discovery (Skill Tool)

The LLM can discover and invoke commands programmatically:

**List available commands:**
```python
result = await tools["slash_command"](operation="list")
# Returns: {"commands": [...], "count": N}
```

**Execute a command:**
```python
result = await tools["slash_command"](
    operation="execute",
    command="review",
    args="src/auth.py"
)
```

**Hiding commands from LLM:**

Add `disable-model-invocation: true` to hide sensitive commands:

```yaml
---
description: Admin-only command
disable-model-invocation: true
---
```

These commands won't appear in `list` and will be blocked if the LLM tries to execute them directly.

## Model Override

Specify a different model for specific commands:

```markdown
---
description: Quick answer using faster model
model: claude-3-5-haiku-20241022
---

Give a brief answer to: $ARGUMENTS
```

The `model_override` is returned in the tool result for the CLI/orchestrator to use.

## Examples

**Simple command:**
```markdown
---
description: Explain code in simple terms
---
Explain this code in simple, beginner-friendly terms: $ARGUMENTS
```

**With bash and file refs:**
```markdown
---
description: Project context dump
allowed-tools: [bash]
---

## Git Status
!`git status --short`

## Recent Commits
!`git log --oneline -10`

## README
@README.md
```

**With granular permissions:**
```markdown
---
description: Safe git operations
allowed-tools:
  - Bash(git status:*)
  - Bash(git diff:*)
---

Current status: !`git status --short`
Changes: !`git diff --stat`
```

**Command composition:**
```markdown
---
description: Full review combining multiple commands
---

/git-status
/file-review README.md

Summarize the above.
```

## Namespacing

Organize commands in subdirectories:

```
.amplifier/commands/
├── frontend/
│   ├── review.md      # /review (namespace: frontend)
│   └── test.md        # /test (namespace: frontend)
└── backend/
    ├── review.md      # /review (namespace: backend)
    └── deploy.md      # /deploy (namespace: backend)
```

Commands with the same name in different namespaces are distinguished by their description in `/help`.

## Architecture

### Module Structure

```
amplifier_module_tool_slash_command/
├── __init__.py           # Module entry point
├── tool.py               # Tool implementation (slash_command tool)
├── command_loader.py     # Discovers and loads .md files
├── parser.py             # Parses frontmatter and templates
├── executor.py           # Executes commands with substitution
├── registry.py           # Command registry management
├── template_processor.py # Bash execution, file refs
└── permissions.py        # Granular permission parsing
```

### Integration Pattern

This module provides a **tool** that can be invoked by:
1. **CommandProcessor** in amplifier-app-cli (interactive REPL)
2. **AI programmatically** via the `slash_command` tool
3. **Other apps** that want extensible commands

### Amplifier Protocol Compliance

Implements the standard Amplifier tool protocol:

```python
async def mount(coordinator, config):
    """Register slash_command tool with coordinator."""
    # Returns cleanup function
```

## API

### Tool: `slash_command`

Execute or discover custom slash commands.

**Parameters:**
- `operation` (str): `"execute"` (default) or `"list"`
- `command` (str): Command name (without leading `/`) - for execute
- `args` (str, optional): Command arguments - for execute

**Execute returns:**
```python
{
    "prompt": "...",                    # Processed template content
    "bash_commands_executed": 3,        # Number of bash commands run
    "files_included": 2,                # Number of files included
    "warnings": ["..."],                # Any warnings (optional)
    "model_override": "model-name",     # If command specifies model (optional)
    "requires_approval": True,          # If approval needed (optional)
}
```

**List returns:**
```python
{
    "commands": [
        {"name": "review", "description": "...", "argument_hint": "..."},
        ...
    ],
    "count": 5,
    "hint": "Use operation='execute' with command='name' to run"
}
```

### Registry Access

The module provides a capability for accessing the command registry:

```python
registry = coordinator.get_capability("slash_command_registry")

# List all commands
commands = registry.list_commands()

# Get command metadata
info = registry.get_command("review")

# Reload commands (useful for development)
registry.reload()
```

## Development

### Setup

```bash
git clone https://github.com/robotdad/amplifier-module-tool-slash-command
cd amplifier-module-tool-slash-command
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Testing

```bash
pytest
pytest --cov=amplifier_module_tool_slash_command
```

### Validation

```bash
amplifier-core validate tool .
```

## Roadmap

- [ ] Bundle/plugin commands (discover from installed bundles)
- [ ] MCP prompt integration (expose MCP prompts as commands)
- [ ] Command marketplace (shared command repository)
- [ ] Command versioning (semantic versioning for commands)

## License

MIT License - See LICENSE file

## Contributing

Contributions welcome! Please:
1. Follow Amplifier's implementation philosophy (ruthless simplicity)
2. Add tests for new features
3. Update documentation
4. Validate with `amplifier-core validate tool .`

## Credits

Inspired by Claude Code's extensible slash command system. Adapted for Amplifier's modular architecture by [@robotdad](https://github.com/robotdad).
