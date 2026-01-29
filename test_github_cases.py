"""
Test Failed Cases from Week 3 Demo
Now that we're in a git repository, test the commands that previously failed.
"""

import asyncio
import sys
from pathlib import Path
from colorama import init, Fore, Style

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from intent.classifier import IntentClassifier
from intent.entities import EntityExtractor
from executor.task_scheduler import TaskScheduler
from executor.powershell_executor import PowerShellExecutor
from executor.file_executor import FileExecutor
from executor.executor_base import TaskContext, TaskStatus

# Initialize colorama
init()


async def test_failed_cases():
    """Test the commands that failed in original demo."""
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}🧪 Testing Previously Failed Cases{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    # Initialize components
    print(f"{Fore.YELLOW}Initializing...{Style.RESET_ALL}")
    classifier = IntentClassifier()
    entities = EntityExtractor()
    scheduler = TaskScheduler(max_concurrent_tasks=5)
    ps_executor = PowerShellExecutor()
    file_executor = FileExecutor()
    
    test_cases = [
        {
            "command": "Check git status",
            "expected_intent": "git_status",
            "executor": ps_executor,
            "description": "Should work now in git repo"
        },
        {
            "command": "git status",
            "expected_intent": "git_status",
            "executor": ps_executor,
            "description": "Direct git status command"
        },
        {
            "command": "Show me git log",
            "expected_intent": "git_status",
            "executor": ps_executor,
            "description": "Git log to see commits"
        },
        {
            "command": "Open file src/main.py",
            "expected_intent": "open_file",
            "executor": file_executor,
            "description": "File that exists in project"
        },
        {
            "command": "List files in src directory",
            "expected_intent": "search_code",
            "executor": ps_executor,
            "description": "List project files"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{Fore.CYAN}{'─'*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Test {i}/{len(test_cases)}: {test_case['description']}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Command: \"{test_case['command']}\"{Style.RESET_ALL}")
        
        # Classify intent
        intent_result = await classifier.classify(test_case['command'])
        print(f"{Fore.YELLOW}  Intent:{Style.RESET_ALL} {intent_result.intent} "
              f"(confidence: {intent_result.confidence:.2f})")
        
        # Extract entities
        entity_result = await entities.extract(
            test_case['command'],
            intent_result.intent
        )
        
        if entity_result.entities:
            print(f"{Fore.YELLOW}  Entities:{Style.RESET_ALL}")
            for key, value in entity_result.entities.items():
                print(f"    • {key}: {value}")
        
        # Map to command
        command = map_to_command(intent_result.intent, entity_result.entities)
        if not command:
            print(f"{Fore.RED}  ❌ Could not map to command{Style.RESET_ALL}")
            continue
        
        print(f"{Fore.YELLOW}  Executing:{Style.RESET_ALL} {command}")
        
        # Create context and execute
        context = TaskContext(
            intent=intent_result.intent,
            command=command,
            params=entity_result.entities,
            timeout_seconds=5  # Shorter timeout for tests
        )
        
        task_id = await scheduler.submit_task(context, test_case['executor'])
        result = await scheduler.wait_for_task(task_id, timeout=6.0)
        
        # Show result
        if result:
            if result.status == TaskStatus.SUCCESS:
                print(f"{Fore.GREEN}  ✅ SUCCESS ({result.latency_ms:.0f}ms){Style.RESET_ALL}")
                if result.output:
                    # Show first 150 chars of output
                    output = result.output.strip()[:150]
                    if len(result.output) > 150:
                        output += "..."
                    print(f"{Fore.WHITE}  Output: {output}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}  ❌ FAILED: {result.error[:100]}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}  ⏱️  TIMEOUT{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ Test completed!{Style.RESET_ALL}\n")
    
    await scheduler.shutdown()


def map_to_command(intent: str, entities: dict) -> str:
    """Map intent to executable command."""
    if intent == "git_status":
        return "git status"
    elif intent == "git_commit":
        message = entities.get("message", "Update")
        return f'git add -A ; git commit -m "{message}"'
    elif intent == "git_push":
        branch = entities.get("branch", "main")
        return f"git push origin {branch}"
    elif intent == "open_file":
        file = entities.get("file", "")
        return f"open {file}"
    elif intent == "search_code":
        return "Get-ChildItem -Path . -Recurse -File | Select-Object Name, Directory | Format-Table"
    else:
        return None


if __name__ == "__main__":
    asyncio.run(test_failed_cases())
