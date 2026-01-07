# Forward Plan - Slash Command System Evolution

## What We've Built

✅ **Core Module Implementation**
- Markdown-based command definition with YAML frontmatter
- Command discovery from `.amplifier/commands/` and `~/.amplifier/commands/`
- Template variable substitution (`$ARGUMENTS`, `$1`, `$2`, etc.)
- Namespace support via subdirectories
- Command registry with precedence (project > user)
- Full test suite covering parser, loader, registry, executor
- Example commands (review, test, security, optimize, explain, document)

✅ **Repository Setup**
- Private GitHub repository: `robotdad/amplifier-module-tool-slash-command`
- MIT License
- Comprehensive README and documentation
- Ready for integration testing

## Phase 1: Integration & Validation (Week 1-2)

### 1.1 Amplifier-App-CLI Integration

**Goal**: Make custom commands available in the Amplifier REPL

**Tasks**:
- [ ] Modify `CommandProcessor` in `amplifier-app-cli/amplifier_app_cli/main.py` to accept dynamic command registration
- [ ] Add `tool-slash-command` to foundation bundle as optional behavior
- [ ] Load commands on session start via `slash_command_registry` capability
- [ ] Merge custom commands into `CommandProcessor.COMMANDS` dict
- [ ] Update `/help` command to show custom commands with descriptions
- [ ] Add `/reload-commands` built-in command for development workflow

**Implementation Pattern**:
```python
# In amplifier-app-cli main.py, after session creation:
registry = coordinator.get_capability("slash_command_registry")
if registry and registry.is_loaded():
    custom_commands = registry.get_command_dict()
    command_processor.register_dynamic_commands(custom_commands)
```

**Testing**:
- Create test commands in `.amplifier/commands/`
- Verify discovery and loading
- Test execution with arguments
- Verify precedence (project > user)
- Test namespace disambiguation

### 1.2 Command Execution Flow

**Goal**: Execute custom commands as prompts to the AI

**Tasks**:
- [ ] Implement `execute_custom_command` action in `CommandProcessor`
- [ ] Use `slash_command_executor` capability to substitute template
- [ ] Pass substituted prompt to `session.execute()`
- [ ] Handle errors gracefully (command not found, substitution failures)

**Implementation Pattern**:
```python
async def handle_command(self, action: str, data: dict):
    if action == "execute_custom_command":
        executor = self.session.coordinator.get_capability("slash_command_executor")
        try:
            prompt = await executor.execute(
                data["metadata"]["name"],
                data.get("args", ""),
                namespace=data["metadata"]["namespace"]
            )
            # Execute the substituted prompt
            await self.session.execute(prompt)
        except ValueError as e:
            return f"Error: {e}"
```

### 1.3 Documentation Updates

**Tasks**:
- [ ] Add section to `amplifier-app-cli` README about custom commands
- [ ] Update user guide with command creation tutorial
- [ ] Document frontmatter options and template syntax
- [ ] Add troubleshooting section (common errors)
- [ ] Create video walkthrough (optional but high value)

### 1.4 Validation & Refinement

**Tasks**:
- [ ] Run amplifier-core validation: `amplifier-core validate tool .`
- [ ] Integration test with real Amplifier session
- [ ] Performance test (load 50+ commands)
- [ ] Error handling edge cases
- [ ] User feedback from early adopters

## Phase 2: Enhanced Features (Week 3-4)

### 2.1 Bash Command Execution

**Goal**: Support `!` prefix for shell command execution

**Syntax**:
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

**Implementation**:
- [ ] Extend parser to detect `!` prefix lines
- [ ] Execute bash commands via `tool-bash`
- [ ] Inject command output into template before substitution
- [ ] Add security warnings to documentation
- [ ] Require explicit `allowed-tools: [bash]` in frontmatter

**Security Considerations**:
- Commands inherit session's bash tool permissions
- Approval hooks can intercept for sensitive commands
- User education on reviewing command files
- Warning when loading commands with bash execution

### 2.2 File References (@mentions)

**Goal**: Support `@` prefix for file content injection

**Syntax**:
```markdown
---
description: Review specific files with context
---

Review the following files for consistency:
- @src/auth.py
- @src/middleware.py
- @tests/test_auth.py

Focus on error handling patterns.
```

**Implementation**:
- [ ] Extend parser to detect `@` prefix
- [ ] Use existing mention resolver from amplifier-app-cli
- [ ] Load file contents and inject into template
- [ ] Handle missing files gracefully
- [ ] Respect file permissions and allowed paths

### 2.3 Character Budget Limits

**Goal**: Prevent context overflow from too many commands

