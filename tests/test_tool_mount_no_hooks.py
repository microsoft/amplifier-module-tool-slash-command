"""Tests verifying tool-slash-command mount registers no hooks."""

import pytest
from typing import Any


class MockHooks:
    """Mock hooks system."""

    def __init__(self):
        self.registered_hooks: list[dict] = []

    def register(self, event: str, handler, priority: int = 10, name: str | None = None):
        self.registered_hooks.append(
            {"event": event, "handler": handler, "priority": priority, "name": name}
        )


class MockCoordinator:
    """Mock coordinator."""

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
async def test_mount_registers_no_hooks():
    """After revert, mount() should register no hooks at all."""
    from amplifier_module_tool_slash_command.tool import mount

    coordinator = MockCoordinator()
    await mount(coordinator, {})

    assert len(coordinator.hooks.registered_hooks) == 0, (
        f"Expected no hooks registered, but found: {coordinator.hooks.registered_hooks}"
    )
