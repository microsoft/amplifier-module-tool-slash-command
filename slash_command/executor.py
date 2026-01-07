"""Execute custom slash commands with template substitution."""

import logging
from typing import Any

from .parser import CommandParser, ParsedCommand
from .registry import CommandRegistry

logger = logging.getLogger(__name__)


class CommandExecutor:
    """Executes custom slash commands."""

    def __init__(self, registry: CommandRegistry, coordinator: Any):
        """Initialize executor.

        Args:
            registry: CommandRegistry instance
            coordinator: Amplifier coordinator
        """
        self.registry = registry
        self.coordinator = coordinator
        self.parser = CommandParser()

    async def execute(
        self, command_name: str, args: str = "", namespace: str | None = None
    ) -> str:
        """Execute a custom command.

        Args:
            command_name: Command name (without leading /)
            args: Command arguments
            namespace: Optional namespace for disambiguation

        Returns:
            Command output (the substituted prompt)

        Raises:
            ValueError: If command not found or execution fails
        """
        # Look up command
        command = self.registry.get_command(command_name, namespace)
        if not command:
            available = self.registry.get_command_names()
            raise ValueError(
                f"Command '/{command_name}' not found. "
                f"Available commands: {', '.join(available)}"
            )

        logger.info(
            f"Executing command: /{command_name} "
            f"(namespace: {namespace or 'none'}, args: {args[:50]}{'...' if len(args) > 50 else ''})"
        )

        # Substitute variables in template
        try:
            substituted = self.parser.substitute_variables(command.template, args)
        except Exception as e:
            raise ValueError(f"Template substitution failed: {e}") from e

        # Validate tool restrictions if specified
        if command.metadata.allowed_tools:
            self._validate_tool_restrictions(command)

        logger.debug(f"Substituted prompt ({len(substituted)} chars)")
        return substituted

    def _validate_tool_restrictions(self, command: ParsedCommand) -> None:
        """Validate that command's tool restrictions are compatible with session.

        This is informational only - actual tool filtering happens at execution time
        through Amplifier's existing tool permission system.

        Args:
            command: Command with allowed_tools metadata

        Note:
            We log warnings but don't block execution. The session's tool permissions
            are the authoritative source.
        """
        if not command.metadata.allowed_tools:
            return

        # Get available tools from coordinator
        tools = self.coordinator.get("tools") or {}
        available_tool_names = set(tools.keys())

        # Check if requested tools are available
        requested_tools = set(command.metadata.allowed_tools)
        missing_tools = requested_tools - available_tool_names

        if missing_tools:
            logger.warning(
                f"Command '/{command.name}' requests tools not available in session: "
                f"{', '.join(missing_tools)}"
            )

    def get_command_info(
        self, command_name: str, namespace: str | None = None
    ) -> dict[str, Any] | None:
        """Get information about a command.

        Args:
            command_name: Command name (without leading /)
            namespace: Optional namespace

        Returns:
            Dict with command info, or None if not found
        """
        command = self.registry.get_command(command_name, namespace)
        if not command:
            return None

        return {
            "name": command.name,
            "namespace": command.namespace,
            "description": command.metadata.description,
            "allowed_tools": command.metadata.allowed_tools,
            "argument_hint": command.metadata.argument_hint,
            "model": command.metadata.model,
            "source_file": str(command.source_file),
            "scope": getattr(command, "scope", "unknown"),
        }
