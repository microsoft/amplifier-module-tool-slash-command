"""Extensible slash command system for Amplifier.

This module provides custom slash commands as Markdown files with YAML frontmatter,
enabling users to define project-scoped and user-scoped commands.
"""

from .tool import mount

__version__ = "0.1.0"

__all__ = ["mount"]
