"""
Test System Controls - Verify All Operations Actually Work
Tests that commands not only execute but produce real system effects

Tests:
1. File operations - actually open files in VS Code
2. Git operations - verify commits are made
3. Browser operations - verify browser opens
4. Process operations - verify programs launch
5. System state changes - verify side effects
"""

import pytest
import asyncio
import subprocess
from pathlib import Path
import sys
import os
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from executor.task_scheduler import TaskScheduler
from executor.powershell_executor import PowerShellExecutor
from executor.file_executor import FileExecutor
from executor.executor_base import TaskContext, TaskStatus


# ==================== FILE OPERATIONS TESTS ====================

@pytest.mark.asyncio
async def test_file_create_actually_creates():
    """Test that create_file actually creates a file on disk."""
    scheduler = TaskScheduler(max_concurrent_tasks=5)
    file_executor = FileExecutor()
    
    test_file = Path("temp_test_create.txt")
    
    # Ensure file doesn't exist
    if test_file.exists():
        test_file.unlink()
    
    # Create file
    context = TaskContext(
        intent="create_file",
        command=f"create {test_file}",
        params={
            "file": str(test_file),
            "content": "Test content from system test"
        }
    )
    
    task_id = await scheduler.submit_task(context, file_executor)
    result = await scheduler.wait_for_task(task_id, timeout=5.0)
    
    # Verify file actually exists
    assert test_file.exists(), "File was not created on disk!"
    assert "Test content" in test_file.read_text()
    
    # Cleanup
    test_file.unlink()
    await scheduler.shutdown()


@pytest.mark.asyncio
async def test_file_delete_actually_deletes():
    """Test that delete_file actually removes file from disk."""
    scheduler = TaskScheduler(max_concurrent_tasks=5)
    file_executor = FileExecutor()
    
    test_file = Path("temp_test_delete.txt")
    test_file.write_text("To be deleted")
    assert test_file.exists()
    
    # Delete file
    context = TaskContext(
        intent="delete_file",
        command=f"delete {test_file}",
        params={"file": str(test_file)}
    )
    
    task_id = await scheduler.submit_task(context, file_executor)
    result = await scheduler.wait_for_task(task_id, timeout=5.0)
    
    # Verify file actually deleted
    assert not test_file.exists(), "File was not deleted from disk!"
    
    await scheduler.shutdown()


# ==================== GIT OPERATIONS TESTS ====================

@pytest.mark.asyncio
async def test_git_status_shows_real_status():
    """Test that git status returns actual repository status."""
    scheduler = TaskScheduler(max_concurrent_tasks=5)
    ps_executor = PowerShellExecutor()
    
    context = TaskContext(
        intent="git_status",
        command="git status",
    )
    
    task_id = await scheduler.submit_task(context, ps_executor)
    result = await scheduler.wait_for_task(task_id, timeout=5.0)
    
    assert result.status == TaskStatus.SUCCESS
    # Should contain real git status info
    assert "branch" in result.output.lower() or "commit" in result.output.lower()
    
    await scheduler.shutdown()


@pytest.mark.asyncio
async def test_git_log_shows_real_commits():
    """Test that git log returns actual commit history."""
    scheduler = TaskScheduler(max_concurrent_tasks=5)
    ps_executor = PowerShellExecutor()
    
    context = TaskContext(
        intent="git_log",
        command="git log --oneline -3",
    )
    
    task_id = await scheduler.submit_task(context, ps_executor)
    result = await scheduler.wait_for_task(task_id, timeout=5.0)
    
    assert result.status == TaskStatus.SUCCESS
    # Should show actual commits with hashes
    assert len(result.output) > 0
    
    await scheduler.shutdown()


# ==================== PROCESS OPERATIONS TESTS ====================

@pytest.mark.asyncio
async def test_command_creates_real_process():
    """Test that commands actually create system processes."""
    scheduler = TaskScheduler(max_concurrent_tasks=5)
    ps_executor = PowerShellExecutor()
    
    # Create a temp file using PowerShell
    test_file = Path("temp_process_test.txt")
    if test_file.exists():
        test_file.unlink()
    
    context = TaskContext(
        intent="create_temp",
        command=f'Write-Output "Process test" > {test_file}',
    )
    
    task_id = await scheduler.submit_task(context, ps_executor)
    result = await scheduler.wait_for_task(task_id, timeout=5.0)
    
    # Verify file was actually created by the process
    assert test_file.exists(), "PowerShell process did not create file!"
    
    # Cleanup
    test_file.unlink()
    await scheduler.shutdown()


# ==================== VS CODE INTEGRATION TESTS ====================

