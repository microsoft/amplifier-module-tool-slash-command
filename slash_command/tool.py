"""Amplifier tool implementation for slash command execution."""

import logging
from pathlib import Path
from typing import Any

from .executor import CommandExecutor
from .registry import CommandRegistry

logger = logging.getLogger(__name__)


async def mount(coordinator: Any, config: dict[str, Any]) -> Any:
    """Mount the slash_command tool into Amplifier coordinator.

    This is the entry point called by Amplifier when loading the module.

    Args:
        coordinator: Amplifier coordinator instance
        config: Module configuration

    Returns:
        Cleanup function
    """
    logger.info("Mounting tool-slash-command module")

    # Initialize registry
    registry = CommandRegistry(coordinator)

    # Get optional config for command directories
    project_dir = config.get("project_dir")
    user_dir = config.get("user_dir")

    if project_dir:
        project_dir = Path(project_dir)
    if user_dir:
        user_dir = Path(user_dir)

    # Discover and load commands
    try:
        count = registry.discover_and_load(project_dir=project_dir, user_dir=user_dir)
        logger.info(f"Loaded {count} custom command(s)")
    except Exception as e:
        logger.error(f"Failed to load commands: {e}")
        # Continue mounting even if command loading fails

    # Create executor
    executor = CommandExecutor(registry, coordinator)

    # Define the slash_command tool
    async def slash_command_tool(command: str, args: str = "") -> str:
        """Execute a custom slash command.

        Args:
            command: Command name (without leading /)
            args: Optional command arguments

        Returns:
            Substituted prompt ready for execution

        Raises:
            ValueError: If command not found or invalid
        """
        # Strip leading / if present
        command = command.lstrip("/")

        # Execute command (returns substituted template)
        prompt = await executor.execute(command, args)

        return prompt

    # Register the tool
    tools = coordinator.get("tools")
    if tools is not None:
        tools["slash_command"] = slash_command_tool

        # Set tool description for help output
        slash_command_tool.description = (
            "Execute a custom slash command defined in .amplifier/commands/ or ~/.amplifier/commands/\n\n"
            "Parameters:\n"
            "  command: Command name (without leading /)\n"
            "  args: Optional command arguments\n\n"
            "Returns the substituted prompt ready for execution."
        )

        logger.info("Registered tool: slash_command")
    else:
        logger.warning("Failed to register slash_command tool - tools registry not available")

    # Register registry as a capability for access by other components
    coordinator.register_capability("slash_command_registry", registry)
    coordinator.register_capability("slash_command_executor", executor)

    logger.info("tool-slash-command module mounted successfully")

    # Return cleanup function
    async def cleanup():
        """Cleanup function called on session end."""
        logger.info("Cleaning up tool-slash-command module")
        # Remove from tools registry
        tools = coordinator.get("tools")
        if tools is not None and "slash_command" in tools:
            del tools["slash_command"]

        # Unregister capabilities
        coordinator.unregister_capability("slash_command_registry")
        coordinator.unregister_capability("slash_command_executor")

    return cleanup
