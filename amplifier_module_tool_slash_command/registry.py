"""Command registry for managing loaded commands."""

import logging
from pathlib import Path
from typing import Any

from .command_loader import CommandLoader
from .parser import ParsedCommand

logger = logging.getLogger(__name__)


class CommandRegistry:
    """Registry for custom slash commands."""

    def __init__(self, coordinator: Any):
        """Initialize registry.

        Args:
            coordinator: Amplifier coordinator instance
        """
        self.coordinator = coordinator
        self.loader = CommandLoader()
        self.commands: dict[str, ParsedCommand] = {}
        self._loaded = False

    def discover_and_load(
        self,
        project_dir: Path | None = None,
        user_dir: Path | None = None,
        command_urls: list[str] | None = None,
    ) -> int:
        """Discover and load all commands from standard locations and git URLs.

        Priority order (highest to lowest):
        1. Project commands (.amplifier/commands/)
        2. User commands (~/.amplifier/commands/)
        3. Git URL commands (declared in bundle config)

        Args:
            project_dir: Project root (uses cwd if None)
            user_dir: User home (uses Path.home() if None)
            command_urls: List of git URLs to fetch commands from

        Returns:
            Number of commands loaded
        """
        # Track seen commands for precedence
        seen_commands: set[tuple[str, str | None]] = set()

        # Load project and user commands first (higher precedence)
        commands = self.loader.discover_commands(project_dir, user_dir)

        # Store in registry and track seen
        self.commands.clear()
        for cmd in commands:
            key = self._make_key(cmd.name, cmd.namespace)
            self.commands[key] = cmd
            seen_commands.add((cmd.name, cmd.namespace))

        # Load git URL commands (lower precedence)
        if command_urls:
            git_commands = self.loader.load_from_git_urls(command_urls, seen_commands)
            for cmd in git_commands:
                key = self._make_key(cmd.name, cmd.namespace)
                self.commands[key] = cmd

        self._loaded = True
        logger.info(f"Command registry loaded {len(self.commands)} command(s)")
        return len(self.commands)

    def reload(
        self,
        project_dir: Path | None = None,
        user_dir: Path | None = None,
        command_urls: list[str] | None = None,
    ) -> int:
        """Reload all commands from filesystem and git URLs.

        Useful for development when commands are modified without restarting session.

        Args:
            project_dir: Project root (uses cwd if None)
            user_dir: User home (uses Path.home() if None)
            command_urls: List of git URLs to fetch commands from

        Returns:
            Number of commands loaded
        """
        logger.info("Reloading command registry...")
        return self.discover_and_load(project_dir, user_dir, command_urls)

    def get_command(
        self, name: str, namespace: str | None = None
    ) -> ParsedCommand | None:
        """Get a command by name and optional namespace.

        Args:
            name: Command name (without leading /)
            namespace: Optional namespace

        Returns:
            ParsedCommand if found, None otherwise
        """
        key = self._make_key(name, namespace)
        return self.commands.get(key)

    def list_commands(self) -> list[ParsedCommand]:
        """List all registered commands.

        Returns:
            List of ParsedCommand instances
        """
        return list(self.commands.values())

    def get_command_names(self) -> list[str]:
        """Get list of command names for help display.

        Returns:
            List of command names (with namespaces if present)
        """
        names = []
        for cmd in self.commands.values():
            if cmd.namespace:
                names.append(
                    f"{cmd.name} ({getattr(cmd, 'scope', 'user')}:{cmd.namespace})"
                )
            else:
                names.append(f"{cmd.name} ({getattr(cmd, 'scope', 'user')})")
        return sorted(names)

    def get_command_dict(self) -> dict[str, dict[str, Any]]:
        """Get commands formatted for CommandProcessor registration.

        Returns:
            Dict mapping command names to command info dicts with:
            - action: "execute_custom_command"
            - description: Command description
            - metadata: Full command metadata
        """
        result = {}
        for cmd in self.commands.values():
            # Create unique command name
            cmd_name = f"/{cmd.name}"

            # Format description with namespace
            desc = cmd.metadata.description
            if cmd.namespace:
                desc = f"{desc} ({getattr(cmd, 'scope', 'user')}:{cmd.namespace})"
            else:
                desc = f"{desc} ({getattr(cmd, 'scope', 'user')})"

            result[cmd_name] = {
                "action": "execute_custom_command",
                "description": desc,
                "metadata": {
                    "name": cmd.name,
                    "namespace": cmd.namespace,
                    "allowed_tools": cmd.metadata.allowed_tools,
                    "argument_hint": cmd.metadata.argument_hint,
                    "model": cmd.metadata.model,
                },
            }

        return result

    def _make_key(self, name: str, namespace: str | None) -> str:
        """Create registry key from name and namespace.

        Args:
            name: Command name
            namespace: Optional namespace

        Returns:
            Registry key string
        """
        if namespace:
            return f"{namespace}:{name}"
        return name

    def is_loaded(self) -> bool:
        """Check if commands have been loaded.

        Returns:
            True if discover_and_load() has been called
        """
        return self._loaded