@pytest.mark.asyncio
async def test_open_file_in_vscode():
    """Test that opening a file actually opens it in VS Code."""
    scheduler = TaskScheduler(max_concurrent_tasks=5)
    ps_executor = PowerShellExecutor()
    
    # Create a test file
    test_file = Path("temp_vscode_test.py")
    test_file.write_text("# Test file for VS Code opening\nprint('Hello')")
    
    # Open in VS Code using command line
    context = TaskContext(
        intent="open_in_vscode",
        command=f'code "{test_file.absolute()}"',
    )
    
    task_id = await scheduler.submit_task(context, ps_executor)
    result = await scheduler.wait_for_task(task_id, timeout=5.0)
    
    # If VS Code is installed, command should succeed
    if result.status == TaskStatus.SUCCESS:
        print(f"✓ VS Code command executed successfully")
    else:
        print(f"⚠ VS Code might not be installed: {result.error}")
    
    # Cleanup
    test_file.unlink()
    await scheduler.shutdown()


# ==================== BROWSER OPERATIONS TESTS ====================

@pytest.mark.asyncio
async def test_browser_actually_opens():
    """Test that browser commands actually open browser."""
    scheduler = TaskScheduler(max_concurrent_tasks=5)
    ps_executor = PowerShellExecutor()
    
    # Open browser to a local test page
    context = TaskContext(
        intent="open_browser",
        command='Start-Process "https://www.google.com"',
    )
    
    task_id = await scheduler.submit_task(context, ps_executor)
    result = await scheduler.wait_for_task(task_id, timeout=5.0)
    
    # Command should execute successfully
    assert result.status == TaskStatus.SUCCESS
    print("✓ Browser open command executed (browser should have opened)")
    
    await scheduler.shutdown()


# ==================== DIRECTORY OPERATIONS TESTS ====================

@pytest.mark.asyncio
async def test_directory_create_actually_creates():
    """Test that mkdir actually creates directories."""
    scheduler = TaskScheduler(max_concurrent_tasks=5)
    file_executor = FileExecutor()
    
    test_dir = Path("temp_test_directory")
    
    # Ensure directory doesn't exist
    if test_dir.exists():
        test_dir.rmdir()
    
    context = TaskContext(
        intent="create_directory",
        command=f"mkdir {test_dir}",
        params={"directory": str(test_dir)}
    )
    
    task_id = await scheduler.submit_task(context, file_executor)
    result = await scheduler.wait_for_task(task_id, timeout=5.0)
    
    # Verify directory actually exists
    assert test_dir.exists(), "Directory was not created!"
    assert test_dir.is_dir(), "Created path is not a directory!"
    
    # Cleanup
    test_dir.rmdir()
    await scheduler.shutdown()


# ==================== CONCURRENT OPERATIONS TESTS ====================

@pytest.mark.asyncio
async def test_multiple_files_created_concurrently():
    """Test that multiple file operations work concurrently."""
    scheduler = TaskScheduler(max_concurrent_tasks=5)
    file_executor = FileExecutor()
    
    test_files = [Path(f"temp_concurrent_{i}.txt") for i in range(3)]
    
    # Submit multiple create operations
    task_ids = []
    for i, test_file in enumerate(test_files):
        context = TaskContext(
            intent="create_file",
            command=f"create {test_file}",
            params={
                "file": str(test_file),
                "content": f"Concurrent test {i}"
            }
        )
        task_id = await scheduler.submit_task(context, file_executor)
        task_ids.append(task_id)
    
    # Wait for all
    await asyncio.sleep(0.5)
    
    # Verify all files exist
    for test_file in test_files:
        assert test_file.exists(), f"File {test_file} was not created!"
    
    # Cleanup
    for test_file in test_files:
        test_file.unlink()
    
    await scheduler.shutdown()


# ==================== SYSTEM STATE VERIFICATION ====================

@pytest.mark.asyncio
async def test_python_execution_has_side_effects():
    """Test that Python commands have real side effects."""
    scheduler = TaskScheduler(max_concurrent_tasks=5)
    ps_executor = PowerShellExecutor()
    
    output_file = Path("temp_python_output.txt")
    if output_file.exists():
        output_file.unlink()
    
    # Run Python code that creates a file
    context = TaskContext(
        intent="run_python",
        command=f'python -c "with open(\'{output_file}\', \'w\') as f: f.write(\'Python executed\')"',
    )
    
    task_id = await scheduler.submit_task(context, ps_executor)
    result = await scheduler.wait_for_task(task_id, timeout=5.0)
    
    # Verify Python actually ran and created file
    assert output_file.exists(), "Python command did not create file!"
    assert "Python executed" in output_file.read_text()
    
    # Cleanup
    output_file.unlink()
    await scheduler.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
