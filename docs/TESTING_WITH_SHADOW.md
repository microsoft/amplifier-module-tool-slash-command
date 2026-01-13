# Testing Slash Commands with Shadow Environments

This guide shows how to test the experimental slash command system using Amplifier's shadow environments.

## What You're Testing

- **Slash Command Module**: `microsoft/amplifier-module-tool-slash-command` (public)
- **Modified CLI**: `robotdad/amplifier-app-cli@feat/custom-slash-commands`

The modified CLI integrates with the slash command module to provide extensible `/commands` in interactive sessions.

## Prerequisites

- Amplifier installed (`uv tool install git+https://github.com/microsoft/amplifier`)
- API key set (`ANTHROPIC_API_KEY` environment variable)
- The `shadow` bundle/tool available in your Amplifier session

## Quick Start (In an Amplifier Session)

Ask Amplifier to set up a test environment:

```
Create a shadow environment to test the slash command system from 
microsoft/amplifier-module-tool-slash-command with the modified CLI 
from robotdad/amplifier-app-cli@feat/custom-slash-commands
```

Or do it step-by-step:

### 1. Create Shadow Environment

```python
# In your Amplifier session, use the shadow tool:
shadow create \
  --name slash-test \
  --local-sources amplifier-app-cli:robotdad/amplifier-app-cli
```

### 2. Install the Modified CLI

```bash
shadow exec slash-test "uv tool install 'git+https://github.com/robotdad/amplifier-app-cli@feat/custom-slash-commands'"
```

### 3. Set Up Test Commands

```bash
# Copy example commands to user directory
shadow exec slash-test "
  git clone https://github.com/microsoft/amplifier-module-tool-slash-command /tmp/slash-cmd
  mkdir -p ~/.amplifier/commands
  cp -r /tmp/slash-cmd/examples/commands/* ~/.amplifier/commands/
"
```

### 4. Inject Your API Key

```bash
# From your host, create a key file and inject it
echo "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY" > /tmp/keys.env
shadow inject slash-test /tmp/keys.env /home/amplifier/.amplifier/keys.env
```

### 5. Test the Commands

```bash
# List available commands
shadow exec slash-test "
  export \$(cat ~/.amplifier/keys.env | xargs)
  amplifier --help
"

# The modified CLI should show custom commands in /help
```

## Available Test Commands

| Command | Description |
|---------|-------------|
| `/issues-no-comments [repo]` | Find GitHub issues needing attention |
| `/pr-activity [repo] [days]` | Summarize recent PR activity |
| `/stale-issues [repo] [days]` | Find stale issues |
| `/git-summary [path]` | Analyze git status |
| `/standup [days]` | Generate standup from git history |
| `/todo-scan [path]` | Find TODO/FIXME comments |
| `/review [file]` | Code review |
| `/explain [code]` | Explain code |
| `/test [file]` | Generate tests |

## How It Works

1. **Command Discovery**: Commands are `.md` files in:
   - `~/.amplifier/commands/` (user-level)
   - `.amplifier/commands/` (project-level)

2. **Template Substitution**: Commands use `$ARGUMENTS`, `$1`, `$2`, and `{{$1 or "default"}}` for argument handling

3. **Execution**: When you type `/review src/main.py`, the CLI:
   - Finds the command template
   - Substitutes arguments
   - Sends the result as a prompt to the LLM

## Creating Your Own Commands

```markdown
---
description: Your command description (shown in /help)
argument-hint: "[optional-args]"
---

Your prompt template here.

Use {{$1 or "default"}} for optional arguments with defaults.
Use $ARGUMENTS for all arguments as-is.
```

## Cleanup

```bash
shadow destroy slash-test
```

## Feedback

This is experimental! Please share feedback on:
- Command discovery and loading
- Template substitution
- CLI integration
- Ideas for useful built-in commands
