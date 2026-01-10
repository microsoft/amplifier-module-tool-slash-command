"""Granular tool permission parsing and validation.

Supports Claude Code-style granular permissions like:
- `bash` - Allow all bash commands
- `Bash(git add:*)` - Allow only 'git add' commands
- `Bash(git status:*)` - Allow only 'git status' commands
"""

import re
from dataclasses import dataclass


@dataclass
class GranularPermission:
    """A parsed granular tool permission.

    Examples:
        - "bash" -> GranularPermission(tool="bash", pattern=None)
        - "Bash(git add:*)" -> GranularPermission(tool="bash", pattern="git add:*")
    """

    tool: str
    pattern: str | None = None

    def allows_command(self, command: str) -> bool:
        """Check if this permission allows a specific command.

        Args:
            command: The bash command to check

        Returns:
            True if this permission allows the command
        """
        if self.tool.lower() != "bash":
            # Non-bash permissions don't apply to bash commands
            return False

        if self.pattern is None:
            # No pattern = allow all commands for this tool
            return True

        # Convert glob pattern to regex
        # "git add:*" means "command starts with 'git add'"
        # The ":*" suffix is the glob wildcard
        pattern_base = self.pattern.rstrip(":*").rstrip("*").rstrip(":")

        # Check if command starts with the pattern
        return command.strip().startswith(pattern_base)


# Regex to parse "Tool(pattern)" syntax
GRANULAR_PATTERN = re.compile(r"^(\w+)(?:\(([^)]+)\))?$")


def parse_permission(spec: str) -> GranularPermission:
    """Parse a permission specification into a GranularPermission.

    Args:
        spec: Permission string like "bash", "Bash(git add:*)", etc.

    Returns:
        GranularPermission with tool and optional pattern

    Raises:
        ValueError: If spec is malformed
    """
    spec = spec.strip()
    if not spec:
        raise ValueError("Empty permission specification")

    match = GRANULAR_PATTERN.match(spec)
    if not match:
        raise ValueError(f"Invalid permission format: {spec}")

    tool = match.group(1).lower()  # Normalize to lowercase
    pattern = match.group(2)  # May be None

    return GranularPermission(tool=tool, pattern=pattern)


def parse_permissions(specs: list[str] | None) -> list[GranularPermission]:
    """Parse a list of permission specifications.

    Args:
        specs: List of permission strings, or None

    Returns:
        List of GranularPermission objects
    """
    if not specs:
        return []

    return [parse_permission(spec) for spec in specs]


def is_tool_allowed(tool_name: str, permissions: list[GranularPermission]) -> bool:
    """Check if a tool is allowed by any permission.

    This is a simple check - just whether the tool appears in permissions.
    For bash, use is_bash_command_allowed() for granular checking.

    Args:
        tool_name: Name of the tool (e.g., "bash", "edit")
        permissions: List of parsed permissions

    Returns:
        True if tool is allowed
    """
    tool_lower = tool_name.lower()
    return any(p.tool == tool_lower for p in permissions)


def is_bash_command_allowed(
    command: str, permissions: list[GranularPermission]
) -> tuple[bool, str | None]:
    """Check if a specific bash command is allowed.

    Args:
        command: The bash command to execute
        permissions: List of parsed permissions

    Returns:
        Tuple of (allowed: bool, reason: str | None)
        - If allowed, reason is None
        - If not allowed, reason explains why
    """
    # Find all bash permissions
    bash_permissions = [p for p in permissions if p.tool == "bash"]

    if not bash_permissions:
        return False, "bash not in allowed-tools"

    # Check if any permission allows this command
    for perm in bash_permissions:
        if perm.allows_command(command):
            return True, None

    # No permission matched - build helpful error message
    allowed_patterns = [p.pattern for p in bash_permissions if p.pattern]
    if allowed_patterns:
        patterns_str = ", ".join(f"'{p}'" for p in allowed_patterns)
        return False, f"Command does not match allowed patterns: {patterns_str}"

    # This shouldn't happen (if we have bash perms with no patterns, all should be allowed)
    return False, "No matching permission found"


def get_bash_permissions_summary(permissions: list[GranularPermission]) -> str:
    """Get a human-readable summary of bash permissions.

    Args:
        permissions: List of parsed permissions

    Returns:
        Summary string like "all bash commands" or "git add:*, git status:*"
    """
    bash_permissions = [p for p in permissions if p.tool == "bash"]

    if not bash_permissions:
        return "no bash commands allowed"

    patterns = [p.pattern for p in bash_permissions if p.pattern]
    if not patterns:
        return "all bash commands"

    return ", ".join(patterns)