**Implementation**:
- [ ] Add configuration for max character budget (default 15k)
- [ ] Count characters in command descriptions
- [ ] Truncate or omit commands when budget exceeded
- [ ] Warn user in `/help` when commands are hidden
- [ ] Prioritize project commands over user commands

### 2.4 Permission Controls

**Goal**: Restrict sensitive commands with approval gates

**Frontmatter Addition**:
```yaml
requires-approval: true
approval-message: "This command will modify production database. Proceed?"
```

**Implementation**:
- [ ] Add `requires-approval` frontmatter field
- [ ] Hook into existing approval system (hooks-approval)
- [ ] Show approval dialog before execution
- [ ] Log approval decisions
- [ ] Document sensitive command patterns

## Phase 3: Ecosystem Integration (Week 5-6)

### 3.1 Foundation Bundle Integration

**Goal**: Make slash commands available to all Amplifier apps

**Tasks**:
- [ ] Create PR to amplifier-foundation with behavior definition
- [ ] Add `tool-slash-command` as optional behavior
- [ ] Include default commands in foundation
- [ ] Update foundation documentation

**Bundle YAML**:
```yaml
behaviors:
  - name: slash-commands
    description: Extensible custom slash commands
    tools:
      - module: tool-slash-command
        source: git+https://github.com/robotdad/amplifier-module-tool-slash-command@main
```

### 3.2 Community Command Library

**Goal**: Create a shared repository of useful commands

**Structure**:
```
amplifier-commands/
├── README.md
├── development/
│   ├── review.md
│   ├── test.md
│   ├── refactor.md
├── security/
│   ├── audit.md
│   ├── scan-secrets.md
├── documentation/
│   ├── readme.md
│   ├── api-docs.md
└── productivity/
    ├── summarize.md
    ├── explain.md
```

**Tasks**:
- [ ] Create `amplifier-commands` repository
- [ ] Port example commands from module
- [ ] Add installation instructions
- [ ] Create contribution guidelines
- [ ] Add quality criteria and review process
- [ ] Set up GitHub Actions for validation

### 3.3 Discovery & Installation Flow

**Goal**: Make it easy to find and install community commands

**CLI Commands**:
```bash
# Browse available commands
amplifier commands browse

# Install a command
amplifier commands install github:community/review.md

# Search commands
amplifier commands search security

# Update installed commands
amplifier commands update
```

**Implementation**:
- [ ] Add `amplifier commands` subcommand group
- [ ] Implement remote command fetching
- [ ] Add local command cache (~/.amplifier/command-cache/)
- [ ] Version tracking for installed commands
- [ ] Update notifications

### 3.4 App Developer Guide

**Goal**: Enable other Amplifier apps to use slash commands

**Documentation**:
- [ ] Integration guide for app developers
- [ ] API reference for registry/executor
- [ ] Example integration code
- [ ] Best practices for app-specific commands
- [ ] Testing strategies

**Example Apps to Target**:
- amplifier-app-transcribe (custom commands for video processing)
- amplifier-app-blog-creator (content generation commands)
- amplifier-app-voice (voice-specific commands)

## Phase 4: Advanced Features (Week 7-8)

### 4.1 Command Composition

**Goal**: Allow commands to call other commands

**Syntax**:
```markdown
---
description: Full code review workflow
---

First, run security audit:
/security $1

Then, check code quality:
/review $1

Finally, verify test coverage:
/test $1
```

**Implementation**:
- [ ] Detect slash commands in template
- [ ] Execute commands sequentially
- [ ] Aggregate results
- [ ] Handle errors in chain
- [ ] Prevent infinite recursion

### 4.2 Model Selection per Command

**Goal**: Use optimal model for each command type

**Current Frontmatter**:
```yaml
model: anthropic/haiku  # Fast, cheap model for simple tasks
```

**Enhancement**:
```yaml
model:
  default: anthropic/haiku
  fallback: anthropic/sonnet  # If haiku fails
  reasoning: Use Haiku for speed; Sonnet if complexity detected
```

**Implementation**:
- [ ] Parse model configuration
- [ ] Override session model temporarily
- [ ] Restore original model after execution
- [ ] Track model usage per command
- [ ] Show model in command execution logs

### 4.3 Command Versioning

**Goal**: Track command versions and manage updates

**Frontmatter Addition**:
```yaml
version: 1.2.0
changelog:
  - 1.2.0: Added support for multiple file patterns
  - 1.1.0: Improved error handling
  - 1.0.0: Initial release
```

**Implementation**:
- [ ] Add version field validation
- [ ] Track installed command versions
- [ ] Check for updates automatically
- [ ] Show changelog on update
- [ ] Support version pinning

### 4.4 Command Analytics

**Goal**: Understand which commands are most valuable

**Metrics**:
- Command invocation frequency
- Average execution time
- Success/failure rates
- User ratings (optional feedback)
- Model costs per command

