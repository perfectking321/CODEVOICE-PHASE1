"""
Tests for BUILD 9: PowerShell Executor
Tests CLI command execution on Windows

Testing:
1. PowerShell command execution
2. Command output capture
3. Error handling (non-zero exit codes)
4. Environment variables
5. Working directory
6. Timeout handling
7. Real git commands
8. Package installation commands
"""

import pytest
import asyncio
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from executor.executor_base import TaskContext, TaskStatus
from executor.powershell_executor import PowerShellExecutor


# ==================== FIXTURES ====================

@pytest.fixture
async def ps_executor():
    """PowerShell executor instance."""
    return PowerShellExecutor()


# ==================== BASIC EXECUTION TESTS ====================

@pytest.mark.asyncio
async def test_powershell_simple_command(ps_executor):
    """Test simple echo command."""
    context = TaskContext(
        intent="test_echo",
        command="Write-Output 'Hello CodeVoice'"
    )
    
    result = await ps_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert "Hello CodeVoice" in result.output
    assert result.latency_ms > 0


@pytest.mark.asyncio
async def test_powershell_get_location(ps_executor):
    """Test Get-Location command."""
    context = TaskContext(
        intent="test_location",
        command="Get-Location"
    )
    
    result = await ps_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert len(result.output) > 0
    # Output should contain a path
    assert ":" in result.output or "\\" in result.output or "/" in result.output


@pytest.mark.asyncio
async def test_powershell_list_files(ps_executor):
    """Test listing files in directory."""
    context = TaskContext(
        intent="test_list",
        command="Get-ChildItem -Path . -Name | Select-Object -First 5"
    )
    
    result = await ps_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert len(result.output) > 0


@pytest.mark.asyncio
async def test_powershell_arithmetic(ps_executor):
    """Test arithmetic expression."""
    context = TaskContext(
        intent="test_math",
        command="Write-Output (42 + 58)"
    )
    
    result = await ps_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert "100" in result.output


# ==================== ERROR HANDLING TESTS ====================

@pytest.mark.asyncio
async def test_powershell_invalid_command(ps_executor):
    """Test handling of invalid command."""
    context = TaskContext(
        intent="test_invalid",
        command="This-Command-Does-Not-Exist"
    )
    
    result = await ps_executor.execute(context)
    
    # Should fail but not crash
    assert result.status == TaskStatus.FAILED
    assert len(result.error) > 0


@pytest.mark.asyncio
async def test_powershell_command_with_error(ps_executor):
    """Test command that produces error."""
    context = TaskContext(
        intent="test_error",
        command="Get-Item 'C:\\ThisFileDoesNotExist123456.txt'"
    )
    
    result = await ps_executor.execute(context)
    
    # Should capture error
    assert result.status == TaskStatus.FAILED
    assert "cannot find" in result.error.lower() or "does not exist" in result.error.lower()


@pytest.mark.asyncio
async def test_powershell_timeout(ps_executor):
    """Test command timeout."""
    context = TaskContext(
        intent="test_timeout",
        command="Start-Sleep -Seconds 10",
        timeout_seconds=1  # 1 second timeout
    )
    
    result = await ps_executor.execute(context)
    
    assert result.status == TaskStatus.TIMEOUT
    assert "timeout" in result.error.lower()


# ==================== WORKING DIRECTORY TESTS ====================

@pytest.mark.asyncio
async def test_powershell_working_directory(ps_executor):
    """Test command with specific working directory."""
    # Use temp directory
    temp_dir = Path.cwd() / "temp_test_dir"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        context = TaskContext(
            intent="test_workdir",
            command="Get-Location",
            working_directory=str(temp_dir)
        )
        
        result = await ps_executor.execute(context)
        
        assert result.status == TaskStatus.SUCCESS
        assert "temp_test_dir" in result.output
    
    finally:
        # Cleanup
        if temp_dir.exists():
            temp_dir.rmdir()


# ==================== ENVIRONMENT VARIABLES TESTS ====================

@pytest.mark.asyncio
async def test_powershell_environment_variable(ps_executor):
    """Test command with custom environment variable."""
    context = TaskContext(
        intent="test_env",
        command="Write-Output $env:CODEVOICE_TEST_VAR",
        environment={"CODEVOICE_TEST_VAR": "test_value_123"}
    )
    
    result = await ps_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert "test_value_123" in result.output


# ==================== GIT COMMAND TESTS ====================

@pytest.mark.asyncio
async def test_powershell_git_version(ps_executor):
    """Test git version command."""
    context = TaskContext(
        intent="git_version",
        command="git --version"
    )
    
    result = await ps_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert "git version" in result.output.lower()


@pytest.mark.asyncio
async def test_powershell_git_status(ps_executor):
    """Test git status in project directory."""
    # This should work if we're in a git repo
    context = TaskContext(
        intent="git_status",
        command="git status",
        working_directory=str(Path(__file__).parent.parent)
    )
    
    result = await ps_executor.execute(context)
    
    # Should work if in git repo, otherwise should fail gracefully
    assert result.status in [TaskStatus.SUCCESS, TaskStatus.FAILED]
    if result.status == TaskStatus.SUCCESS:
        assert "branch" in result.output.lower() or "commit" in result.output.lower()


# ==================== PYTHON COMMAND TESTS ====================

@pytest.mark.asyncio
async def test_powershell_python_version(ps_executor):
    """Test Python version command."""
    context = TaskContext(
        intent="python_version",
        command="python --version"
    )
    
    result = await ps_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert "Python" in result.output


@pytest.mark.asyncio
async def test_powershell_python_expression(ps_executor):
    """Test Python expression evaluation."""
    context = TaskContext(
        intent="python_expr",
        command='python -c "print(2 + 2)"'
    )
    
    result = await ps_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert "4" in result.output


# ==================== PERFORMANCE TESTS ====================

@pytest.mark.asyncio
async def test_powershell_execution_latency(ps_executor):
    """Test execution latency is reasonable."""
    context = TaskContext(
        intent="test_latency",
        command="Write-Output 'fast'"
    )
    
    result = await ps_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    # Should be under 500ms for simple command
    assert result.latency_ms < 500


@pytest.mark.asyncio
async def test_powershell_concurrent_execution():
    """Test multiple commands can run concurrently."""
    executor = PowerShellExecutor()
    
    contexts = [
        TaskContext(intent=f"concurrent_{i}", command=f"Write-Output {i}")
        for i in range(5)
    ]
    
    # Execute all concurrently
    results = await asyncio.gather(*[
        executor.execute(ctx) for ctx in contexts
    ])
    
    assert len(results) == 5
    for i, result in enumerate(results):
        assert result.status == TaskStatus.SUCCESS
        assert str(i) in result.output


# ==================== MULTILINE COMMAND TESTS ====================

@pytest.mark.asyncio
async def test_powershell_multiline_command(ps_executor):
    """Test multiline PowerShell command."""
    context = TaskContext(
        intent="test_multiline",
        command="""
        $a = 10
        $b = 20
        Write-Output ($a + $b)
        """
    )
    
    result = await ps_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert "30" in result.output


# ==================== PIPED COMMAND TESTS ====================

@pytest.mark.asyncio
async def test_powershell_piped_command(ps_executor):
    """Test command with pipeline."""
    context = TaskContext(
        intent="test_pipeline",
        command="Get-Process | Select-Object -First 1 | Format-Table Name"
    )
    
    result = await ps_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert len(result.output) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
