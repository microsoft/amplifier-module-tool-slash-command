"""Tests for skill:command_registered hook listener in tool-slash-command."""

import pytest
from pathlib import Path
from typing import Any


class MockHooks:
    """Mock hooks system for testing."""

    def __init__(self):
        self.registered_hooks: list[dict] = []
        self.emitted_events: list[tuple] = []

    def register(
        self, event: str, handler, priority: int = 10, name: str | None = None
    ):
        self.registered_hooks.append(
            {"event": event, "handler": handler, "priority": priority, "name": name}
        )

    async def emit(self, event_name: str, data: Any):
        self.emitted_events.append((event_name, data))
        # Also invoke registered handlers for the event
        for hook in self.registered_hooks:
            if hook["event"] == event_name:
                await hook["handler"](event_name, data)


class MockCoordinator:
    """Mock coordinator for testing."""

    def __init__(self):
        self.capabilities: dict = {}
        self._registry: dict = {}
        self.hooks = MockHooks()
        self.config: dict = {}

    def register_capability(self, name: str, value: Any):
        self.capabilities[name] = value

    def get_capability(self, name: str) -> Any:
        return self.capabilities.get(name)

    def get(self, key: str) -> Any:
        return self._registry.get(key)


@pytest.mark.asyncio
async def test_mount_registers_hook_for_skill_command_registered():
    """mount() registers a hook listener for skill:command_registered event."""
    from amplifier_module_tool_slash_command.tool import mount

    coordinator = MockCoordinator()
    await mount(coordinator, {})

    # Check that a hook was registered for skill:command_registered
    registered = coordinator.hooks.registered_hooks
    skill_hooks = [h for h in registered if h["event"] == "skill:command_registered"]
    assert len(skill_hooks) == 1
    assert skill_hooks[0]["priority"] == 50


@pytest.mark.asyncio
async def test_skill_command_registered_hook_registers_command():
    """skill:command_registered event registers skill as slash command."""
    from amplifier_module_tool_slash_command.tool import mount

    coordinator = MockCoordinator()
    await mount(coordinator, {})

    # Get the registry
    registry = coordinator.get_capability("slash_command_registry")
    assert registry is not None

    # Emit a skill:command_registered event.
    # "context" is included to mirror the real event shape even though
    # the handler does not use it.
    await coordinator.hooks.emit(
        "skill:command_registered",
        {
            "skill_name": "my-skill",
            "description": "A test skill",
            "disable_model_invocation": False,
            "context": None,
        },
    )

    # The skill should now be registered as a command
    cmd = registry.get_command("my-skill")
    assert cmd is not None
    assert cmd.name == "my-skill"
    assert cmd.metadata.description == "A test skill"


@pytest.mark.asyncio
async def test_file_based_command_takes_precedence_over_skill(tmp_path: Path):
    """File-based commands take precedence: skill command skipped if file command exists."""
    from amplifier_module_tool_slash_command.tool import mount
    from amplifier_module_tool_slash_command.parser import (
        CommandMetadata,
        ParsedCommand,
    )

    coordinator = MockCoordinator()
    await mount(coordinator, {})

    registry = coordinator.get_capability("slash_command_registry")
    assert registry is not None

    # Pre-register a file-based command with the same name
    file_metadata = CommandMetadata(description="File-based command description")
    file_cmd = ParsedCommand(
        name="existing-skill",
        metadata=file_metadata,
        template="file template",
        source_file=Path("/some/dir/existing-skill.md"),
        namespace=None,
    )
    registry.commands["existing-skill"] = file_cmd

    # Emit skill:command_registered for the same name
    await coordinator.hooks.emit(
        "skill:command_registered",
        {
            "skill_name": "existing-skill",
            "description": "Skill description (should be ignored)",
            "disable_model_invocation": False,
            "context": None,
        },
    )

    # File-based command should still be there, not overwritten
    cmd = registry.get_command("existing-skill")
    assert cmd is not None
    assert cmd.metadata.description == "File-based command description"
    assert str(cmd.source_file) == "/some/dir/existing-skill.md"


@pytest.mark.asyncio
async def test_skill_command_registered_with_disable_model_invocation():
    """Skill command registered with disable_model_invocation=True is preserved."""
    from amplifier_module_tool_slash_command.tool import mount

    coordinator = MockCoordinator()
    await mount(coordinator, {})

    registry = coordinator.get_capability("slash_command_registry")

    await coordinator.hooks.emit(
        "skill:command_registered",
        {
            "skill_name": "internal-skill",
            "description": "An internal skill",
            "disable_model_invocation": True,
            "context": None,
        },
    )

    cmd = registry.get_command("internal-skill")
    assert cmd is not None
    assert cmd.metadata.disable_model_invocation is True


@pytest.mark.asyncio
async def test_skill_command_registered_missing_skill_name_does_nothing():
    """skill:command_registered with missing skill_name does not crash."""
    from amplifier_module_tool_slash_command.tool import mount

    coordinator = MockCoordinator()
    await mount(coordinator, {})

    registry = coordinator.get_capability("slash_command_registry")
    initial_count = len(registry.commands)

    # Emit event with no skill_name
    await coordinator.hooks.emit(
        "skill:command_registered",
        {
            "description": "Missing skill name",
            "disable_model_invocation": False,
            "context": None,
        },
    )

    # Registry should not have changed
    assert len(registry.commands) == initial_count
