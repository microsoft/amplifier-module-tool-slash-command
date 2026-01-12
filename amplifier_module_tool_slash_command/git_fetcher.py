"""Git content fetcher for command repositories.

Handles lazy acquisition of command files from git URLs.
Uses a marker file convention (.amplifier-commands) to validate repos.
"""

from __future__ import annotations

import hashlib
import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Marker file that identifies a valid command repository
COMMANDS_MARKER_FILE = ".amplifier-commands"

# Default cache directory (under user's amplifier home)
DEFAULT_CACHE_DIR = Path.home() / ".amplifier" / "cache" / "commands"


class GitCommandFetcher:
    """Fetches command repositories from git URLs.

    Implements lazy acquisition: checks cache first, clones if not present.
    Validates repos contain the marker file (.amplifier-commands).
    """

    def __init__(self, cache_dir: Path | None = None):
        """Initialize fetcher.

        Args:
            cache_dir: Directory for caching cloned repos (uses default if None)
        """
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR

    def parse_git_url(self, url: str) -> tuple[str, str | None, str | None]:
        """Parse git URL into base URL, ref, and subpath.

        Args:
            url: Git URL like "git+https://github.com/org/repo@v1:subpath"

        Returns:
            Tuple of (git_url, ref, subpath) where ref and subpath may be None
        """
        # Remove git+ prefix if present
        if url.startswith("git+"):
            url = url[4:]

        ref = None
        subpath = None

        # Split on @ to get ref (and possibly subpath after ref)
        if "@" in url:
            base_part, ref_part = url.rsplit("@", 1)
            # Check if ref contains subpath (ref:subpath)
            if ":" in ref_part:
                ref, subpath = ref_part.split(":", 1)
            else:
                ref = ref_part
            url = base_part
        elif ":" in url and not url.startswith("http"):
            # Handle case of no ref but has subpath (unlikely)
            # e.g., "https://github.com/org/repo:subpath" - this is ambiguous
            # We'll assume the : after the domain is part of the URL
            pass

        return url, ref, subpath

    def get_cache_path(self, git_url: str, ref: str | None) -> Path:
        """Get the cache path for a git URL.

        Args:
            git_url: Base git URL (without git+ prefix)
            ref: Git ref (branch, tag, commit) or None for default

        Returns:
            Path where this repo should be cached
        """
        ref_str = ref or "HEAD"
        cache_key = hashlib.sha256(f"{git_url}@{ref_str}".encode()).hexdigest()[:16]
        repo_name = git_url.rstrip("/").split("/")[-1]
        return self.cache_dir / f"{repo_name}-{cache_key}"

    def is_valid_command_repo(self, path: Path) -> bool:
        """Check if a path contains a valid command directory.

        Validates:
        1. Directory exists
        2. Has marker file (.amplifier-commands)

        Note: .git check is skipped because path may be a subpath within a repo.

        Args:
            path: Path to check (may be repo root or subpath)

        Returns:
            True if valid command directory
        """
        if not path.exists():
            return False

        if not (path / COMMANDS_MARKER_FILE).exists():
            logger.debug(f"Missing marker file {COMMANDS_MARKER_FILE}: {path}")
            return False

        return True

    def fetch(self, url: str) -> Path | None:
        """Fetch a command repository from git URL.

        Implements lazy acquisition:
        1. Parse URL to get cache path
        2. If cached and valid, return cached path
        3. Otherwise clone and validate

        Supports subpaths for repos with commands in a subdirectory:
            git+https://github.com/org/repo@v1:commands

        Args:
            url: Git URL like "git+https://github.com/org/repo@v1:subpath"

        Returns:
            Path to command directory (may be subpath), or None if fetch failed
        """
        git_url, ref, subpath = self.parse_git_url(url)
        cache_path = self.get_cache_path(git_url, ref)

        # Determine the actual command directory (may be subpath)
        command_path = cache_path / subpath if subpath else cache_path

        # Check if already cached and valid
        if cache_path.exists():
            if self.is_valid_command_repo(command_path):
                logger.debug(f"Using cached command repo: {command_path}")
                return command_path
            else:
                # Invalid cache, remove it
                logger.warning(f"Invalid cached repo, removing: {cache_path}")
                shutil.rmtree(cache_path, ignore_errors=True)

        # Clone repository
        logger.info(f"Fetching command repo: {url}")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Build clone command
            clone_args = ["git", "clone", "--depth", "1"]
            if ref and ref != "HEAD":
                clone_args.extend(["--branch", ref])
            clone_args.extend([git_url, str(cache_path)])

            result = subprocess.run(
                clone_args,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                logger.error(f"Git clone failed: {result.stderr}")
                return None

            # Validate the command directory (may be subpath)
            if not self.is_valid_command_repo(command_path):
                logger.error(
                    f"Cloned repo is not a valid command repository "
                    f"(missing {COMMANDS_MARKER_FILE}): {url}"
                )
                shutil.rmtree(cache_path, ignore_errors=True)
                return None

            logger.info(f"Successfully fetched command repo to: {command_path}")
            return command_path

        except subprocess.TimeoutExpired:
            logger.error(f"Git clone timed out: {url}")
            shutil.rmtree(cache_path, ignore_errors=True)
            return None
        except Exception as e:
            logger.error(f"Failed to fetch command repo: {e}")
            shutil.rmtree(cache_path, ignore_errors=True)
            return None

    def fetch_all(self, urls: list[str]) -> list[Path]:
        """Fetch multiple command repositories.

        Args:
            urls: List of git URLs

        Returns:
            List of paths to successfully fetched repos
        """
        paths = []
        for url in urls:
            path = self.fetch(url)
            if path:
                paths.append(path)
        return paths
