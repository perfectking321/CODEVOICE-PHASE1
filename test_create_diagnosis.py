"""
Test: What does the system hear when you say "create file"?
Simulates the full pipeline to diagnose the issue
"""

import sys
from pathlib import Path
import asyncio

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from intent.classifier import IntentClassifier
from intent.entities import EntityExtractor
from executor.file_executor import FileExecutor
from executor.executor_base import TaskContext

async def test_create_file_command():
    print("=" * 70)
    print("🧪 TESTING: What happens when you say 'create file hello.py'?")
    print("=" * 70)
    
    # Initialize components
    classifier = IntentClassifier()
    extractor = EntityExtractor()
    file_executor = FileExecutor()
    
    # Test different variations
    test_phrases = [
        "create file hello.py",
        "create a file test.txt",
        "make a file config.json",
        "create new file main.py",
        "please create file data.csv",
    ]
    
    for phrase in test_phrases:
        print(f"\n📝 You said: '{phrase}'")
        
        # Step 1: Intent Classification
        intent_result = await classifier.classify(phrase)
        print(f"   🎯 Intent: {intent_result.intent} (confidence: {intent_result.confidence:.2f})")
        
        # Step 2: Entity Extraction  
        entity_result = await extractor.extract(phrase, intent_result.intent)
        entities = entity_result.entities if hasattr(entity_result, 'entities') else entity_result
        print(f"   📦 Entities: {entities}")
        
        # Step 3: Command Mapping (simulating demo logic)
        if intent_result.intent == "create_file":
            file = entities.get("file", "new_file.txt")
            command = f"create {file}"
            print(f"   ⚡ Command: {command}")
            
            # Step 4: Execute
            context = TaskContext(
                intent="create_file",
                command=command,
                params={
                    "file": file,
                    "content": f"# Created by voice command: {phrase}"
                }
            )
            
            result = await file_executor.execute(context)
            print(f"   📊 Result: {result.status.name}")
            if result.status.name == "SUCCESS":
                print(f"   ✅ {result.output}")
                # Verify and cleanup
                file_path = Path(file)
                if file_path.exists():
                    print(f"   ✓ File actually exists: {file_path.absolute()}")
                    file_path.unlink()
                else:
                    print(f"   ⚠️  File not found on disk!")
            else:
                print(f"   ❌ Error: {result.error}")
        else:
            print(f"   ❌ Wrong intent! Should be 'create_file', got '{intent_result.intent}'")
    
    print("\n" + "=" * 70)
    print("✅ Testing Complete!")
    print("=" * 70)
    
    # Now test what demo receives with typical speech transcription issues
    print("\n" + "=" * 70)
    print("🎤 TESTING: Whisper transcription variations")
    print("=" * 70)
    
    transcription_variations = [
        "Create file helloworld.py",  # Your exact phrase from terminal
        "Create file helloworld.twi",  # Another variation from terminal
        "Create file hello world.py",
        "created file test.py",
        "creative file test.py",
    ]
    
    for phrase in transcription_variations:
        print(f"\n📝 Transcribed as: '{phrase}'")
        intent_result = await classifier.classify(phrase)
        print(f"   🎯 Intent: {intent_result.intent} (confidence: {intent_result.confidence:.2f})")
        
        if intent_result.intent != "create_file":
            print(f"   ❌ PROBLEM: Misclassified!")

if __name__ == "__main__":
    asyncio.run(test_create_file_command())
