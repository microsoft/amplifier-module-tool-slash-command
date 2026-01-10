"""Parse command files with YAML frontmatter and template substitution."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CommandMetadata:
    """Metadata extracted from command frontmatter."""

    description: str
    allowed_tools: list[str] | None = None
    argument_hint: str | None = None
    model: str | None = None
    disable_model_invocation: bool = False
    # Phase 2: Approval gates
    requires_approval: bool = False
    approval_message: str | None = None
    # Phase 2: Character budget
    max_chars: int | None = None


@dataclass
class ParsedCommand:
    """Parsed command with metadata and template."""

    name: str
    metadata: CommandMetadata
    template: str
    source_file: Path
    namespace: str | None = None


class CommandParser:
    """Parser for command Markdown files with frontmatter."""

    # Regex patterns
    FRONTMATTER_PATTERN = re.compile(
        r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL | re.MULTILINE
    )
    VARIABLE_PATTERN = re.compile(r"\{\{(\$\d+|\$ARGUMENTS)\s+or\s+\"([^\"]*)\"\}\}")
    SIMPLE_VARIABLE_PATTERN = re.compile(r"\$(\d+|\bARGUMENTS\b)")

    def parse_file(self, file_path: Path, namespace: str | None = None) -> ParsedCommand:
        """Parse a command file.

        Args:
            file_path: Path to the .md command file
            namespace: Optional namespace (from subdirectory)

        Returns:
            ParsedCommand with metadata and template

        Raises:
            ValueError: If file is malformed
        """
        content = file_path.read_text(encoding="utf-8")

        # Extract frontmatter and body
        match = self.FRONTMATTER_PATTERN.match(content)
        if not match:
            raise ValueError(f"Command file missing frontmatter: {file_path}")

        frontmatter_str, template = match.groups()

        # Parse YAML frontmatter
        try:
            frontmatter_data = yaml.safe_load(frontmatter_str) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML frontmatter in {file_path}: {e}") from e

        # Extract metadata
        metadata = self._parse_metadata(frontmatter_data, file_path)

        # Command name from filename
        name = file_path.stem

        return ParsedCommand(
            name=name,
            metadata=metadata,
            template=template.strip(),
            source_file=file_path,
            namespace=namespace,
        )

    def _parse_metadata(
        self, frontmatter: dict[str, Any], file_path: Path
    ) -> CommandMetadata:
        """Parse and validate frontmatter metadata.

        Args:
            frontmatter: Parsed YAML data
            file_path: Source file (for error messages)

        Returns:
            CommandMetadata

        Raises:
            ValueError: If required fields missing or invalid
        """
        # Description is required
        description = frontmatter.get("description")
        if not description:
            raise ValueError(f"Command missing 'description' in frontmatter: {file_path}")

        # Optional fields
        allowed_tools = frontmatter.get("allowed-tools") or frontmatter.get("allowed_tools")
        if allowed_tools and not isinstance(allowed_tools, list):
            raise ValueError(f"'allowed-tools' must be a list in {file_path}")

        argument_hint = frontmatter.get("argument-hint") or frontmatter.get("argument_hint")
        model = frontmatter.get("model")
        disable_model_invocation = frontmatter.get("disable-model-invocation", False) or frontmatter.get("disable_model_invocation", False)

        # Phase 2: Approval gates
        requires_approval = frontmatter.get("requires-approval", False) or frontmatter.get("requires_approval", False)
        approval_message = frontmatter.get("approval-message") or frontmatter.get("approval_message")

        # Phase 2: Character budget
        max_chars = frontmatter.get("max-chars") or frontmatter.get("max_chars")
        if max_chars is not None:
            try:
                max_chars = int(max_chars)
            except (ValueError, TypeError):
                raise ValueError(f"'max-chars' must be an integer in {file_path}")

        return CommandMetadata(
            description=description,
            allowed_tools=allowed_tools,
            argument_hint=argument_hint,
            model=model,
            disable_model_invocation=bool(disable_model_invocation),
            requires_approval=bool(requires_approval),
            approval_message=approval_message,
            max_chars=max_chars,
        )

    def substitute_variables(self, template: str, args: str) -> str:
        """Substitute template variables with arguments.

        Supports:
        - $ARGUMENTS - All arguments as string
        - $1, $2, $3 - Positional arguments
        - {{$1 or "default"}} - Variable with fallback

        Args:
            template: Command template string
            args: Space-separated arguments

        Returns:
            Template with variables substituted
        """
        # Split arguments (simple space-split for now)
        arg_list = args.split() if args else []

        # First pass: Handle {{$N or "default"}} syntax
        def replace_with_fallback(match):
            var_name = match.group(1)
            default = match.group(2)

            if var_name == "$ARGUMENTS":
                return args if args else default

            # Extract position number
            pos_match = re.match(r"\$(\d+)", var_name)
            if pos_match:
                pos = int(pos_match.group(1))
                # 1-indexed positions
                if pos > 0 and pos <= len(arg_list):
                    return arg_list[pos - 1]
                return default

            return match.group(0)  # Leave unchanged if unrecognized

        result = self.VARIABLE_PATTERN.sub(replace_with_fallback, template)

        # Second pass: Handle simple $ARGUMENTS and $N
        def replace_simple(match):
            var_name = match.group(1)

            if var_name == "ARGUMENTS":
                return args

            # Positional argument
            try:
                pos = int(var_name)
                if pos > 0 and pos <= len(arg_list):
                    return arg_list[pos - 1]
            except ValueError:
                pass

            return match.group(0)  # Leave unchanged

        result = self.SIMPLE_VARIABLE_PATTERN.sub(replace_simple, result)

        return result
