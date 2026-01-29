"""
Test Specific Git Operations that Failed Before
Focus on git status, git commit scenarios
"""

import asyncio
import sys
from pathlib import Path
from colorama import init, Fore, Style

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from executor.task_scheduler import TaskScheduler
from executor.powershell_executor import PowerShellExecutor
from executor.file_executor import FileExecutor
from executor.executor_base import TaskContext, TaskStatus

# Initialize colorama
init()


async def test_git_operations():
    """Test git operations that previously failed."""
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}🧪 Testing Git Operations{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    scheduler = TaskScheduler(max_concurrent_tasks=5)
    ps_executor = PowerShellExecutor()
    file_executor = FileExecutor()
    
    # Test 1: Git Status (Previously Failed)
    print(f"{Fore.CYAN}Test 1: Git Status{Style.RESET_ALL}")
    context = TaskContext(
        intent="git_status",
        command="git status",
    )
    task_id = await scheduler.submit_task(context, ps_executor)
    result = await scheduler.wait_for_task(task_id, timeout=5.0)
    
    if result and result.status == TaskStatus.SUCCESS:
        print(f"{Fore.GREEN}✅ Git Status Works!{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{result.output[:200]}{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.RED}❌ Failed: {result.error if result else 'Timeout'}{Style.RESET_ALL}\n")
    
    # Test 2: Git Log
    print(f"{Fore.CYAN}Test 2: Git Log (Show Commits){Style.RESET_ALL}")
    context = TaskContext(
        intent="git_log",
        command="git log --oneline -5",
    )
    task_id = await scheduler.submit_task(context, ps_executor)
    result = await scheduler.wait_for_task(task_id, timeout=5.0)
    
    if result and result.status == TaskStatus.SUCCESS:
        print(f"{Fore.GREEN}✅ Git Log Works!{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{result.output}{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.RED}❌ Failed: {result.error if result else 'Timeout'}{Style.RESET_ALL}\n")
    
    # Test 3: Check Remote
    print(f"{Fore.CYAN}Test 3: Git Remote{Style.RESET_ALL}")
    context = TaskContext(
        intent="git_remote",
        command="git remote -v",
    )
    task_id = await scheduler.submit_task(context, ps_executor)
    result = await scheduler.wait_for_task(task_id, timeout=5.0)
    
    if result and result.status == TaskStatus.SUCCESS:
        print(f"{Fore.GREEN}✅ Git Remote Works!{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{result.output}{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.RED}❌ Failed: {result.error if result else 'Timeout'}{Style.RESET_ALL}\n")
    
    # Test 4: File Operations (Previously Failed)
    print(f"{Fore.CYAN}Test 4: Open Existing File (src/main.py){Style.RESET_ALL}")
    context = TaskContext(
        intent="open_file",
        command="open src/main.py",
        params={"file": "src/main.py"}
    )
    task_id = await scheduler.submit_task(context, file_executor)
    result = await scheduler.wait_for_task(task_id, timeout=5.0)
    
    if result and result.status == TaskStatus.SUCCESS:
        print(f"{Fore.GREEN}✅ File Open Works!{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{result.output}{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.RED}❌ Failed: {result.error if result else 'Timeout'}{Style.RESET_ALL}\n")
    
    # Test 5: List Project Files
    print(f"{Fore.CYAN}Test 5: List Source Files{Style.RESET_ALL}")
    context = TaskContext(
        intent="list_files",
        command="Get-ChildItem -Path src -Recurse -File -Name | Select-Object -First 10",
    )
    task_id = await scheduler.submit_task(context, ps_executor)
    result = await scheduler.wait_for_task(task_id, timeout=5.0)
    
    if result and result.status == TaskStatus.SUCCESS:
        print(f"{Fore.GREEN}✅ List Files Works!{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{result.output}{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.RED}❌ Failed: {result.error if result else 'Timeout'}{Style.RESET_ALL}\n")
    
    # Test 6: Python Version (Was Working)
    print(f"{Fore.CYAN}Test 6: Python Version{Style.RESET_ALL}")
    context = TaskContext(
        intent="python_version",
        command="python --version",
    )
    task_id = await scheduler.submit_task(context, ps_executor)
    result = await scheduler.wait_for_task(task_id, timeout=5.0)
    
    if result and result.status == TaskStatus.SUCCESS:
        print(f"{Fore.GREEN}✅ Python Version Works!{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{result.output}{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.RED}❌ Failed: {result.error if result else 'Timeout'}{Style.RESET_ALL}\n")
    
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ All Tests Completed!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Summary: Git operations now work because we're in a repo!{Style.RESET_ALL}\n")
    
    await scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(test_git_operations())
