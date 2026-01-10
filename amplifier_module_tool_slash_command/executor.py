"""Execute custom slash commands with template substitution."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .parser import CommandParser, ParsedCommand
from .registry import CommandRegistry
from .template_processor import TemplateProcessor

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of command execution."""

    prompt: str
    warnings: list[str] | None = None
    bash_commands_executed: int = 0
    files_included: int = 0
    requires_approval: bool = False
    approval_message: str | None = None


class CommandExecutor:
    """Executes custom slash commands."""

    def __init__(
        self,
        registry: CommandRegistry,
        coordinator: Any,
        working_dir: Path | None = None,
    ):
        """Initialize executor.

        Args:
            registry: CommandRegistry instance
            coordinator: Amplifier coordinator
            working_dir: Working directory for file refs and bash
        """
        self.registry = registry
        self.coordinator = coordinator
        self.parser = CommandParser()
        self.working_dir = working_dir or Path.cwd()
        self.template_processor = TemplateProcessor(
            coordinator=coordinator,
            working_dir=self.working_dir,
        )

    async def execute(
        self,
        command_name: str,
        args: str = "",
        namespace: str | None = None,
        process_advanced: bool = True,
    ) -> str:
        """Execute a custom command.

        Args:
            command_name: Command name (without leading /)
            args: Command arguments
            namespace: Optional namespace for disambiguation
            process_advanced: Whether to process bash/file refs (Phase 2)

        Returns:
            Command output (the substituted prompt)

        Raises:
            ValueError: If command not found or execution fails
        """
        result = await self.execute_full(command_name, args, namespace, process_advanced)
        return result.prompt

    async def execute_full(
        self,
        command_name: str,
        args: str = "",
        namespace: str | None = None,
        process_advanced: bool = True,
    ) -> ExecutionResult:
        """Execute a custom command with full result details.

        Args:
            command_name: Command name (without leading /)
            args: Command arguments
            namespace: Optional namespace for disambiguation
            process_advanced: Whether to process bash/file refs

        Returns:
            ExecutionResult with prompt and metadata

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

        # Step 1: Substitute variables in template
        try:
            substituted = self.parser.substitute_variables(command.template, args)
        except Exception as e:
            raise ValueError(f"Template substitution failed: {e}") from e

        # Step 2: Process advanced features (bash, file refs) if enabled
        warnings: list[str] = []
        bash_count = 0
        files_count = 0

        if process_advanced:
            processed = await self.template_processor.process(
                substituted,
                allowed_tools=command.metadata.allowed_tools,
                include_files=True,
            )
            substituted = processed.content
            bash_count = processed.bash_commands_executed
            files_count = processed.files_included
            if processed.warnings:
                warnings.extend(processed.warnings)

        # Step 3: Validate tool restrictions if specified
        if command.metadata.allowed_tools:
            self._validate_tool_restrictions(command)

        # Step 4: Check approval requirements
        requires_approval = getattr(command.metadata, "requires_approval", False)
        approval_message = getattr(command.metadata, "approval_message", None)

        # Step 5: Apply character budget if specified
        if command.metadata.max_chars and len(substituted) > command.metadata.max_chars:
            original_len = len(substituted)
            substituted = self._apply_char_budget(substituted, command.metadata.max_chars)
            warnings.append(
                f"Content truncated from {original_len} to {len(substituted)} chars "
                f"(max-chars: {command.metadata.max_chars})"
            )

        logger.debug(
            f"Substituted prompt ({len(substituted)} chars, "
            f"{bash_count} bash, {files_count} files)"
        )

        return ExecutionResult(
            prompt=substituted,
            warnings=warnings if warnings else None,
            bash_commands_executed=bash_count,
            files_included=files_count,
            requires_approval=requires_approval,
            approval_message=approval_message,
        )

    def _apply_char_budget(self, content: str, max_chars: int) -> str:
        """Truncate content to fit character budget.

        Tries to truncate at a sensible boundary (paragraph, sentence).

        Args:
            content: Content to truncate
            max_chars: Maximum characters allowed

        Returns:
            Truncated content with indicator
        """
        if len(content) <= max_chars:
            return content

        # Reserve space for truncation indicator
        truncation_msg = "\n\n[...truncated due to character limit...]"
        available = max_chars - len(truncation_msg)

        if available <= 0:
            return content[:max_chars]

        truncated = content[:available]

        # Try to find a good break point (paragraph > sentence > word)
        for sep in ["\n\n", "\n", ". ", " "]:
            last_sep = truncated.rfind(sep)
            if last_sep > available * 0.7:  # Don't cut too much
                truncated = truncated[:last_sep + len(sep)]
                break

        return truncated.rstrip() + truncation_msg

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
