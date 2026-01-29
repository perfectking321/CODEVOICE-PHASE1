"""
Quick test: Can we create files?
Tests file creation to diagnose permission issues
"""

import sys
from pathlib import Path
import asyncio

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from executor.file_executor import FileExecutor
from executor.executor_base import TaskContext

async def test_file_creation():
    print("=" * 60)
    print("Testing File Creation - Permission Check")
    print("=" * 60)
    
    executor = FileExecutor()
    
    # Test 1: Create file in current directory
    print("\n1️⃣  Test: Create file in current directory")
    context = TaskContext(
        intent="create_file",
        command="create test_permission.txt",
        params={
            "file": "test_permission.txt",
            "content": "This is a test file to check permissions."
        }
    )
    
    try:
        result = await executor.execute(context)
        print(f"   Status: {result.status}")
        print(f"   Output: {result.output}")
        
        # Verify file exists
        test_file = Path("test_permission.txt")
        if test_file.exists():
            print(f"   ✅ File created successfully!")
            print(f"   Content: {test_file.read_text()}")
            test_file.unlink()  # Cleanup
        else:
            print(f"   ❌ File NOT created!")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Test 2: Create file with subdirectory
    print("\n2️⃣  Test: Create file in subdirectory")
    context = TaskContext(
        intent="create_file",
        command="create temp/nested/test.py",
        params={
            "file": "temp/nested/test.py",
            "content": "# Test file\nprint('Hello')"
        }
    )
    
    try:
        result = await executor.execute(context)
        print(f"   Status: {result.status}")
        print(f"   Output: {result.output}")
        
        # Verify file exists
        test_file = Path("temp/nested/test.py")
        if test_file.exists():
            print(f"   ✅ File created successfully in subdirectory!")
            # Cleanup
            import shutil
            shutil.rmtree("temp")
        else:
            print(f"   ❌ File NOT created!")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Test 3: Try to create in restricted location (should fail)
    print("\n3️⃣  Test: Try to create in restricted location")
    context = TaskContext(
        intent="create_file",
        command="create C:/Windows/System32/test.txt",
        params={
            "file": "C:/Windows/System32/test.txt",
            "content": "This should fail"
        }
    )
    
    try:
        result = await executor.execute(context)
        print(f"   Status: {result.status}")
        if result.status.name == "FAILED":
            print(f"   ✅ Correctly failed (as expected)")
            print(f"   Error: {result.error}")
        else:
            print(f"   ⚠️  Unexpectedly succeeded")
    except Exception as e:
        print(f"   ✅ Correctly failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_file_creation())