**Implementation**:
- [ ] Hook into event system to track usage
- [ ] Store metrics in local database
- [ ] `/stats commands` to view analytics
- [ ] Privacy-preserving aggregation
- [ ] Export for community insights

## Phase 5: Polish & Optimization (Ongoing)

### 5.1 Performance Optimization

**Tasks**:
- [ ] Lazy loading of commands (don't parse all at startup)
- [ ] Command caching (parse once, cache result)
- [ ] Parallel command discovery
- [ ] Minimize file I/O
- [ ] Benchmark and profile

### 5.2 Error Messages & UX

**Tasks**:
- [ ] Clear error messages with suggestions
- [ ] Command validation on load (warn about issues)
- [ ] Syntax highlighting in examples
- [ ] Autocomplete support (if feasible)
- [ ] Rich command help display

### 5.3 Testing & Quality

**Tasks**:
- [ ] Increase test coverage to 95%+
- [ ] Add integration tests with real Amplifier session
- [ ] Performance benchmarks
- [ ] Compatibility testing across platforms
- [ ] Security audit

### 5.4 Community Building

**Tasks**:
- [ ] Blog post announcing feature
- [ ] Video tutorial series
- [ ] Community call for feedback
- [ ] Showcase impressive community commands
- [ ] Contributor recognition

## Success Metrics

### Technical Metrics
- **Module Quality**: 95%+ test coverage, passes all validation
- **Performance**: <100ms command discovery, <10ms substitution
- **Reliability**: <1% error rate in production use
- **Compatibility**: Works with all Amplifier providers and orchestrators

### Adoption Metrics
- **Usage**: 50%+ of active users create custom commands
- **Community**: 100+ shared commands in community library
- **Integration**: 5+ community apps integrate slash commands
- **Feedback**: 4.5+ star rating from users

### Business Metrics
- **Differentiation**: Unique feature vs. competitors
- **Retention**: Increased user retention (hypothesis: yes)
- **Ecosystem**: More community modules and apps built
- **Support**: Reduced support tickets (self-service via commands)

## Risk Management

### Technical Risks
- **Context Overflow**: Mitigated by character budget limits
- **Security**: Mitigated by tool restrictions and approval hooks
- **Performance**: Mitigated by lazy loading and caching
- **Compatibility**: Mitigated by strict protocol compliance

### Adoption Risks
- **Discoverability**: Mitigated by good documentation and examples
- **Complexity**: Mitigated by simple starting point and gradual feature addition
- **Quality**: Mitigated by community review process
- **Abandonment**: Mitigated by making it part of foundation

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | 2 weeks | Working integration with amplifier-app-cli |
| Phase 2 | 2 weeks | Bash execution, file references, permissions |
| Phase 3 | 2 weeks | Foundation integration, community library |
| Phase 4 | 2 weeks | Advanced features (composition, versioning) |
| Phase 5 | Ongoing | Optimization, community building |

**Total: 8 weeks to full feature set, with ongoing improvements**

## Immediate Next Steps

1. **Test the module** (blocked on local testing environment)
   - Set up venv: `python3 -m venv .venv`
   - Install deps: `source .venv/bin/activate && pip install -e ".[dev]"`
   - Run tests: `pytest -v`

2. **Create integration branch in amplifier-app-cli**
   - Fork/clone amplifier-app-cli
   - Create feature branch: `feature/slash-commands`
   - Implement CommandProcessor changes

3. **Write integration guide**
   - Document how app developers integrate
   - Provide code examples
   - List common patterns

4. **Create demo video**
   - Show command creation workflow
   - Demonstrate execution
   - Highlight use cases

5. **Get early feedback**
   - Share with amplifier-core maintainers
   - Test with 3-5 early adopters
   - Iterate based on feedback

## Open Questions

1. **Module Hosting**: Should this move to `microsoft/amplifier-module-tool-slash-command` or stay under `robotdad`?
2. **Foundation Integration**: Should slash commands be part of the default foundation bundle or opt-in?
3. **Community Library Governance**: Who reviews and approves community commands?
4. **Pricing/Cost**: How do we handle model costs for frequently-run commands?
5. **Privacy**: What telemetry (if any) is acceptable for command usage?

## Conclusion

The slash command system provides a powerful extensibility mechanism that empowers users to customize their Amplifier experience. By following this phased approach, we can deliver value incrementally while building toward a rich ecosystem of shared commands.

The implementation is complete and ready for integration testing. The forward path focuses on integration with amplifier-app-cli, enhancement with advanced features, and ecosystem adoption through community engagement.

**Repository**: https://github.com/robotdad/amplifier-module-tool-slash-command (private)
**Status**: ✅ Ready for Phase 1 integration
