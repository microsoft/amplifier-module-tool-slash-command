# amplifier-module-tool-slash-command

Extensible slash command system for Amplifier, enabling custom commands defined as Markdown files.

## Overview

This module provides:
- **Custom slash commands** as Markdown files with YAML frontmatter
- **Project-scoped** commands (`.amplifier/commands/`)
- **User-scoped** commands (`~/.amplifier/commands/`)
- **Template substitution** for arguments (`$ARGUMENTS`, `$1`, `$2`, etc.)
- **Tool integration** via `allowed-tools` frontmatter
- **Namespace support** via subdirectories

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
allowed-tools: [tool1, tool2]  # Optional: restrict which tools can be used
argument-hint: [arg1] [arg2]   # Optional: shown in autocomplete
model: provider/model-name     # Optional: override session model
```

### Template Variables

- `$ARGUMENTS` - All arguments as a single string
- `$1`, `$2`, `$3`, ... - Individual positional arguments
- `{{$1 or "default"}}` - Variable with fallback value

### Examples

**Simple command:**
```markdown
---
description: Explain code in simple terms
---
Explain this code in simple, beginner-friendly terms: $ARGUMENTS
```

**With fallback:**
```markdown
---
description: Optimize code for performance
argument-hint: [file-path]
---
Analyze {{$1 or "current file"}} for performance bottlenecks and suggest optimizations.
```

**With tool restrictions:**
```markdown
---
description: Security audit
allowed-tools: [read_file, grep]
---
Perform security audit on {{$1}}:
- Check for SQL injection vulnerabilities
- Look for XSS risks
- Scan for hardcoded secrets
- Review authentication/authorization
```

## Namespacing

Organize commands in subdirectories:

```
.amplifier/commands/
├── frontend/
│   ├── review.md      # /review (shown as "project:frontend")
│   └── test.md        # /test (shown as "project:frontend")
└── backend/
    ├── review.md      # /review (shown as "project:backend")
    └── deploy.md      # /deploy (shown as "project:backend")
```

Commands with the same name in different namespaces are distinguished by their description in `/help`.

## Architecture

### Module Structure

```
slash_command/
├── __init__.py           # Module entry point
├── tool.py               # Tool implementation (slash_command tool)
├── command_loader.py     # Discovers and loads .md files
├── parser.py             # Parses frontmatter and templates
├── executor.py           # Executes commands with substitution
└── registry.py           # Command registry management
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

Execute a custom slash command programmatically.

**Parameters:**
- `command` (str): Command name (without leading `/`)
- `args` (str, optional): Command arguments

**Returns:**
- Command output as string

**Example:**
```python
result = await tools["slash_command"](
    command="review",
    args="src/auth.py"
)
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
pytest --cov=slash_command
```

### Validation

```bash
amplifier-core validate tool .
```

## Example Commands

See `examples/commands/` for ready-to-use commands:
- `review.md` - Code review
- `test.md` - Generate tests
- `security.md` - Security audit
- `optimize.md` - Performance optimization
- `explain.md` - Code explanation
- `document.md` - Generate documentation

## Integration with amplifier-app-cli

To integrate with amplifier-app-cli's CommandProcessor:

```python
from slash_command.registry import CommandRegistry

# Initialize registry
registry = CommandRegistry(session.coordinator)

# Load commands
registry.discover_commands()

# Get commands for registration
custom_commands = registry.get_command_dict()

# Merge with CommandProcessor.COMMANDS
command_processor.register_dynamic_commands(custom_commands)
```

## Roadmap

- [ ] Bash execution (`!` prefix for shell commands)
- [ ] File references (`@` prefix for @mentions)
- [ ] Character budget limits (prevent context overflow)
- [ ] Permission controls (sensitive command restrictions)
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
