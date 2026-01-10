"""Tests for command parser."""

import pytest
from pathlib import Path
from amplifier_module_tool_slash_command.parser import CommandParser, CommandMetadata, ParsedCommand


@pytest.fixture
def parser():
    return CommandParser()


@pytest.fixture
def temp_command_file(tmp_path):
    """Create a temporary command file for testing."""
    def _create_file(content: str, filename: str = "test.md") -> Path:
        file_path = tmp_path / filename
        file_path.write_text(content)
        return file_path
    return _create_file


def test_parse_basic_command(parser, temp_command_file):
    """Test parsing a basic command with minimal frontmatter."""
    content = """---
description: Test command
---

This is a test command.
"""
    file_path = temp_command_file(content)
    
    result = parser.parse_file(file_path)
    
    assert result.name == "test"
    assert result.metadata.description == "Test command"
    assert result.template == "This is a test command."
    assert result.namespace is None


def test_parse_command_with_all_fields(parser, temp_command_file):
    """Test parsing a command with all frontmatter fields."""
    content = """---
description: Full test command
allowed-tools: [read_file, grep]
argument-hint: "[file-path] [pattern]"
model: anthropic/claude-sonnet-4.5
---

Search {{$1 or "current file"}} for {{$2 or "pattern"}}.
"""
    file_path = temp_command_file(content)
    
    result = parser.parse_file(file_path, namespace="test-namespace")
    
    assert result.name == "test"
    assert result.metadata.description == "Full test command"
    assert result.metadata.allowed_tools == ["read_file", "grep"]
    assert result.metadata.argument_hint == "[file-path] [pattern]"
    assert result.metadata.model == "anthropic/claude-sonnet-4.5"
    assert result.namespace == "test-namespace"


def test_parse_missing_frontmatter(parser, temp_command_file):
    """Test that missing frontmatter raises ValueError."""
    content = "This is just content without frontmatter."
    file_path = temp_command_file(content)
    
    with pytest.raises(ValueError, match="missing frontmatter"):
        parser.parse_file(file_path)


def test_parse_missing_description(parser, temp_command_file):
    """Test that missing description raises ValueError."""
    content = """---
allowed-tools: [read_file]
---

Content here.
"""
    file_path = temp_command_file(content)
    
    with pytest.raises(ValueError, match="missing 'description'"):
        parser.parse_file(file_path)


def test_substitute_arguments_simple(parser):
    """Test simple $ARGUMENTS substitution."""
    template = "Execute command: $ARGUMENTS"
    result = parser.substitute_variables(template, "arg1 arg2 arg3")
    
    assert result == "Execute command: arg1 arg2 arg3"


def test_substitute_positional_args(parser):
    """Test $1, $2, $3 substitution."""
    template = "First: $1, Second: $2, Third: $3"
    result = parser.substitute_variables(template, "one two three")
    
    assert result == "First: one, Second: two, Third: three"


def test_substitute_with_fallback(parser):
    """Test {{$N or "default"}} syntax."""
    template = "File: {{$1 or \"current file\"}}, Pattern: {{$2 or \"default\"}}"
    
    # With both arguments
    result = parser.substitute_variables(template, "test.py mypattern")
    assert result == "File: test.py, Pattern: mypattern"
    
    # With one argument
    result = parser.substitute_variables(template, "test.py")
    assert result == "File: test.py, Pattern: default"
    
    # With no arguments
    result = parser.substitute_variables(template, "")
    assert result == "File: current file, Pattern: default"


def test_substitute_arguments_fallback(parser):
    """Test {{$ARGUMENTS or "default"}} syntax."""
    template = "Search for: {{$ARGUMENTS or \"nothing specified\"}}"
    
    # With arguments
    result = parser.substitute_variables(template, "test pattern")
    assert result == "Search for: test pattern"
    
    # Without arguments
    result = parser.substitute_variables(template, "")
    assert result == "Search for: nothing specified"


def test_substitute_mixed_syntax(parser):
    """Test mixing simple and fallback syntax."""
    template = "Command: $1 on {{$2 or \"all files\"}} with $ARGUMENTS"
    result = parser.substitute_variables(template, "search test.py searchterm")
    
    assert result == "Command: search on test.py with search test.py searchterm"


def test_substitute_empty_args(parser):
    """Test substitution with empty arguments."""
    template = "Args: $ARGUMENTS, First: $1"
    result = parser.substitute_variables(template, "")
    
    assert result == "Args: , First: $1"  # Unmatched variables stay as-is


def test_parse_invalid_yaml(parser, temp_command_file):
    """Test that invalid YAML raises ValueError."""
    content = """---
description: Test
  invalid: yaml: structure
---

Content
"""
    file_path = temp_command_file(content)
    
    with pytest.raises(ValueError, match="Invalid YAML"):
        parser.parse_file(file_path)
