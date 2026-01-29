"""
Tests for Intent Classification - BUILD 6
Test-driven development: Write tests first, then implement.
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from intent.classifier import IntentClassifier, IntentResult


class TestIntentClassifier:
    """Test intent classification functionality."""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier instance for testing."""
        return IntentClassifier()
    
    def test_classifier_initialization(self, classifier):
        """Test that classifier initializes properly."""
        assert classifier is not None
        assert classifier.model is not None
        assert classifier.intents is not None
        assert len(classifier.intents) >= 15  # Should have at least 15 intents
    
    def test_intents_loaded(self, classifier):
        """Test that intents configuration is loaded."""
        # Check core intents exist
        core_intents = [
            "open_file", "create_function", "run_tests",
            "git_commit", "git_push", "build_project",
            "search_code", "explain_code", "refactor_code",
            "debug_error", "open_terminal", "install_package",
            "open_browser", "search_content", "general_query"
        ]
        
        for intent_name in core_intents:
            assert intent_name in classifier.intents, f"Missing intent: {intent_name}"
    
    @pytest.mark.asyncio
    async def test_classify_simple_command(self, classifier):
        """Test classification of simple command."""
        result = await classifier.classify("run tests")
        
        assert isinstance(result, IntentResult)
        assert result.intent == "run_tests"
        assert result.confidence > 0.7  # High confidence for clear command
        assert result.latency_ms < 50  # Should be fast
    
    @pytest.mark.asyncio
    async def test_classify_git_commit(self, classifier):
        """Test git commit intent."""
        result = await classifier.classify("commit changes")
        
        assert result.intent == "git_commit"
        assert result.confidence > 0.6
    
    @pytest.mark.asyncio
    async def test_classify_file_open(self, classifier):
        """Test file opening intent."""
        result = await classifier.classify("open main.py")
        
        assert result.intent == "open_file"
        assert result.confidence > 0.6
    
    @pytest.mark.asyncio
    async def test_classify_browser_open(self, classifier):
        """Test browser opening intent."""
        result = await classifier.classify("open youtube")
        
        assert result.intent == "open_browser"
        assert result.confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_classify_search(self, classifier):
        """Test search intent."""
        result = await classifier.classify("search for function definition")
        
        assert result.intent in ["search_code", "search_content"]
        assert result.confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_classify_ambiguous_command(self, classifier):
        """Test that ambiguous commands still return a result."""
        result = await classifier.classify("do something")
        
        assert isinstance(result, IntentResult)
        assert result.intent is not None
        # Confidence may be lower for ambiguous commands
        assert 0.0 <= result.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_classify_latency(self, classifier):
        """Test that classification is fast enough."""
        commands = [
            "run tests",
            "open main.py",
            "commit changes",
            "search code",
            "explain function"
        ]
        
        for cmd in commands:
            result = await classifier.classify(cmd)
            assert result.latency_ms < 50, f"Too slow for '{cmd}': {result.latency_ms}ms"
    
    @pytest.mark.asyncio
    async def test_classify_multiple_words(self, classifier):
        """Test classification with longer commands."""
        result = await classifier.classify("open youtube and search for hellfire song")
        
        assert isinstance(result, IntentResult)
        # Should recognize either browser or search intent
        assert result.intent in ["open_browser", "search_content", "general_query"]
    
    def test_intent_metadata(self, classifier):
        """Test that intents have proper metadata."""
        for intent_name, intent_data in classifier.intents.items():
            assert "description" in intent_data
            assert "examples" in intent_data
            assert "category" in intent_data
            assert isinstance(intent_data["examples"], list)
            assert len(intent_data["examples"]) > 0
    
    @pytest.mark.asyncio
    async def test_classify_empty_string(self, classifier):
        """Test handling of empty input."""
        result = await classifier.classify("")
        
        assert isinstance(result, IntentResult)
        assert result.intent is not None  # Should have fallback
        assert result.confidence < 0.5  # Low confidence expected
    
    @pytest.mark.asyncio
    async def test_classify_batch(self, classifier):
        """Test batch classification for efficiency."""
        commands = [
            "run tests",
            "open file",
            "commit changes",
            "build project",
            "search code"
        ]
        
        results = await classifier.classify_batch(commands)
        
        assert len(results) == len(commands)
        assert all(isinstance(r, IntentResult) for r in results)
        assert all(r.intent is not None for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
