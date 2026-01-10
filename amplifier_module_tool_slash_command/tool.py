"""Amplifier tool implementation for slash command execution."""

import logging
from pathlib import Path
from typing import Any

from .executor import CommandExecutor
from .registry import CommandRegistry

logger = logging.getLogger(__name__)


class SlashCommandTool:
    """Tool for executing custom slash commands.

    Implements the Amplifier Tool protocol with name, description, and execute().
    """

    def __init__(self, registry: CommandRegistry, executor: CommandExecutor):
        """Initialize the slash command tool.

        Args:
            registry: Command registry for discovering commands
            executor: Command executor for running commands
        """
        self._registry = registry
        self._executor = executor

    @property
    def name(self) -> str:
        """Tool name for invocation."""
        return "slash_command"

    @property
    def description(self) -> str:
        """Human-readable tool description."""
        return (
            "Execute a custom slash command defined in .amplifier/commands/ or ~/.amplifier/commands/\n\n"
            "Parameters:\n"
            "  command: Command name (without leading /)\n"
            "  args: Optional command arguments\n\n"
            "Returns the substituted prompt ready for execution."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        """Return JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Command name (without leading /)",
                },
                "args": {
                    "type": "string",
                    "description": "Optional command arguments",
                    "default": "",
                },
            },
            "required": ["command"],
        }

    @property
    def registry(self) -> CommandRegistry:
        """Access to command registry for CLI integration."""
        return self._registry

    @property
    def executor(self) -> CommandExecutor:
        """Access to command executor for CLI integration."""
        return self._executor

    async def execute(self, input: dict[str, Any]) -> Any:
        """Execute a custom slash command.

        Args:
            input: Dictionary with 'command' (required) and 'args' (optional)

        Returns:
            ToolResult with the substituted prompt
        """
        # Import here to avoid circular dependency at module level
        from amplifier_core.models import ToolResult  # type: ignore[import-not-found]

        command = input.get("command", "")
        args = input.get("args", "")

        # Strip leading / if present
        command = command.lstrip("/")

        if not command:
            return ToolResult(
                success=False,
                error={"message": "No command specified"},
            )

        try:
            # Execute command (returns substituted template)
            prompt = await self._executor.execute(command, args)
            return ToolResult(success=True, output=prompt)
        except ValueError as e:
            return ToolResult(success=False, error={"message": str(e)})
        except Exception as e:
            logger.exception(f"Error executing slash command '{command}'")
            return ToolResult(success=False, error={"message": f"Execution error: {e}"})


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

    # Create executor and tool
    executor = CommandExecutor(registry, coordinator)
    tool = SlashCommandTool(registry, executor)

    # Register the tool using the class instance
    tools = coordinator.get("tools")
    if tools is not None:
        tools["slash_command"] = tool
        logger.info("Registered tool: slash_command")
    else:
        logger.warning(
            "Failed to register slash_command tool - tools registry not available"
        )

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

        # Note: Capabilities are automatically cleaned up when session ends
        # The coordinator doesn't have unregister_capability method

    return cleanup
