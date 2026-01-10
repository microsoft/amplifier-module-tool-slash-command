"""Extensible slash command system for Amplifier.

This module provides custom slash commands as Markdown files with YAML frontmatter,
enabling users to define project-scoped and user-scoped commands.
"""

from .command_loader import CommandLoader
from .executor import CommandExecutor, ExecutionResult
from .parser import CommandMetadata, CommandParser, ParsedCommand
from .registry import CommandRegistry
from .template_processor import ProcessedTemplate, TemplateProcessor
from .tool import mount

__version__ = "0.1.0"

__all__ = [
    "mount",
    "CommandLoader",
    "CommandParser",
    "CommandMetadata",
    "ParsedCommand",
    "CommandRegistry",
    "CommandExecutor",
    "ExecutionResult",
    "TemplateProcessor",
    "ProcessedTemplate",
]
