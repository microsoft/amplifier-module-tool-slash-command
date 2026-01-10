"""Tests for granular permission parsing and validation."""

import pytest

from amplifier_module_tool_slash_command.permissions import (
    GranularPermission,
    get_bash_permissions_summary,
    is_bash_command_allowed,
    is_tool_allowed,
    parse_permission,
    parse_permissions,
)


class TestParsePermission:
    """Tests for parse_permission function."""

    def test_simple_tool(self):
        """Parse simple tool name."""
        perm = parse_permission("bash")
        assert perm.tool == "bash"
        assert perm.pattern is None

    def test_simple_tool_uppercase(self):
        """Parse uppercase tool name (normalized to lowercase)."""
        perm = parse_permission("Bash")
        assert perm.tool == "bash"
        assert perm.pattern is None

    def test_granular_permission(self):
        """Parse granular permission with pattern."""
        perm = parse_permission("Bash(git add:*)")
        assert perm.tool == "bash"
        assert perm.pattern == "git add:*"

    def test_granular_permission_git_status(self):
        """Parse git status permission."""
        perm = parse_permission("Bash(git status:*)")
        assert perm.tool == "bash"
        assert perm.pattern == "git status:*"

    def test_granular_permission_with_spaces(self):
        """Parse permission with spaces in pattern."""
        perm = parse_permission("Bash(git commit -m:*)")
        assert perm.tool == "bash"
        assert perm.pattern == "git commit -m:*"

    def test_empty_spec_raises(self):
        """Empty spec raises ValueError."""
        with pytest.raises(ValueError, match="Empty permission"):
            parse_permission("")

    def test_invalid_format_raises(self):
        """Invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid permission"):
            parse_permission("(invalid)")

    def test_whitespace_stripped(self):
        """Whitespace is stripped from spec."""
        perm = parse_permission("  bash  ")
        assert perm.tool == "bash"


class TestParsePermissions:
    """Tests for parse_permissions function."""

    def test_empty_list(self):
        """Empty list returns empty permissions."""
        assert parse_permissions([]) == []

    def test_none_input(self):
        """None input returns empty permissions."""
        assert parse_permissions(None) == []

    def test_multiple_permissions(self):
        """Parse multiple permissions."""
        perms = parse_permissions(["bash", "Bash(git add:*)", "edit"])
        assert len(perms) == 3
        assert perms[0].tool == "bash"
        assert perms[0].pattern is None
        assert perms[1].tool == "bash"
        assert perms[1].pattern == "git add:*"
        assert perms[2].tool == "edit"


class TestGranularPermissionAllowsCommand:
    """Tests for GranularPermission.allows_command method."""

    def test_no_pattern_allows_all(self):
        """Permission without pattern allows all bash commands."""
        perm = GranularPermission(tool="bash", pattern=None)
        assert perm.allows_command("ls -la")
        assert perm.allows_command("rm -rf /")
        assert perm.allows_command("git add .")

    def test_pattern_allows_matching(self):
        """Permission with pattern allows matching commands."""
        perm = GranularPermission(tool="bash", pattern="git add:*")
        assert perm.allows_command("git add .")
        assert perm.allows_command("git add -A")
        assert perm.allows_command("git add file.txt")

    def test_pattern_blocks_non_matching(self):
        """Permission with pattern blocks non-matching commands."""
        perm = GranularPermission(tool="bash", pattern="git add:*")
        assert not perm.allows_command("git commit -m 'test'")
        assert not perm.allows_command("rm -rf /")
        assert not perm.allows_command("ls")

    def test_pattern_git_status(self):
        """Git status pattern works correctly."""
        perm = GranularPermission(tool="bash", pattern="git status:*")
        assert perm.allows_command("git status")
        assert perm.allows_command("git status --short")
        assert not perm.allows_command("git add .")

    def test_pattern_git_diff(self):
        """Git diff pattern works correctly."""
        perm = GranularPermission(tool="bash", pattern="git diff:*")
        assert perm.allows_command("git diff")
        assert perm.allows_command("git diff HEAD")
        assert perm.allows_command("git diff --staged")
        assert not perm.allows_command("git status")

    def test_non_bash_tool_returns_false(self):
        """Non-bash tool permissions don't allow bash commands."""
        perm = GranularPermission(tool="edit", pattern=None)
        assert not perm.allows_command("ls")

    def test_command_with_leading_whitespace(self):
        """Commands with leading whitespace are handled."""
        perm = GranularPermission(tool="bash", pattern="git add:*")
        assert perm.allows_command("  git add .")


