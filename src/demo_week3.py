"""
Week 3 Demo: Complete Voice-to-Execution Pipeline
Demonstrates full CodeVoice functionality from Weeks 1-3

Pipeline:
1. Microphone → Audio capture (Week 1)
2. VAD → Speech detection (Week 1)
3. Whisper → Transcription (Week 1)
4. Intent Classifier → Understanding (Week 2)
5. Entity Extractor → Parameter extraction (Week 2)
6. Task Scheduler + Executors → Execution (Week 3)
"""

import asyncio
import sys
from pathlib import Path
from colorama import init, Fore, Style

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from audio.microphone import MicrophoneStream
from audio.vad import VADDetector
from asr.whisper_asr import WhisperASR
from intent.classifier import IntentClassifier
from intent.entities import EntityExtractor
from executor.task_scheduler import TaskScheduler
from executor.powershell_executor import PowerShellExecutor
from executor.file_executor import FileExecutor
from executor.executor_base import TaskContext, TaskStatus

# Initialize colorama
init()


class CodeVoiceDemo:
    """Complete voice-controlled development assistant demo."""
    
    def __init__(self):
        """Initialize all pipeline components."""
        print(f"{Fore.CYAN}🚀 Initializing CodeVoice...{Style.RESET_ALL}")
        
        # Week 1: Audio pipeline
        print(f"{Fore.YELLOW}   Loading audio components...{Style.RESET_ALL}")
        self.microphone = MicrophoneStream()
        self.vad = VADDetector(threshold=0.2)
        self.asr = WhisperASR(model_size="base")
        
        # Week 2: Understanding
        print(f"{Fore.YELLOW}   Loading intent classifier...{Style.RESET_ALL}")
        self.classifier = IntentClassifier()
        self.entities = EntityExtractor()
        
        # Week 3: Execution
        print(f"{Fore.YELLOW}   Loading executors...{Style.RESET_ALL}")
        self.scheduler = TaskScheduler(max_concurrent_tasks=5)
        self.ps_executor = PowerShellExecutor()
        self.file_executor = FileExecutor()
        
        print(f"{Fore.GREEN}✅ CodeVoice ready!{Style.RESET_ALL}\n")
    
    async def process_command(self, transcription: str):
        """
        Process a voice command through full pipeline.
        
        Args:
            transcription: Transcribed text from speech
        """
        print(f"\n{Fore.CYAN}📝 You said:{Style.RESET_ALL} \"{transcription}\"")
        
        # Step 1: Classify intent
        intent_result = await self.classifier.classify(transcription)
        print(f"{Fore.YELLOW}🎯 Intent:{Style.RESET_ALL} {intent_result.intent} "
              f"(confidence: {intent_result.confidence:.2f}, "
              f"{intent_result.latency_ms:.1f}ms)")
        
        # Step 2: Extract entities
        entity_result = await self.entities.extract(
            transcription,
            intent_result.intent
        )
        
        if entity_result.entities:
            print(f"{Fore.YELLOW}📦 Entities:{Style.RESET_ALL}")
            for key, value in entity_result.entities.items():
                print(f"   • {key}: {value}")
        
        # Step 3: Map intent to command
        command = self._map_intent_to_command(
            intent_result.intent,
            entity_result.entities
        )
        
        if not command:
            print(f"{Fore.RED}❌ Unknown intent: {intent_result.intent}{Style.RESET_ALL}")
            return
        
        print(f"{Fore.YELLOW}⚡ Command:{Style.RESET_ALL} {command}")
        
        # Step 4: Select executor
        executor = self._select_executor(intent_result.intent)
        
        # Step 5: Create task context
        context = TaskContext(
            intent=intent_result.intent,
            command=command,
            params=entity_result.entities
        )
        
        # Step 6: Submit task
        task_id = await self.scheduler.submit_task(context, executor)
        print(f"{Fore.GREEN}✓ Task {task_id} submitted{Style.RESET_ALL}")
        
        # Step 7: Wait for completion
        result = await self.scheduler.wait_for_task(task_id, timeout=10.0)
        
        if result:
            if result.status == TaskStatus.SUCCESS:
                print(f"{Fore.GREEN}✅ Success ({result.latency_ms:.0f}ms):{Style.RESET_ALL}")
                if result.output:
                    # Limit output to 200 chars
                    output = result.output[:200]
                    if len(result.output) > 200:
                        output += "..."
                    print(f"{Fore.WHITE}{output}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ Failed: {result.error}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}⏱️  Task timed out{Style.RESET_ALL}")
    
    def _map_intent_to_command(self, intent: str, entities: dict) -> str:
        """
        Map intent and entities to executable command.
        
        Args:
            intent: Classified intent
            entities: Extracted entities
            
        Returns:
            Command string or None
        """
        # Git commands
        if intent == "git_commit":
            message = entities.get("message", "Update")
            return f'git add -A ; git commit -m "{message}"'
        
        elif intent == "git_push":
            branch = entities.get("branch", "main")
            return f"git push origin {branch}"
        
        elif intent == "git_status":
            return "git status"
        
        # Test commands
        elif intent == "run_tests":
            path = entities.get("path", ".")
            return f"pytest {path} -v"
        
        # File commands
        elif intent == "open_file":
            file = entities.get("file", "")
            return f"open {file}"
        
        elif intent == "create_function":
            name = entities.get("function_name", "new_function")
            return f"create {name}.py"
        
        # Build commands
        elif intent == "build_project":
            return "python -m build"
        
        # Package commands
        elif intent == "install_package":
            package = entities.get("package", "")
            return f"pip install {package}"
        
        # Terminal commands
        elif intent == "open_terminal":
            return "Write-Output 'Terminal opened'"
        
        # Browser commands
        elif intent == "open_browser":
            url = entities.get("url", "https://google.com")
            return f"Start-Process {url}"
        
        # Search commands
        elif intent == "search_code":
            query = entities.get("query", "")
            return f'Get-ChildItem -Recurse | Select-String "{query}"'
        
        # Default
        return None
    
    def _select_executor(self, intent: str):
        """
        Select appropriate executor for intent.
        
        Args:
            intent: Intent type
            
        Returns:
            Executor instance
        """
        # File operations
        if intent in ["open_file", "create_function"]:
            return self.file_executor
        
        # Everything else uses PowerShell
        return self.ps_executor
    
    async def run_demo(self):
        """Run interactive voice demo."""
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}🎤 CodeVoice Interactive Demo{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Try saying:{Style.RESET_ALL}")
        print(f"  • \"Commit changes with message fix bug\"")
        print(f"  • \"Run all tests\"")
        print(f"  • \"Check git status\"")
        print(f"  • \"Open file main.py\"")
        print(f"  • \"Install package requests\"")
        print(f"\n{Fore.CYAN}Press Ctrl+C to stop{Style.RESET_ALL}\n")
        
        try:
            # Start listening
            async for audio_chunk in self.microphone.stream_audio():
                # Detect speech
                is_speech = self.vad.is_speech(audio_chunk)
                
                if not is_speech:
                    continue
                
                print(f"{Fore.YELLOW}🎤 Speech detected, listening...{Style.RESET_ALL}")
                
                # Collect speech audio
                speech_audio = [audio_chunk]
                silence_count = 0
                
                async for chunk in self.microphone.stream_audio():
                    is_speech_chunk = self.vad.is_speech(chunk)
                    
                    if is_speech_chunk:
                        speech_audio.append(chunk)
                        silence_count = 0
                    else:
                        silence_count += 1
                        if silence_count > 10:  # ~320ms silence
                            break
                
                # Transcribe
                print(f"{Fore.YELLOW}🔄 Transcribing...{Style.RESET_ALL}")
                transcription = await self.asr.transcribe(b''.join(speech_audio))
                
                if transcription.text.strip():
                    # Process command
                    await self.process_command(transcription.text)
                
                print(f"\n{Fore.CYAN}{'─'*60}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Ready for next command...{Style.RESET_ALL}\n")
        
        except KeyboardInterrupt:
            print(f"\n\n{Fore.CYAN}Shutting down...{Style.RESET_ALL}")
            await self.scheduler.shutdown()
            print(f"{Fore.GREEN}✅ Goodbye!{Style.RESET_ALL}")
    
    async def run_test_commands(self):
        """Run test commands without voice input."""
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}🧪 CodeVoice Test Mode{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
        test_commands = [
            "Check git status",
            "Run tests",
            "Open file main.py",
            "Commit changes with message test commit",
        ]
        
        for cmd in test_commands:
            await self.process_command(cmd)
            print(f"\n{Fore.CYAN}{'─'*60}{Style.RESET_ALL}\n")
            await asyncio.sleep(0.5)
        
        await self.scheduler.shutdown()
        print(f"\n{Fore.GREEN}✅ Test completed!{Style.RESET_ALL}")


async def main():
    """Main entry point."""
    demo = CodeVoiceDemo()
    
    # Check if running in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        await demo.run_test_commands()
    else:
        await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())
