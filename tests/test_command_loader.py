"""Tests for command loader."""

import pytest
from pathlib import Path
from amplifier_module_tool_slash_command.command_loader import CommandLoader


@pytest.fixture
def loader():
    return CommandLoader()


@pytest.fixture
def temp_commands_dir(tmp_path):
    """Create a temporary commands directory structure."""
    commands_dir = tmp_path / ".amplifier" / "commands"
    commands_dir.mkdir(parents=True)
    return commands_dir


def test_load_single_command(loader, temp_commands_dir):
    """Test loading a single command file."""
    cmd_file = temp_commands_dir / "test.md"
    cmd_file.write_text("""---
description: Test command
---

Test content
""")
    
    result = loader.load_single_command(cmd_file)
    
    assert result.name == "test"
    assert result.metadata.description == "Test command"


def test_discover_project_commands(loader, tmp_path):
    """Test discovering commands from project directory."""
    project_dir = tmp_path / "project"
    commands_dir = project_dir / ".amplifier" / "commands"
    commands_dir.mkdir(parents=True)
    
    # Create test commands
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
    
    commands = loader.discover_commands(project_dir=project_dir, user_dir=tmp_path / "user")
    
    assert len(commands) == 2
    names = {cmd.name for cmd in commands}
    assert names == {"review", "test"}


def test_discover_user_commands(loader, tmp_path):
    """Test discovering commands from user directory."""
    user_dir = tmp_path / "user"
    commands_dir = user_dir / ".amplifier" / "commands"
    commands_dir.mkdir(parents=True)
    
    (commands_dir / "personal.md").write_text("""---
description: Personal command
---
Personal content
""")
    
    commands = loader.discover_commands(project_dir=tmp_path / "project", user_dir=user_dir)
    
    assert len(commands) == 1
    assert commands[0].name == "personal"


def test_project_commands_override_user(loader, tmp_path):
    """Test that project commands take precedence over user commands."""
    project_dir = tmp_path / "project"
    user_dir = tmp_path / "user"
    
    # Create same command in both locations
    project_commands = project_dir / ".amplifier" / "commands"
    project_commands.mkdir(parents=True)
    (project_commands / "shared.md").write_text("""---
description: Project version
---
Project content
""")
    
    user_commands = user_dir / ".amplifier" / "commands"
    user_commands.mkdir(parents=True)
    (user_commands / "shared.md").write_text("""---
description: User version
---
User content
""")
    
    commands = loader.discover_commands(project_dir=project_dir, user_dir=user_dir)
    
    # Should only have one command (project wins)
    assert len(commands) == 1
    assert commands[0].metadata.description == "Project version"


def test_discover_with_namespaces(loader, tmp_path):
    """Test discovering commands in subdirectories (namespaces)."""
    project_dir = tmp_path / "project"
    commands_dir = project_dir / ".amplifier" / "commands"
    
    # Create frontend namespace
    frontend_dir = commands_dir / "frontend"
    frontend_dir.mkdir(parents=True)
    (frontend_dir / "review.md").write_text("""---
description: Frontend review
---
Review frontend
""")
    
    # Create backend namespace
    backend_dir = commands_dir / "backend"
    backend_dir.mkdir(parents=True)
    (backend_dir / "review.md").write_text("""---
description: Backend review
---
Review backend
""")
    
    commands = loader.discover_commands(project_dir=project_dir, user_dir=tmp_path / "user")
    
    assert len(commands) == 2
    namespaces = {cmd.namespace for cmd in commands}
    assert namespaces == {"frontend", "backend"}


def test_skip_invalid_commands(loader, tmp_path, caplog):
    """Test that invalid commands are skipped with warning."""
    project_dir = tmp_path / "project"
    commands_dir = project_dir / ".amplifier" / "commands"
    commands_dir.mkdir(parents=True)
    
    # Valid command
    (commands_dir / "good.md").write_text("""---
description: Good command
---
Content
""")
    
    # Invalid command (missing frontmatter)
    (commands_dir / "bad.md").write_text("No frontmatter here")
    
    commands = loader.discover_commands(project_dir=project_dir, user_dir=tmp_path / "user")
    
    # Should load only the valid one
    assert len(commands) == 1
    assert commands[0].name == "good"
    
    # Should log warning
    assert "Failed to load command" in caplog.text


def test_discover_empty_directory(loader, tmp_path):
    """Test discovering commands from empty directory."""
    commands = loader.discover_commands(
        project_dir=tmp_path / "project",
        user_dir=tmp_path / "user"
    )
    
    assert len(commands) == 0


def test_load_from_directory_recursive(loader, tmp_path):
    """Test recursive directory loading."""
    base_dir = tmp_path / "commands"
    base_dir.mkdir()
    
    # Root level
    (base_dir / "root.md").write_text("""---
description: Root command
---
Root
""")
    
    # Nested level 1
    level1 = base_dir / "level1"
    level1.mkdir()
    (level1 / "nested1.md").write_text("""---
description: Nested 1
---
Nested 1
""")
    
    # Nested level 2
    level2 = level1 / "level2"
    level2.mkdir()
    (level2 / "nested2.md").write_text("""---
description: Nested 2
---
Nested 2
""")
    
    commands = loader._load_from_directory(base_dir, scope="test")
    
    assert len(commands) == 3
    namespaces = {cmd.namespace for cmd in commands}
    assert None in namespaces  # root command
    assert "level1" in namespaces
    assert "level1:level2" in namespaces