class TestIsBashCommandAllowed:
    """Tests for is_bash_command_allowed function."""

    def test_no_bash_permissions(self):
        """No bash permissions returns not allowed."""
        perms = [GranularPermission(tool="edit", pattern=None)]
        allowed, reason = is_bash_command_allowed("ls", perms)
        assert not allowed
        assert "bash not in allowed-tools" in reason

    def test_simple_bash_allows_all(self):
        """Simple bash permission allows all commands."""
        perms = [GranularPermission(tool="bash", pattern=None)]
        allowed, reason = is_bash_command_allowed("rm -rf /", perms)
        assert allowed
        assert reason is None

    def test_granular_allows_matching(self):
        """Granular permission allows matching commands."""
        perms = [GranularPermission(tool="bash", pattern="git add:*")]
        allowed, reason = is_bash_command_allowed("git add .", perms)
        assert allowed
        assert reason is None

    def test_granular_blocks_non_matching(self):
        """Granular permission blocks non-matching commands."""
        perms = [GranularPermission(tool="bash", pattern="git add:*")]
        allowed, reason = is_bash_command_allowed("git commit -m 'test'", perms)
        assert not allowed
        assert "does not match allowed patterns" in reason

    def test_multiple_patterns_any_match(self):
        """Multiple patterns - any match allows command."""
        perms = [
            GranularPermission(tool="bash", pattern="git add:*"),
            GranularPermission(tool="bash", pattern="git status:*"),
            GranularPermission(tool="bash", pattern="git diff:*"),
        ]
        # All should be allowed
        assert is_bash_command_allowed("git add .", perms)[0]
        assert is_bash_command_allowed("git status", perms)[0]
        assert is_bash_command_allowed("git diff HEAD", perms)[0]
        # This should be blocked
        assert not is_bash_command_allowed("git commit -m 'test'", perms)[0]


class TestIsToolAllowed:
    """Tests for is_tool_allowed function."""

    def test_tool_in_permissions(self):
        """Tool in permissions returns True."""
        perms = [GranularPermission(tool="bash", pattern=None)]
        assert is_tool_allowed("bash", perms)
        assert is_tool_allowed("Bash", perms)  # Case insensitive

    def test_tool_not_in_permissions(self):
        """Tool not in permissions returns False."""
        perms = [GranularPermission(tool="bash", pattern=None)]
        assert not is_tool_allowed("edit", perms)

    def test_empty_permissions(self):
        """Empty permissions returns False."""
        assert not is_tool_allowed("bash", [])


class TestGetBashPermissionsSummary:
    """Tests for get_bash_permissions_summary function."""

    def test_no_bash_permissions(self):
        """No bash permissions returns appropriate message."""
        perms = [GranularPermission(tool="edit", pattern=None)]
        assert get_bash_permissions_summary(perms) == "no bash commands allowed"

    def test_all_bash_allowed(self):
        """Simple bash permission returns 'all bash commands'."""
        perms = [GranularPermission(tool="bash", pattern=None)]
        assert get_bash_permissions_summary(perms) == "all bash commands"

    def test_granular_permissions(self):
        """Granular permissions returns comma-separated patterns."""
        perms = [
            GranularPermission(tool="bash", pattern="git add:*"),
            GranularPermission(tool="bash", pattern="git status:*"),
        ]
        summary = get_bash_permissions_summary(perms)
        assert "git add:*" in summary
        assert "git status:*" in summary


class TestIntegrationScenarios:
    """Integration tests for realistic permission scenarios."""

    def test_safe_git_operations_only(self):
        """Test a realistic 'safe git operations only' permission set."""
        specs = [
            "Bash(git add:*)",
            "Bash(git status:*)",
            "Bash(git diff:*)",
            "Bash(git log:*)",
        ]
        perms = parse_permissions(specs)

        # Should allow
        assert is_bash_command_allowed("git add .", perms)[0]
        assert is_bash_command_allowed("git status --short", perms)[0]
        assert is_bash_command_allowed("git diff HEAD~1", perms)[0]
        assert is_bash_command_allowed("git log --oneline -10", perms)[0]

        # Should block
        assert not is_bash_command_allowed("git push origin main", perms)[0]
        assert not is_bash_command_allowed("git reset --hard HEAD~1", perms)[0]
        assert not is_bash_command_allowed("rm -rf /", perms)[0]
        assert not is_bash_command_allowed("curl https://evil.com", perms)[0]

    def test_mixed_simple_and_granular(self):
        """Test mixing simple 'bash' with granular permissions."""
        # If simple 'bash' is present, it allows everything
        specs = ["bash", "Bash(git add:*)"]
        perms = parse_permissions(specs)

        # Simple 'bash' allows everything
        assert is_bash_command_allowed("rm -rf /", perms)[0]
        assert is_bash_command_allowed("curl https://evil.com", perms)[0]

    def test_read_only_operations(self):
        """Test read-only operations permission set."""
        specs = [
            "Bash(ls:*)",
            "Bash(cat:*)",
            "Bash(head:*)",
            "Bash(tail:*)",
            "Bash(grep:*)",
            "Bash(find:*)",
        ]
        perms = parse_permissions(specs)

        # Should allow
        assert is_bash_command_allowed("ls -la", perms)[0]
        assert is_bash_command_allowed("cat file.txt", perms)[0]
        assert is_bash_command_allowed("grep -r 'pattern' .", perms)[0]

        # Should block
        assert not is_bash_command_allowed("rm file.txt", perms)[0]
        assert not is_bash_command_allowed("echo 'data' > file.txt", perms)[0]
