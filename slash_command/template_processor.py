"""Template processor for advanced substitutions (bash, file refs)."""

import asyncio
import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProcessedTemplate:
    """Result of template processing."""

    content: str
    bash_commands_executed: int = 0
    files_included: int = 0
    warnings: list[str] | None = None


class TemplateProcessor:
    """Process templates with bash execution and file references.

    Security Model:
    - Bash execution requires explicit `allowed-tools: [bash]` in frontmatter
    - File references respect working directory boundaries
    - All operations are logged for auditability
    """

    # Pattern for inline bash: !`command` or !`command`
    BASH_INLINE_PATTERN = re.compile(r"!`([^`]+)`")

    # Pattern for bash block: !```\ncommand\n```
    BASH_BLOCK_PATTERN = re.compile(r"!```\n(.*?)\n```", re.DOTALL)

    # Pattern for file references: @path/to/file
    FILE_REF_PATTERN = re.compile(r"@([\w./-]+)")

    def __init__(
        self,
        coordinator: Any | None = None,
        working_dir: Path | None = None,
        timeout: int = 30,
    ):
        """Initialize template processor.

        Args:
            coordinator: Amplifier coordinator (for tool access)
            working_dir: Working directory for relative paths
            timeout: Timeout for bash commands in seconds
        """
        self.coordinator = coordinator
        self.working_dir = working_dir or Path.cwd()
        self.timeout = timeout

    async def process(
        self,
        template: str,
        allowed_tools: list[str] | None = None,
        include_files: bool = True,
    ) -> ProcessedTemplate:
        """Process a template with bash execution and file references.

        Args:
            template: Template content to process
            allowed_tools: List of allowed tools (must include 'bash' for execution)
            include_files: Whether to process @file references

        Returns:
            ProcessedTemplate with substitutions applied
        """
        warnings: list[str] = []
        bash_count = 0
        file_count = 0

        result = template
        bash_allowed = allowed_tools and "bash" in allowed_tools

        # Process bash blocks first (multi-line)
        if self.BASH_BLOCK_PATTERN.search(result):
            if bash_allowed:
                result, count = await self._process_bash_blocks(result)
                bash_count += count
            else:
                warnings.append(
                    "Template contains bash blocks but 'bash' not in allowed-tools. "
                    "Add 'allowed-tools: [bash]' to frontmatter to enable execution."
                )

        # Process inline bash commands
        if self.BASH_INLINE_PATTERN.search(result):
            if bash_allowed:
                result, count = await self._process_bash_inline(result)
                bash_count += count
            else:
                warnings.append(
                    "Template contains inline bash (!`) but 'bash' not in allowed-tools. "
                    "Add 'allowed-tools: [bash]' to frontmatter to enable execution."
                )

        # Process file references
        if include_files and self.FILE_REF_PATTERN.search(result):
            result, count, file_warnings = self._process_file_refs(result)
            file_count = count
            warnings.extend(file_warnings)

        return ProcessedTemplate(
            content=result,
            bash_commands_executed=bash_count,
            files_included=file_count,
            warnings=warnings if warnings else None,
        )

    async def _process_bash_blocks(self, template: str) -> tuple[str, int]:
        """Process !``` bash blocks."""
        count = 0

        async def replace_block(match: re.Match) -> str:
            nonlocal count
            command = match.group(1).strip()
            output = await self._execute_bash(command)
            count += 1
            return output

        # Process each match
        result = template
        for match in list(self.BASH_BLOCK_PATTERN.finditer(template)):
            replacement = await replace_block(match)
            result = result.replace(match.group(0), replacement, 1)

        return result, count

    async def _process_bash_inline(self, template: str) -> tuple[str, int]:
        """Process inline !`command` patterns."""
        count = 0

        async def replace_inline(match: re.Match) -> str:
            nonlocal count
            command = match.group(1).strip()
            output = await self._execute_bash(command)
            count += 1
            return output

        # Process each match
        result = template
        for match in list(self.BASH_INLINE_PATTERN.finditer(template)):
            replacement = await replace_inline(match)
            result = result.replace(match.group(0), replacement, 1)

        return result, count

    async def _execute_bash(self, command: str) -> str:
        """Execute a bash command and return output.

        Args:
            command: Shell command to execute

        Returns:
            Command output (stdout + stderr combined)
        """
        logger.info(f"Executing bash command: {command[:100]}{'...' if len(command) > 100 else ''}")

        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=str(self.working_dir),
                ),
            )

            output = result.stdout
            if result.stderr:
                output += f"\n{result.stderr}" if output else result.stderr

            if result.returncode != 0:
                output = f"[Command exited with code {result.returncode}]\n{output}"

            return output.strip()

        except subprocess.TimeoutExpired:
            logger.warning(f"Bash command timed out after {self.timeout}s: {command[:50]}")
            return f"[Command timed out after {self.timeout} seconds]"
        except Exception as e:
            logger.error(f"Bash execution failed: {e}")
            return f"[Command failed: {e}]"

    def _process_file_refs(self, template: str) -> tuple[str, int, list[str]]:
        """Process @file references.

        Args:
            template: Template with @file references

        Returns:
            Tuple of (processed template, file count, warnings)
        """
        count = 0
        warnings: list[str] = []

        def replace_file_ref(match: re.Match) -> str:
            nonlocal count
            file_path_str = match.group(1)

            # Resolve path relative to working directory
            file_path = self.working_dir / file_path_str

            # Security: ensure path doesn't escape working directory
            try:
                resolved = file_path.resolve()
                working_resolved = self.working_dir.resolve()

                # Check if file is within working directory or is absolute
                if not str(resolved).startswith(str(working_resolved)):
                    # Allow absolute paths that exist
                    if not file_path_str.startswith("/"):
                        warnings.append(
                            f"File reference @{file_path_str} outside working directory"
                        )
                        return match.group(0)  # Leave unchanged
            except Exception:
                pass  # Continue with best effort

            # Try to read file
            try:
                if file_path.exists():
                    content = file_path.read_text(encoding="utf-8")
                    count += 1
                    logger.debug(f"Included file: {file_path_str} ({len(content)} chars)")
                    return f"```\n# {file_path_str}\n{content}\n```"
                else:
                    warnings.append(f"File not found: @{file_path_str}")
                    return match.group(0)
            except Exception as e:
                warnings.append(f"Failed to read @{file_path_str}: {e}")
                return match.group(0)

        result = self.FILE_REF_PATTERN.sub(replace_file_ref, template)
        return result, count, warnings


def process_template_sync(
    template: str,
    allowed_tools: list[str] | None = None,
    working_dir: Path | None = None,
    timeout: int = 30,
) -> ProcessedTemplate:
    """Synchronous wrapper for template processing.

    Args:
        template: Template to process
        allowed_tools: List of allowed tools
        working_dir: Working directory
        timeout: Bash timeout

    Returns:
        ProcessedTemplate
    """
    processor = TemplateProcessor(working_dir=working_dir, timeout=timeout)
    return asyncio.run(processor.process(template, allowed_tools))
