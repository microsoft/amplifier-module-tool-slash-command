"""Tests for command registry."""

import pytest
from pathlib import Path
from unittest.mock import Mock
from slash_command.registry import CommandRegistry


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = Mock()
    coordinator.register_capability = Mock()
    coordinator.unregister_capability = Mock()
    coordinator.get_capability = Mock(return_value=None)
    return coordinator


@pytest.fixture
def registry(mock_coordinator):
    """Create a registry with mock coordinator."""
    return CommandRegistry(mock_coordinator)


@pytest.fixture
def sample_commands_dir(tmp_path):
    """Create sample commands for testing."""
    commands_dir = tmp_path / ".amplifier" / "commands"
    commands_dir.mkdir(parents=True)
    
    (commands_dir / "review.md").write_text("""---
description: Review code
---
Review this code
""")
    
    (commands_dir / "test.md").write_text("""---
description: Generate tests
---
Generate tests
""")
    
    # Create namespace
    frontend_dir = commands_dir / "frontend"
    frontend_dir.mkdir()
    (frontend_dir / "build.md").write_text("""---
description: Build frontend
---
Build frontend
""")
    
    return tmp_path


def test_discover_and_load(registry, sample_commands_dir):
    """Test discovering and loading commands."""
    count = registry.discover_and_load(project_dir=sample_commands_dir)
    
    assert count == 3
    assert registry.is_loaded()


def test_get_command_by_name(registry, sample_commands_dir):
    """Test retrieving a command by name."""
    registry.discover_and_load(project_dir=sample_commands_dir)
    
    cmd = registry.get_command("review")
    
    assert cmd is not None
    assert cmd.name == "review"
    assert cmd.metadata.description == "Review code"


def test_get_command_with_namespace(registry, sample_commands_dir):
    """Test retrieving a command by name and namespace."""
    registry.discover_and_load(project_dir=sample_commands_dir)
    
    cmd = registry.get_command("build", namespace="frontend")
    
    assert cmd is not None
    assert cmd.name == "build"
    assert cmd.namespace == "frontend"


def test_get_nonexistent_command(registry, sample_commands_dir):
    """Test retrieving a command that doesn't exist."""
    registry.discover_and_load(project_dir=sample_commands_dir)
    
    cmd = registry.get_command("nonexistent")
    
    assert cmd is None


def test_list_commands(registry, sample_commands_dir):
    """Test listing all commands."""
    registry.discover_and_load(project_dir=sample_commands_dir)
    
    commands = registry.list_commands()
    
    assert len(commands) == 3
    names = {cmd.name for cmd in commands}
    assert names == {"review", "test", "build"}


def test_get_command_names(registry, sample_commands_dir):
    """Test getting formatted command names."""
    registry.discover_and_load(project_dir=sample_commands_dir)
    
    names = registry.get_command_names()
    
    assert len(names) == 3
    # Names should be sorted and include scope
    assert all("project" in name or "user" in name for name in names)


def test_get_command_dict(registry, sample_commands_dir):
    """Test getting commands as dict for CommandProcessor."""
    registry.discover_and_load(project_dir=sample_commands_dir)
    
    cmd_dict = registry.get_command_dict()
    
    assert "/review" in cmd_dict
    assert "/test" in cmd_dict
    assert "/build" in cmd_dict
    
    # Check structure
    review_cmd = cmd_dict["/review"]
    assert review_cmd["action"] == "execute_custom_command"
    assert "Review code" in review_cmd["description"]
    assert review_cmd["metadata"]["name"] == "review"


def test_reload_commands(registry, sample_commands_dir):
    """Test reloading commands."""
    # Load initially
    count1 = registry.discover_and_load(project_dir=sample_commands_dir)
    assert count1 == 3
    
    # Add a new command
    new_cmd = sample_commands_dir / ".amplifier" / "commands" / "new.md"
    new_cmd.write_text("""---
description: New command
---
New content
""")
    
    # Reload
    count2 = registry.reload(project_dir=sample_commands_dir)
    assert count2 == 4
    
    # Verify new command is loaded
    cmd = registry.get_command("new")
    assert cmd is not None


def test_make_key(registry):
    """Test key generation for command lookup."""
    # No namespace
    key1 = registry._make_key("test", None)
    assert key1 == "test"
    
    # With namespace
    key2 = registry._make_key("test", "frontend")
    assert key2 == "frontend:test"


def test_is_loaded_flag(registry, sample_commands_dir):
    """Test is_loaded flag tracking."""
    assert not registry.is_loaded()
    
    registry.discover_and_load(project_dir=sample_commands_dir)
    assert registry.is_loaded()
