---
bundle:
  name: slash-commands-demo
  version: 0.1.0
  description: Demo bundle showing extensible slash commands

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main

tools:
  - module: tool-slash-command
    source: git+https://github.com/robotdad/amplifier-module-tool-slash-command@main
---

# Slash Commands Demo Bundle

This bundle demonstrates the extensible slash command system.

## Custom Commands

Create custom commands by adding `.md` files to:
- `.amplifier/commands/` (project-level)
- `~/.amplifier/commands/` (user-level)

### Command Format

```markdown
---
description: Short description shown in /help
argument-hint: "[optional] [args]"
allowed-tools: [read_file, grep]  # Optional: restrict tools
---

Your prompt template here.

Use $ARGUMENTS for all args, or $1, $2 for positional.
Use {{$1 or "default"}} for fallback values.
```

## Example Commands

See `examples/commands/` in the module repo for ready-to-use commands:
- `/review` - Code review
- `/test` - Generate tests  
- `/security` - Security audit
- `/optimize` - Performance review
- `/explain` - Code explanation
- `/document` - Generate docs

## Usage

1. Copy example commands to `.amplifier/commands/`
2. Run amplifier with this bundle
3. Use `/help` to see available commands
4. Use `/reload-commands` after adding new commands

---

@foundation:context/shared/common-system-base.md
