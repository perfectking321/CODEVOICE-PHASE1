"""
Test Actual File Opening - Verify FileExecutor Opens Files
This test verifies that the FileExecutor actually opens files in VS Code or default app
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from executor.file_executor import FileExecutor
from executor.executor_base import TaskContext, TaskStatus


@pytest.mark.asyncio
async def test_file_executor_opens_file_in_vscode():
    """Test that FileExecutor._open_file actually opens a file in VS Code."""
    executor = FileExecutor()
    
    # Create a test file
    test_file = Path("temp_actual_open_test.py")
    test_file.write_text("# This file should open in VS Code\nprint('Testing actual file opening')")
    
    try:
        # Open the file using FileExecutor
        context = TaskContext(
            intent="open_file",
            command=f"open {test_file}",
            params={"file": str(test_file)}
        )
        
        result = await executor.execute(context)
        
        # Should succeed
        assert result.status == TaskStatus.SUCCESS, f"Open failed: {result.error}"
        
        # Should mention VS Code or default app
        assert "VS Code" in result.output or "default app" in result.output
        
        print(f"\n✓ {result.output}")
        print(f"  Method: {result.metadata.get('method', 'unknown')}")
        print(f"  Latency: {result.latency_ms:.1f}ms")
        
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()


@pytest.mark.asyncio
async def test_file_executor_opens_readme():
    """Test opening README.md file."""
    executor = FileExecutor()
    
    readme = Path("README.md")
    if not readme.exists():
        pytest.skip("README.md not found")
    
    context = TaskContext(
        intent="open_file",
        command=f"open {readme}",
        params={"file": str(readme)}
    )
    
    result = await executor.execute(context)
    
    assert result.status == TaskStatus.SUCCESS
    print(f"\n✓ Opened README.md: {result.output}")


@pytest.mark.asyncio
async def test_file_executor_handles_missing_file():
    """Test that opening non-existent file returns proper error."""
    executor = FileExecutor()
    
    context = TaskContext(
        intent="open_file",
        command="open nonexistent_file_xyz.txt",
        params={"file": "nonexistent_file_xyz.txt"}
    )
    
    result = await executor.execute(context)
    
    # Should fail with proper error
    assert result.status == TaskStatus.FAILED
    assert "not found" in result.error.lower()
    print(f"\n✓ Correctly handled missing file: {result.error}")


@pytest.mark.asyncio
async def test_multiple_files_open_concurrently():
    """Test opening multiple files at once."""
    executor = FileExecutor()
    
    # Create test files
    test_files = [Path(f"temp_open_{i}.txt") for i in range(3)]
    for f in test_files:
        f.write_text(f"Test content {f.name}")
    
    try:
        # Open all files concurrently
        tasks = []
        for test_file in test_files:
            context = TaskContext(
                intent="open_file",
                command=f"open {test_file}",
                params={"file": str(test_file)}
            )
            tasks.append(executor.execute(context))
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        for i, result in enumerate(results):
            assert result.status == TaskStatus.SUCCESS, f"File {i} failed: {result.error}"
            print(f"✓ Opened {test_files[i].name}: {result.output[:50]}")
        
    finally:
        # Cleanup
        for f in test_files:
            if f.exists():
                f.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
