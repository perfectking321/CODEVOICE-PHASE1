"""
Test All Voice Commands - Verify Intent Classification
Tests that all commands are classified correctly before using in demo
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from intent.classifier import IntentClassifier
from intent.entities import EntityExtractor

# Initialize
classifier = IntentClassifier()
extractor = EntityExtractor()

# Test commands
test_commands = [
    # File operations
    ("open file main.py", "open_file"),
    ("show me readme.md", "open_file"),
    ("open the config file", "open_file"),
    
    # Create operations
    ("create file test.py", "create_file"),
    ("create a new file hello.py", "create_file"),
    ("make a file config.json", "create_file"),
    ("create function parse_data", "create_function"),
    
    # Git operations
    ("commit changes with message fix bug", "git_commit"),
    ("git commit", "git_commit"),
    ("push to origin", "git_push"),
    ("git push", "git_push"),
    ("check git status", "git_status"),
    ("git status", "git_status"),
    
    # Test operations
    ("run tests", "run_tests"),
    ("run all tests", "run_tests"),
    ("execute test suite", "run_tests"),
    
    # Package operations
    ("install numpy", "install_package"),
    ("install package requests", "install_package"),
    ("pip install pytest", "install_package"),
    
    # Browser operations
    ("open google", "open_browser"),
    ("open youtube", "open_browser"),
    ("navigate to github", "open_browser"),
    
    # Build operations
    ("build project", "build_project"),
    ("compile the code", "build_project"),
    
    # Search operations
    ("search for function definition", "search_code"),
    ("find class User", "search_code"),
    
    # Terminal operations
    ("open terminal", "open_terminal"),
    ("launch powershell", "open_terminal"),
]

print("\n" + "="*80)
print("🧪 TESTING ALL VOICE COMMANDS - Intent Classification")
print("="*80 + "\n")

async def test_all_commands():
    correct = 0
    wrong = 0
    issues = []

    for text, expected_intent in test_commands:
        result = await classifier.classify(text)
        predicted_intent = result.intent
        confidence = result.confidence
        
        if predicted_intent == expected_intent:
            status = "✅"
            correct += 1
        else:
            status = "❌"
            wrong += 1
            issues.append((text, expected_intent, predicted_intent, confidence))
        
        print(f"{status} '{text}'")
        print(f"   Expected: {expected_intent}")
        print(f"   Got: {predicted_intent} (confidence: {confidence:.2f})")
        print()

    print("="*80)
    print(f"📊 RESULTS: {correct}/{len(test_commands)} correct ({correct/len(test_commands)*100:.1f}%)")
    print(f"   ✅ Correct: {correct}")
    print(f"   ❌ Wrong: {wrong}")
    print("="*80)

    if issues:
        print("\n⚠️  CLASSIFICATION ISSUES:")
        print("-"*80)
        for text, expected, predicted, conf in issues:
            print(f"❌ '{text}'")
            print(f"   Expected: {expected}")
            print(f"   Got: {predicted} (confidence: {conf:.2f})")
            print()

    print("\n" + "="*80)
    print("🔍 ENTITY EXTRACTION TEST")
    print("="*80 + "\n")

    entity_tests = [
        ("commit changes with message fix bug", "git_commit"),
        ("open file main.py", "open_file"),
        ("install package numpy", "install_package"),
        ("create file test.py", "create_file"),
        ("push to main branch", "git_push"),
    ]

    for text, intent in entity_tests:
        entities = extractor.extract(text, intent)
        print(f"📝 '{text}'")
        print(f"   Intent: {intent}")
        print(f"   Entities: {entities}")
        print()

    print("="*80)
    print("✅ Testing complete!")
    print("="*80)

asyncio.run(test_all_commands())
