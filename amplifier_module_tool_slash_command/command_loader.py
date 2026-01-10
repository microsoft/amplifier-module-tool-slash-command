"""Discover and load command files from filesystem."""

import logging
from pathlib import Path

from .parser import CommandParser, ParsedCommand

logger = logging.getLogger(__name__)


class CommandLoader:
    """Loads custom slash commands from filesystem."""

    def __init__(self, parser: CommandParser | None = None):
        """Initialize loader.

        Args:
            parser: CommandParser instance (creates default if not provided)
        """
        self.parser = parser or CommandParser()

    def discover_commands(
        self, project_dir: Path | None = None, user_dir: Path | None = None
    ) -> list[ParsedCommand]:
        """Discover all commands from standard locations.

        Searches:
        1. Project commands: <project>/.amplifier/commands/
        2. User commands: ~/.amplifier/commands/

        Project commands take precedence over user commands.

        Args:
            project_dir: Project root (uses cwd if None)
            user_dir: User home (uses Path.home() if None)

        Returns:
            List of ParsedCommand instances
        """
        commands = []

        # Determine search paths
        if project_dir is None:
            project_dir = Path.cwd()
        if user_dir is None:
            user_dir = Path.home()

        project_commands_dir = project_dir / ".amplifier" / "commands"
        user_commands_dir = user_dir / ".amplifier" / "commands"

        # Track command names to handle precedence
        seen_commands: set[tuple[str, str | None]] = set()

        # Load project commands first (higher precedence)
        if project_commands_dir.exists():
            logger.debug(f"Scanning project commands: {project_commands_dir}")
            project_commands = self._load_from_directory(
                project_commands_dir, scope="project"
            )
            for cmd in project_commands:
                key = (cmd.name, cmd.namespace)
                commands.append(cmd)
                seen_commands.add(key)
            logger.info(
                f"Loaded {len(project_commands)} project command(s) from {project_commands_dir}"
            )

        # Load user commands (lower precedence)
        if user_commands_dir.exists():
            logger.debug(f"Scanning user commands: {user_commands_dir}")
            user_commands = self._load_from_directory(user_commands_dir, scope="user")
            for cmd in user_commands:
                key = (cmd.name, cmd.namespace)
                if key not in seen_commands:
                    commands.append(cmd)
                    seen_commands.add(key)
                else:
                    logger.debug(
                        f"Skipping user command '{cmd.name}' (namespace: {cmd.namespace}) - "
                        f"overridden by project command"
                    )
            logger.info(
                f"Loaded {len([c for c in user_commands if (c.name, c.namespace) not in seen_commands])} "
                f"user command(s) from {user_commands_dir}"
            )

        return commands

    def _load_from_directory(
        self, directory: Path, scope: str, namespace: str | None = None
    ) -> list[ParsedCommand]:
        """Load commands recursively from a directory.

        Args:
            directory: Directory to scan
            scope: "project" or "user"
            namespace: Current namespace (from parent directories)

        Returns:
            List of ParsedCommand instances
        """
        commands = []

        if not directory.is_dir():
            return commands

        for item in directory.iterdir():
            if item.is_file() and item.suffix == ".md":
                # Load command file
                try:
                    parsed = self.parser.parse_file(item, namespace=namespace)
                    # Attach scope for display purposes
                    parsed.scope = scope  # type: ignore[attr-defined]
                    commands.append(parsed)
                    logger.debug(
                        f"Loaded command: /{parsed.name} ({scope}"
                        f"{':' + namespace if namespace else ''})"
                    )
                except Exception as e:
                    logger.warning(f"Failed to load command from {item}: {e}")

            elif item.is_dir() and not item.name.startswith("."):
                # Recurse into subdirectory (creates namespace)
                subnamespace = f"{namespace}:{item.name}" if namespace else item.name
                subcommands = self._load_from_directory(item, scope, subnamespace)
                commands.extend(subcommands)

        return commands

    def load_single_command(
        self, file_path: Path, namespace: str | None = None
    ) -> ParsedCommand:
        """Load a single command file.

        Args:
            file_path: Path to .md file
            namespace: Optional namespace

        Returns:
            ParsedCommand instance

        Raises:
            ValueError: If file is invalid
        """
        return self.parser.parse_file(file_path, namespace=namespace)
