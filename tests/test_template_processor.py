"""Tests for template processor (bash execution, file references)."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from slash_command.template_processor import ProcessedTemplate, TemplateProcessor


class TestBashExecution:
    """Tests for bash command execution."""

    @pytest.fixture
    def processor(self, tmp_path: Path) -> TemplateProcessor:
        """Create processor with temp working directory."""
        return TemplateProcessor(working_dir=tmp_path, timeout=5)

    @pytest.mark.asyncio
    async def test_inline_bash_with_permission(self, processor: TemplateProcessor):
        """Inline bash executes when allowed."""
        template = "Current date: !`date +%Y`"
        result = await processor.process(template, allowed_tools=["bash"])

        assert result.bash_commands_executed == 1
        assert "202" in result.content  # Year starts with 202x
        assert "!`" not in result.content

    @pytest.mark.asyncio
    async def test_inline_bash_without_permission(self, processor: TemplateProcessor):
        """Inline bash not executed without permission."""
        template = "Current date: !`date +%Y`"
        result = await processor.process(template, allowed_tools=None)

        assert result.bash_commands_executed == 0
        assert "!`date" in result.content  # Left unchanged
        assert result.warnings is not None
        assert any("bash" in w.lower() for w in result.warnings)

    @pytest.mark.asyncio
    async def test_multiple_inline_bash(self, processor: TemplateProcessor):
        """Multiple inline bash commands execute."""
        template = "User: !`whoami` Home: !`echo $HOME`"
        result = await processor.process(template, allowed_tools=["bash"])

        assert result.bash_commands_executed == 2
        assert "!`" not in result.content

    @pytest.mark.asyncio
    async def test_bash_block(self, processor: TemplateProcessor):
        """Bash block executes."""
        template = """Before
!```
echo "hello"
echo "world"
```
After"""
        result = await processor.process(template, allowed_tools=["bash"])

        assert result.bash_commands_executed == 1
        assert "hello" in result.content
        assert "world" in result.content
        assert "!```" not in result.content

    @pytest.mark.asyncio
    async def test_bash_command_failure(self, processor: TemplateProcessor):
        """Failed bash command includes error info."""
        template = "Result: !`exit 1`"
        result = await processor.process(template, allowed_tools=["bash"])

        assert result.bash_commands_executed == 1
        assert "exit" in result.content.lower() or "code" in result.content.lower()

    @pytest.mark.asyncio
    async def test_bash_timeout(self, tmp_path: Path):
        """Bash command timeout is handled."""
        processor = TemplateProcessor(working_dir=tmp_path, timeout=1)
        template = "Result: !`sleep 10`"
        result = await processor.process(template, allowed_tools=["bash"])

        assert result.bash_commands_executed == 1
        assert "timed out" in result.content.lower()


class TestFileReferences:
    """Tests for @file references."""

    @pytest.fixture
    def processor(self, tmp_path: Path) -> TemplateProcessor:
        """Create processor with temp working directory."""
        return TemplateProcessor(working_dir=tmp_path)

    @pytest.mark.asyncio
    async def test_file_reference(self, processor: TemplateProcessor, tmp_path: Path):
        """File reference includes content."""
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    print('hi')")

        template = "Review this:\n@test.py"
        result = await processor.process(template)

        assert result.files_included == 1
        assert "def hello" in result.content
        assert "```" in result.content  # Wrapped in code block

    @pytest.mark.asyncio
    async def test_multiple_file_references(
        self, processor: TemplateProcessor, tmp_path: Path
    ):
        """Multiple file references work."""
        (tmp_path / "a.py").write_text("# file a")
        (tmp_path / "b.py").write_text("# file b")

        template = "Files:\n@a.py\n@b.py"
        result = await processor.process(template)

        assert result.files_included == 2
        assert "file a" in result.content
        assert "file b" in result.content

    @pytest.mark.asyncio
    async def test_missing_file_reference(
        self, processor: TemplateProcessor, tmp_path: Path
    ):
        """Missing file reference produces warning."""
        template = "Review:\n@nonexistent.py"
        result = await processor.process(template)

        assert result.files_included == 0
        assert result.warnings is not None
        assert any("not found" in w.lower() for w in result.warnings)
        assert "@nonexistent.py" in result.content  # Left unchanged

    @pytest.mark.asyncio
    async def test_nested_file_reference(
        self, processor: TemplateProcessor, tmp_path: Path
    ):
        """Nested directory file references work."""
        subdir = tmp_path / "src"
        subdir.mkdir()
        (subdir / "main.py").write_text("# main code")

        template = "Review:\n@src/main.py"
        result = await processor.process(template)

        assert result.files_included == 1
        assert "main code" in result.content


class TestCombinedProcessing:
    """Tests for combined bash + file processing."""

    @pytest.mark.asyncio
    async def test_bash_and_files_together(self, tmp_path: Path):
        """Both bash and file refs process together."""
        processor = TemplateProcessor(working_dir=tmp_path)

        (tmp_path / "config.txt").write_text("setting=value")

        template = """Config: @config.txt

Status: !`echo "OK"`"""

        result = await processor.process(template, allowed_tools=["bash"])

        assert result.bash_commands_executed == 1
        assert result.files_included == 1
        assert "setting=value" in result.content
        assert "OK" in result.content

    @pytest.mark.asyncio
    async def test_no_processing_when_disabled(self, tmp_path: Path):
        """Processing can be disabled."""
        processor = TemplateProcessor(working_dir=tmp_path)

        template = "Test: !`echo hi` @file.txt"
        result = await processor.process(
            template, allowed_tools=["bash"], include_files=False
        )

        # Bash should process
        assert result.bash_commands_executed == 1
        # File refs left alone
        assert "@file.txt" in result.content


class TestProcessedTemplateResult:
    """Tests for ProcessedTemplate dataclass."""

    def test_default_values(self):
        """Default values are sensible."""
        result = ProcessedTemplate(content="test")
        assert result.content == "test"
        assert result.bash_commands_executed == 0
        assert result.files_included == 0
        assert result.warnings is None

    def test_with_values(self):
        """All values can be set."""
        result = ProcessedTemplate(
            content="processed",
            bash_commands_executed=3,
            files_included=2,
            warnings=["warning1"],
        )
        assert result.bash_commands_executed == 3
        assert result.files_included == 2
        assert len(result.warnings) == 1
