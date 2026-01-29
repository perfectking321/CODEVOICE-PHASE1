"""
Tests for BUILD 10: File Operations Executor
Tests file system operations for opening, creating, editing files

Testing:
1. Open file command
2. Create file command
3. Read file contents
4. Write to file
5. Delete file
6. File existence checks
7. Directory operations
"""

import pytest
import asyncio
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from executor.executor_base import TaskContext, TaskStatus
from executor.file_executor import FileExecutor


# ==================== FIXTURES ====================

@pytest.fixture
async def file_executor():
    """File executor instance."""
    return FileExecutor()


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create temporary directory for tests."""
    test_dir = tmp_path / "codevoice_test"
    test_dir.mkdir(exist_ok=True)
    return test_dir


# ==================== FILE OPEN TESTS ====================

@pytest.mark.asyncio
async def test_file_open_existing(file_executor, temp_test_dir):
    """Test opening an existing file."""
    # Create test file
    test_file = temp_test_dir / "test.txt"
    test_file.write_text("Hello World")
    
    context = TaskContext(
        intent="open_file",
        command=f"open {test_file}",
        params={"file": str(test_file)}
    )
    
    result = await file_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert str(test_file) in result.output


@pytest.mark.asyncio
async def test_file_open_nonexistent(file_executor, temp_test_dir):
    """Test opening a non-existent file."""
    test_file = temp_test_dir / "nonexistent.txt"
    
    context = TaskContext(
        intent="open_file",
        command=f"open {test_file}",
        params={"file": str(test_file)}
    )
    
    result = await file_executor.execute(context)
    
    # Should handle gracefully - either fail or create
    assert result.status in [TaskStatus.SUCCESS, TaskStatus.FAILED]


# ==================== FILE CREATE TESTS ====================

@pytest.mark.asyncio
async def test_file_create_new(file_executor, temp_test_dir):
    """Test creating a new file."""
    test_file = temp_test_dir / "new_file.txt"
    
    context = TaskContext(
        intent="create_file",
        command=f"create {test_file}",
        params={
            "file": str(test_file),
            "content": "print('Hello CodeVoice')"
        }
    )
    
    result = await file_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert test_file.exists()
    assert "Hello CodeVoice" in test_file.read_text()


@pytest.mark.asyncio
async def test_file_create_with_directory(file_executor, temp_test_dir):
    """Test creating file in nested directory."""
    test_file = temp_test_dir / "subdir" / "test.py"
    
    context = TaskContext(
        intent="create_file",
        command=f"create {test_file}",
        params={
            "file": str(test_file),
            "content": "# Test file"
        }
    )
    
    result = await file_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert test_file.exists()
    assert test_file.parent.exists()


# ==================== FILE READ TESTS ====================

@pytest.mark.asyncio
async def test_file_read_content(file_executor, temp_test_dir):
    """Test reading file contents."""
    test_file = temp_test_dir / "read_test.txt"
    content = "Line 1\nLine 2\nLine 3"
    test_file.write_text(content)
    
    context = TaskContext(
        intent="read_file",
        command=f"read {test_file}",
        params={"file": str(test_file)}
    )
    
    result = await file_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert "Line 1" in result.output
    assert "Line 3" in result.output


# ==================== FILE WRITE TESTS ====================

@pytest.mark.asyncio
async def test_file_write_content(file_executor, temp_test_dir):
    """Test writing to existing file."""
    test_file = temp_test_dir / "write_test.txt"
    test_file.write_text("Original content")
    
    new_content = "Updated content"
    
    context = TaskContext(
        intent="write_file",
        command=f"write {test_file}",
        params={
            "file": str(test_file),
            "content": new_content
        }
    )
    
    result = await file_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert test_file.read_text() == new_content


# ==================== FILE DELETE TESTS ====================

@pytest.mark.asyncio
async def test_file_delete(file_executor, temp_test_dir):
    """Test deleting a file."""
    test_file = temp_test_dir / "delete_test.txt"
    test_file.write_text("To be deleted")
    assert test_file.exists()
    
    context = TaskContext(
        intent="delete_file",
        command=f"delete {test_file}",
        params={"file": str(test_file)}
    )
    
    result = await file_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert not test_file.exists()


# ==================== FILE EXISTS TESTS ====================

@pytest.mark.asyncio
async def test_file_exists_check(file_executor, temp_test_dir):
    """Test checking if file exists."""
    test_file = temp_test_dir / "exists_test.txt"
    test_file.write_text("Exists")
    
    context = TaskContext(
        intent="check_file",
        command=f"exists {test_file}",
        params={"file": str(test_file)}
    )
    
    result = await file_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert "exists" in result.output.lower()


# ==================== DIRECTORY TESTS ====================

@pytest.mark.asyncio
async def test_directory_create(file_executor, temp_test_dir):
    """Test creating a directory."""
    test_dir = temp_test_dir / "new_directory"
    
    context = TaskContext(
        intent="create_directory",
        command=f"mkdir {test_dir}",
        params={"directory": str(test_dir)}
    )
    
    result = await file_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert test_dir.exists()
    assert test_dir.is_dir()


@pytest.mark.asyncio
async def test_directory_list(file_executor, temp_test_dir):
    """Test listing directory contents."""
    # Create some files
    (temp_test_dir / "file1.txt").write_text("1")
    (temp_test_dir / "file2.txt").write_text("2")
    
    context = TaskContext(
        intent="list_directory",
        command=f"ls {temp_test_dir}",
        params={"directory": str(temp_test_dir)}
    )
    
    result = await file_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    assert "file1.txt" in result.output
    assert "file2.txt" in result.output


# ==================== PATH RESOLUTION TESTS ====================

@pytest.mark.asyncio
async def test_relative_path_resolution(file_executor):
    """Test resolving relative paths."""
    context = TaskContext(
        intent="open_file",
        command="open main.py",
        params={"file": "main.py"}
    )
    
    result = await file_executor.execute(context)
    
    # Should handle relative paths
    assert result.status in [TaskStatus.SUCCESS, TaskStatus.FAILED]


# ==================== ERROR HANDLING TESTS ====================

@pytest.mark.asyncio
async def test_invalid_file_operation(file_executor):
    """Test handling invalid file operations."""
    context = TaskContext(
        intent="read_file",
        command="read /invalid/path/that/does/not/exist.txt",
        params={"file": "/invalid/path/that/does/not/exist.txt"}
    )
    
    result = await file_executor.execute(context)
    
    assert result.status == TaskStatus.FAILED
    assert len(result.error) > 0


# ==================== PERFORMANCE TESTS ====================

@pytest.mark.asyncio
async def test_file_operation_latency(file_executor, temp_test_dir):
    """Test file operations complete quickly."""
    test_file = temp_test_dir / "latency_test.txt"
    
    context = TaskContext(
        intent="create_file",
        command=f"create {test_file}",
        params={
            "file": str(test_file),
            "content": "test"
        }
    )
    
    result = await file_executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    # File operations should be very fast (<100ms)
    assert result.latency_ms < 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
